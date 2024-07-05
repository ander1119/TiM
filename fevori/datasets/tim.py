import json
import os

import pandas as pd
from torch.utils.data import Dataset
import decord
from decord import cpu
import numpy as np
import numpy as np

def load_file(file_name):
    annos = None
    if os.path.splitext(file_name)[-1] == '.csv':
        return pd.read_csv(file_name)
    with open(file_name, 'r') as fp:
        if os.path.splitext(file_name)[1]== '.txt':
            annos = fp.readlines()
            annos = [line.rstrip() for line in annos]
        if os.path.splitext(file_name)[1] == '.json':
            annos = json.load(fp)

    return annos


def save_file(obj, filename):
    """
    save obj to filename
    :param obj:
    :param filename:
    :return:
    """
    filepath = os.path.dirname(filename)
    if filepath != '' and not os.path.exists(filepath):
        os.makedirs(filepath)
    else:
        with open(filename, 'w') as fp:
            json.dump(obj, fp, indent=4)


class TiMDataset(Dataset):
    def __init__(self, split, data_path="", tokenize=None, max_samples=None, version='multiplechoice', fps=10,
                 max_num_frames=None, start_sample=0, hard_attn_file_path=None, **kwargs):

        assert version in ['multiplechoice']
        
        self.split = split
        self.data_path = data_path
        self.tokenize = tokenize
        self.version = version
        self.fps = fps
        self.input_type = 'video'
        self.max_num_frames = max_num_frames
        self.anno_path = kwargs['anno_path']

        sample_list_path = self.anno_path
        self.sample_list = load_file(sample_list_path)

        if max_samples is not None:
            # self.sample_list = self.sample_list.sample(n=max_samples)
            self.sample_list = self.sample_list[start_sample:start_sample+max_samples]

    def get_sample_path(self, index):
        cur_sample = self.sample_list[index]
        video_name = str(cur_sample['video'])
        video_path = os.path.join(self.data_path, 'videos', video_name + '.mp4')
        return video_path

    def load_annotation(self, video_name):
        annotation_path = os.path.join(self.data_path, 'subtitles', video_name + '.json')
        annotation = json.load(open(annotation_path, 'r'))
        return annotation

    def get_video_and_annotation(self, video_name, hard_attn_idx=None):
        annotation = self.load_annotation(video_name)
        video_path = os.path.join(self.data_path, 'videos', video_name + '.mp4')
        # If fixed width and height are required, VideoReader takes width and height as arguments.
        video_reader = decord.VideoReader(video_path, num_threads=1, ctx=cpu(0))
        decord.bridge.set_bridge('torch')

        vlen = len(video_reader)
        original_fps = video_reader.get_avg_fps()
        num_frames = int(vlen * self.fps / original_fps)

        assert num_frames == len(annotation)

        if self.max_num_frames is not None:
            num_frames = min(self.max_num_frames, num_frames)
        else:
            num_frames = num_frames // 3
        
        intervals = np.linspace(0, vlen, num=num_frames+1).astype(np.int64)
        ranges = []
        for idx, interv in enumerate(intervals[:-1]):
            ranges.append((interv, intervals[idx + 1]))
        # frame_idxs = np.linspace(0, vlen, num_frames, endpoint=False).astype(np.int64)
        frame_idxs = [(x[0] + x[1]) // 2 for x in ranges]
        if len(frame_idxs) < num_frames:
            rest = [frame_idxs[-1] for i in range(num_frames - len(frame_idxs))]
            frame_idxs = frame_idxs + rest 

        if hard_attn_idx is not None:
            frame_idxs = [frame_idxs[idx] for idx in hard_attn_idx]

        video = video_reader.get_batch(frame_idxs).byte() # (num_frames, H, W, C)
        video = video.permute(0, 3, 1, 2) # (num_frames, C, H, W)

        annotation = [list(annotation.values())[i] for i in frame_idxs]

        return video, annotation

    def __getitem__(self, idx):
        cur_sample = self.sample_list[idx]

        sample_id = str(cur_sample['qid'])
        question = str(cur_sample['question'])
        hard_attn_idx = cur_sample.get('hard_attn_idx', None)
        if self.tokenize:
            question = self.tokenize(question)

        video_name = str(cur_sample['video'])
        video, annotation = self.get_video_and_annotation(video_name, hard_attn_idx)

        answer_idx = int(cur_sample['answer'])
        possible_answers = [str(cur_sample[f'a{i}']) for i in range(2)]
        answer = possible_answers[answer_idx]

        query_type = sample_id.split('_')[0]
        trope = str(cur_sample['trope'])
        out_dict = {
            "sample_id": sample_id, 
            "answer": answer, 
            "image": video, 
            "query": question, 
            'pil_img': -1,
            "query_type": query_type, 
            'index': idx, 
            'possible_answers': possible_answers,
            'extra_context': possible_answers,
            'trope': trope,
            'annotation': annotation
        }

        return out_dict

    def __len__(self):
        return len(self.sample_list)

    # def get_index_from_sample_id(self, sample_id):
    #     return self.sample_id_to_index[sample_id]

    def get_img_path(self, index):
        cur_sample = self.sample_list[index]
        video_name = str(cur_sample['video'])
        video_path = os.path.join(self.data_path, 'videos', video_name + '.mp4')
        return video_path

    def accuracy(self, prediction, ground_truth, possible_answers, query_type):
        """
        Args:
            prediction (list): List of predicted answers.
            ground_truth (list): List of ground truth answers.
            possible_answers (list): List of possible answers.
            query_type (list): List of query types
        Returns:
            score (float): Score of the prediction.
        """
        from sklearn.metrics import precision_recall_fscore_support
        assert len(prediction) == len(ground_truth)

        binary_prediction = []
        binary_ground_truth = []
        for p, g in zip(prediction, ground_truth):
            if p not in ['yes', 'no']:
                print(f'unexpected prediction: {p}')
                continue
            binary_prediction.append(1 if p == 'yes' else 0)
            binary_ground_truth.append(1 if g == 'yes' else 0)    

        # prediction = [1 if p == 'yes' else 0 for p in prediction]
        # ground_truth = [1 if g == 'yes' else 0 for g in ground_truth]

        accuracy = sum(1 for p, t in zip(binary_prediction, binary_ground_truth) if p == t) / len(ground_truth)

        f1 = precision_recall_fscore_support(binary_ground_truth, binary_prediction, average='binary')
        weighted_f1 = precision_recall_fscore_support(binary_ground_truth, binary_prediction, average='weighted')
        score = {
            'precision': f1[0],
            'recall': f1[1],
            'f1': f1[2],
            'weighted_precision': weighted_f1[0],
            'weighted_recall': weighted_f1[1],
            'weighted_f1': weighted_f1[2],
            'accuracy': accuracy
        }

        return score