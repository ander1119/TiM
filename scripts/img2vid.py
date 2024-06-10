import cv2
import os
import argparse
from pathlib import Path
from tqdm import tqdm
import concurrent.futures

def process_folder(args, folder):
    jpg_folder = args.root_folder / folder

    tmp = sorted(os.listdir(jpg_folder))[0]
    tmp = cv2.imread(str(jpg_folder / tmp))
    resolution = (tmp.shape[1], tmp.shape[0])

    output_video = str(args.output_folder / folder) + '.mp4'
    # print(output_video)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, args.frame_rate, resolution)

    for jpg_file in tqdm(sorted(os.listdir(jpg_folder)), desc=folder):
        if jpg_file.endswith('.jpg'):
            jpg_path = jpg_folder / jpg_file
            frame = cv2.imread(str(jpg_path))
            out.write(frame)
    out.release()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root_folder', type=Path, help='Root path to MovieNet keyframe folder', required=True)
    parser.add_argument('--output_folder', type=Path, help='Output folder for transformed MP4 files', required=True)
    parser.add_argument('--frame_rate', type=int, help='Frame rate of the output MP4 files (depends on your model)', default=10)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    if not args.root_folder.exists():
        raise FileNotFoundError(args.root_folder)
    if not args.output_folder.exists():
        args.output_folder.mkdir(parents=True)
    if not args.output_folder.is_dir():
        raise NotADirectoryError(args.output_folder)
    if not args.root_folder.is_dir():
        raise NotADirectoryError(args.root_folder)

    with concurrent.futures.ThreadPoolExecutor(48) as executor:
        folders = sorted(os.listdir(args.root_folder))
        executor.map(process_folder, [args, folders])

    print("All folders processed.")
    

if __name__ == '__main__':
    main()

