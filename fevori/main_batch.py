import json
import os
import pathlib
from functools import partial
import warnings
import traceback

import pandas as pd
import torch.multiprocessing as mp
from joblib import Memory
from omegaconf import OmegaConf
from rich.console import Console
from torch.utils.data import DataLoader
from tqdm import tqdm

from configs import config
from utils import format_dict, seed_everything
import datasets

# See https://github.com/pytorch/pytorch/issues/11201, https://github.com/pytorch/pytorch/issues/973
# Not for dataloader, but for multiprocessing batches
mp.set_sharing_strategy('file_system')
queue_results = None

cache = Memory('cache/' if config.use_cache else None, verbose=0)
runs_dict = {}
seed_everything()
console = Console(highlight=False)


def my_collate(batch):
    # Avoid stacking images (different size). Return everything as a list
    to_return = {k: [d[k] for d in batch] for k in batch[0].keys()}
    return to_return


def run_program(parameters, queues_in_, input_type_, retrying=True):
    from image_patch import ImagePatch, llm_query, best_image_match, distance, bool_to_yesno
    from video_segment import VideoSegment

    global queue_results

    code, sample_id, image, annotation, possible_answers, query = parameters

    code_header = f'def execute_command_{sample_id}(' \
                  f'{input_type_}, annotation, possible_answers, query, ' \
                  f'ImagePatch, VideoSegment, ' \
                  'llm_query, bool_to_yesno, distance, best_image_match):\n' \
                  f'    # Answer is:'

    code = code.replace('```', '').replace('python', '')
    code = code_header + code.strip()

    answer = None
    reason = None
    info = None
    compilation_error = ''
    runtime_error = ''

    try:
        exec(compile(code, 'Codex', 'exec'), globals())
    except Exception as e:
        compilation_error = str(e)
        print(f'Sample {sample_id} failed at compilation time with error: {e}')

    queues = [queues_in_, queue_results]

    image_patch_partial = partial(ImagePatch, queues=queues)
    video_segment_partial = partial(VideoSegment, queues=queues)
    llm_query_partial = partial(llm_query, queues=queues)

    try:
        answer, reason, info = globals()[f'execute_command_{sample_id}'](
            # Inputs to the function
            image, annotation, possible_answers, query,
            # Classes to be used
            image_patch_partial, video_segment_partial,
            # Functions to be used
            llm_query_partial, bool_to_yesno, distance, best_image_match)
    except Exception as e:
        # print full traceback
        traceback.print_exc()
        runtime_error = str(e)

    # The function run_{sample_id} is defined globally (exec doesn't work locally). A cleaner alternative would be to
    # save it in a global dict (replace globals() for dict_name in exec), but then it doesn't detect the imported
    # libraries for some reason. Because defining it globally is not ideal, we just delete it after running it.
    if f'execute_command_{sample_id}' in globals():
        del globals()[f'execute_command_{sample_id}']  # If it failed to compile the code, it won't be defined
    return {
        'answer': answer,
        'compilation_error': compilation_error,
        'runtime_error': runtime_error,
        'info': info,
        'code': code,
        'reason': reason,
    }


def worker_init(queue_results_):
    global queue_results
    index_queue = mp.current_process()._identity[0] % len(queue_results_)
    queue_results = queue_results_[index_queue]


