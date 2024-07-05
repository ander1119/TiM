from __future__ import annotations

import torch
from typing import Union, Iterator

from configs import config
from image_patch import ImagePatch
from vision_processes import forward

import os
from utils import show_single_image

class VideoSegment:
    """A Python class containing a set of frames represented as ImagePatch objects, as well as relevant information.
    Attributes
    ----------
    video : torch.Tensor
        A tensor of the original video.
    start : int
        An int describing the starting frame in this video segment with respect to the original video.
    end : int
        An int describing the ending frame in this video segment with respect to the original video.
    num_frames->int
        An int containing the number of frames in the video segment.

    Methods
    -------
    frame_iterator->Iterator[ImagePatch]
    trim(start, end)->VideoSegment
        Returns a new VideoSegment containing a trimmed version of the original video at the [start, end] segment.
    """

    def __init__(self, video: torch.Tensor, annotation: list, start: int = None, end: int = None, parent_start=0, queues=None):
        """Initializes a VideoSegment object by trimming the video at the given [start, end] times and stores the
        start and end times as attributes. If no times are provided, the video is left unmodified, and the times are
        set to the beginning and end of the video.

        Parameters
        -------
        video : torch.Tensor
            A tensor of the original video.
        annotation : list of dict
            An list with length equal to video.shape[0]. Each entry is a dict with the following keys: "bboxes" and "subtitles"
        start : int
            An int describing the starting frame in this video segment with respect to the original video.
        end : int
            An int describing the ending frame in this video segment with respect to the original video.
        """

        if start is None and end is None:
            self.trimmed_video = video
            self.annotation = annotation
            self.start = 0
            self.end = video.shape[0]  # duration
        else:
            self.trimmed_video = video[start:end]
            self.annotation = annotation[start:end]
            if start is None:
                start = 0
            if end is None:
                end = video.shape[0]
            self.start = start + parent_start
            self.end = end + parent_start

        self.num_frames = self.trimmed_video.shape[0]

        self.cache = {}
        self.queues = (None, None) if queues is None else queues

        if self.trimmed_video.shape[0] == 0:
            raise Exception("VideoSegment has duration=0")
        
        self.role_face_db = {}

        assert video.shape[0] == len(annotation)

    def forward(self, model_name, *args, **kwargs):
        return forward(model_name, *args, queues=self.queues, **kwargs)

    def frame_from_index(self, index) -> ImagePatch:
        """Returns the frame at position 'index', as an ImagePatch object."""
        if index < self.num_frames:
            image = self.trimmed_video[index]
            annotation = self.annotation[index]
        else:
            image = self.trimmed_video[-1]
            annotation = self.annotation[-1]
        return ImagePatch(image, annotation, queues=self.queues)

    def trim(self, start: Union[int, None] = None, end: Union[int, None] = None) -> VideoSegment:
        """Returns a new VideoSegment containing a trimmed version of the original video at the [start, end]
        segment.

        Parameters
        ----------
        start : Union[int, None]
            An int describing the starting frame in this video segment with respect to the original video.
        end : Union[int, None]
            An int describing the ending frame in this video segment with respect to the original video.

        Returns
        -------
        VideoSegment
            a new VideoSegment containing a trimmed version of the original video at the [start, end]
        """
        if start is not None:
            start = max(start, 0)
        if end is not None:
            end = min(end, self.num_frames)

        return VideoSegment(self.trimmed_video, self.annotation, start, end, self.start, queues=self.queues)

    def face_identify(self, image: ImagePatch) -> str:
        """Identifies the person in the given image and return an unique identifier."""
        # return self.forward('deepface', image, self.role_face_db)
        # idx = 0
        # while os.path.exists(f'./tmp2/{idx}.jpg'):
        #     idx += 1
        # show_single_image(image.cropped_image, save_path=f'./tmp2/{idx}.jpg')
        # for pid, faces in self.role_face_db.items():
        #     for i, face in enumerate(faces):
        #         img_path = f'./tmp/{pid}/{i}.jpg'
        #         if not os.path.exists(img_path):
        #             show_single_image(face.cropped_image, save_path=img_path)
        # state_role_face_db = {
        #     pid: len(faces) for pid, faces in self.role_face_db.items()
        # }
        # print(state_role_face_db)
        role_id, self.role_face_db = self.forward('deepface', image, self.role_face_db)
        return role_id

    def select_answer(self, info: dict, question: str, options=None) -> str:
        
        import json

        def info_summarize(info):
            # prompt = f'You are given an json string that contains caption or query from frames in a video, please remove redundant information from the json string (for example, similar description in adjacent frame). And return the final response in json format. Please make the summarization result at most 3000 tokens. Here is json string you are asked to task:\n{info}\n'
            prompt = f'{info}'
            return self.forward('gpt3_summarize', prompt)
            
        with open(config.select_answer_prompt, 'r') as f:
            prompt = f.read()
        # info_formatting = '\n'.join([f"- {k}: {format_dict(v)}" for k, v in info.items()])
        character_limit = 20000 - len(prompt)
        chunk_limit = 10000

        # info = json.dumps(info)
        # print(f'before summarization got info length: {len(json.dumps(info))}')

        round = 0
        summarization = ""
        chunk_message = {}
        for key, value in info.items():
            chunk_message[key] = value
            if len(json.dumps(chunk_message)) > chunk_limit:
                chunk_summarization = info_summarize(json.dumps(chunk_message))
                summarization += '\n' + chunk_summarization

                chunk_message_str = json.dumps(chunk_message, indent=4)
                # print(f'============== round {round} ==============')
                # print(f'\n{chunk_message_str}\n')
                # print(f'\n{chunk_summarization}\n')

                chunk_message = {}
        if len(chunk_message) != 0:
            chunk_summarization = info_summarize(json.dumps(chunk_message))
            summarization += '\n' + chunk_summarization

            # chunk_message_str = json.dumps(chunk_message, indent=4)
            # print(f'============== round {round} ==============')
            # print(f'\n{chunk_message_str}\n')
            # print(f'\n{chunk_summarization}\n')

        info = summarization
        round += 1

        while len(info) > character_limit:
            summarization = ""
            for start_idx in range(0, len(info), chunk_limit):
                chunk_message = info[start_idx:start_idx + chunk_limit]
                chunk_summarization = info_summarize(chunk_message)
                summarization += '\n' + chunk_summarization

                # print(f'============== round {round} ==============')
                # print(f'\n{chunk_message}\n')
                # print(f'\n{chunk_summarization}\n')

            info = summarization
            round += 1

        # info_legnth = len(json.dumps(info))
        # print(f'after summarization got info length: {info_legnth}')

        # info_formatting = json.dumps(info)
        prompt = prompt.format(info=info, question=question, options=options)
        result = self.forward('gpt3_general', prompt, to_json=True)
        
        try:
            result = eval(result)
            answer = result.get('answer', 'None')
            reason = result.get('reason', f'gpt3_general return {result}') 
        except:
            answer = 'None'
            reason = f'gpt3_general return {result}'

        return answer, reason
    
    def frame_iterator(self) -> Iterator[ImagePatch]:
        """Returns an iterator over the frames in the video segment."""
        for i in range(self.num_frames):
            yield ImagePatch(self.trimmed_video[i], self.annotation[i], queues=self.queues)

    def __repr__(self):
        return "VideoSegment({}, {})".format(self.start, self.end)
    
    def __len__(self):
        return self.num_frames