def main():
    mp.set_start_method('spawn')

    from vision_processes import queues_in, finish_all_consumers, forward, manager
    from datasets import get_dataset

    batch_size = config.dataset.batch_size
    num_processes = min(batch_size, 50)

    if config.multiprocessing:
        queue_results_main = manager.Queue()
        queues_results = [manager.Queue() for _ in range(batch_size)]
    else:
        queue_results_main = None
        queues_results = [None for _ in range(batch_size)]

    model_name_codex = 'codellama' if config.codex.model == 'codellama' else 'codex'
    codex = partial(forward, model_name=model_name_codex, queues=[queues_in, queue_results_main])

    if config.clear_cache:
        cache.clear()

    if config.wandb:
        import wandb
        wandb.init(project="viper", config=OmegaConf.to_container(config))
        # log the prompt file
        wandb.save(config.codex.prompt)

    dataset = get_dataset(config.dataset)

    codes_all = None
    if config.use_cached_codex:
        results = pd.read_csv(config.cached_codex_path, sep='|')
        codes_all = {trope: code for trope, code in zip(results['trope'], results['code'])}
    # python -c "from joblib import Memory; cache = Memory('cache/', verbose=0); cache.clear()"
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True,
                            collate_fn=my_collate)
    input_type = dataset.input_type

    all_answers = []
    all_infos = []
    all_compilation_errors = []
    all_runtime_errors = []
    all_codes = []
    all_reasons = []
    all_tropes = []

    all_groundtruths = []
    all_ids = []
    all_queries = []
    all_img_paths = []
    all_possible_answers = []
    all_query_types = []

    filename = None

    with mp.Pool(processes=num_processes, initializer=worker_init, initargs=(queues_results,)) \
            if config.multiprocessing else open(os.devnull, "w") as pool:
        try:
            n_batches = len(dataloader)

            for i, batch in tqdm(enumerate(dataloader), total=n_batches):

                # Combine all queries and get Codex predictions for them
                # TODO compute Codex for next batch as current batch is being processed

                if not config.use_cached_codex:
                    codes, messages = codex(prompt=batch['query'], input_type=input_type, extra_context=batch['extra_context'])
                else:
                    # codes = codes_all[i * batch_size:(i + 1) * batch_size]  # If cache
                    codes = [codes_all[trope] for trope in batch['trope']]

                # Run the code
                if config.execute_code:
                    if not config.multiprocessing:
                        # Otherwise, we would create a new model for every process
                        results = []
                        for c, sample_id, img, anno, possible_answers, query, gt in \
                                zip(codes, batch['sample_id'], batch['image'], batch['annotation'], batch['possible_answers'], batch['query'], batch['answer']):
                            result = run_program([c, sample_id, img, anno, possible_answers, query], queues_in, input_type)
                            result['groundtruth'] = gt
                            results.append(result)
                    else:
                        results = list(pool.imap(partial(
                            run_program, queues_in_=queues_in, input_type_=input_type),
                            zip(codes, batch['sample_id'], batch['image'], batch['annotation'], batch['possible_answers'], batch['query'])))
                else:
                    results = [{'code': c} for c in codes]
                    warnings.warn("Not executing code! This is only generating the code. We set the flag "
                                  "'execute_code' to False by default, because executing code generated by a language "
                                  "model can be dangerous. Set the flag 'execute_code' to True if you want to execute "
                                  "it.")

                all_answers += [r.get('answer', 'NO EXECUTION') for r in results]
                all_infos += [json.dumps(r.get('info', {}), indent=2) for r in results]
                all_codes += [r['code'] for r in results]
                all_compilation_errors += [r.get('compilation_error', 'NO EXECUTION') for r in results]
                all_runtime_errors += [r.get('runtime_error', 'NO EXECUTION') for r in results]
                all_reasons += [r.get('reason', 'NO EXECUTION') for r in results]
                all_tropes += batch.get('trope', ['no'] * len(batch['sample_id']))
                all_ids += batch['sample_id']
                all_groundtruths += batch['answer']
                all_possible_answers += batch['possible_answers']
                all_query_types += batch['query_type']
                all_queries += batch['query']
                all_img_paths += [dataset.get_sample_path(idx) for idx in batch['index']]
                if i % config.log_every == 0:
                    try:
                        accuracy = dataset.accuracy(all_answers, all_groundtruths, all_possible_answers, all_query_types)
                        console.print(f'Accuracy at Batch {i}/{n_batches}: {accuracy}')
                    except Exception as e:
                        console.print(f'Error computing accuracy: {e}')

                if i % config.log_every == 0 and config.save:
                    if filename is None:
                        results_dir = pathlib.Path(config['results_dir'])
                        results_dir = results_dir / config.dataset.split
                        results_dir.mkdir(parents=True, exist_ok=True)
                        if not config.save_new_results:
                            filename = 'results.csv'
                        else:
                            existing_files = list(results_dir.glob('results_*.csv'))
                            if len(existing_files) == 0:
                                filename = 'results_0.csv'
                            else:
                                filename = 'results_' + str(max([int(ef.stem.split('_')[-1]) for ef in existing_files if
                                                 str.isnumeric(ef.stem.split('_')[-1])]) + 1) + '.csv'
                    print('Saving results to', filename)
                    df = pd.DataFrame([all_answers, 
                                    all_groundtruths, 
                                    all_ids, 
                                    all_tropes, 
                                    all_queries, 
                                    all_img_paths,
                                    all_possible_answers,
                                    all_codes,
                                    all_infos,
                                    all_reasons,
                                    all_compilation_errors,
                                    all_runtime_errors]).T
                    df.columns = [
                        'answer', 
                        'groundtruth', 
                        'id', 
                        'trope',
                        'query', 
                        'img_path', 
                        'possible_answers', 
                        'code', 
                        'info', 
                        'reason', 
                        # 'reflection',
                        'compilation_error', 
                        'runtime_error'
                        ]
                    # make the result column a string
                    df.to_csv(results_dir / filename, header=True, index=False, encoding='utf-8', sep='|')

        except Exception as e:
            # print full stack trace
            traceback.print_exc()
            console.print(f'Exception: {e}')
            console.print("Completing logging and exiting...")

    try:
        accuracy = dataset.accuracy(all_answers, all_groundtruths, all_possible_answers, all_query_types)
        console.print(f'Final accuracy: {accuracy}')
    except Exception as e:
        print(f'Error computing accuracy: {e}')

    if config.save:
        print('Saving results to', filename)
        df = pd.DataFrame([all_answers, 
                           all_groundtruths, 
                           all_ids, 
                           all_tropes, 
                           all_queries, 
                           all_img_paths,
                           all_possible_answers,
                           all_codes,
                           all_infos,
                           all_reasons,
                        #    all_reflection,
                           all_compilation_errors,
                           all_runtime_errors]).T
        df.columns = [
            'answer', 
            'groundtruth', 
            'id', 
            'trope',
            'query', 
            'img_path', 
            'possible_answers', 
            'code', 
            'info', 
            'reason', 
            # 'reflection',
            'compilation_error', 
            'runtime_error'
            ]
        # make the result column a string
        df.to_csv(results_dir / filename, header=True, index=False, encoding='utf-8', sep='|')
        # torch.save([all_results, all_answers, all_codes, all_ids, all_queries, all_img_paths], results_dir/filename)

        if config.wandb:
            wandb.log({'accuracy': accuracy})
            wandb.log({'results': wandb.Table(dataframe=df, allow_mixed_types=True)})

    finish_all_consumers()


if __name__ == '__main__':
    main()
