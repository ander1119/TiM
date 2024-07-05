# TiM
Trope in Movies (TiM) comprises (1) 684 movies, each annotated with per-shot keyframes, subtitles, and trope labels, and (2) 95 trope identification queries accompanied by their definitions.

TiM is designed as a testbed for exploring two critical yet previously overlooked video reasoning skills: (1) Abstract Perception: understanding and tokenizing abstract concepts in videos, and (2) Long-range Compositional Reasoning: planning and integrating intermediate reasoning steps for managing long-range videos with numerous input.

## Data Preparation
Please download images, QA annotations and subtiltes for multimodality usage from [here](https://drive.google.com/drive/folders/11RqbFUogRdU6MAJmnz9OrtZTWR9sx1Ia?usp=sharing)
Or you can download images from [MovieNet](https://movienet.github.io/) official website

### Movie keyframes
From our link you can download zip file with difference settings:
- *fullset.zip*: 684 movie folders with keyframes
- *vdset.zip*: subset of fullset, contatins 246 movies that has subtitles in seperate annotation file
- *mainset.zip*: subset of vdset, contains 50 movies that has subtitles in seperate annotation file
You can use the pre-preprocessing script to concatenate keyframes into .mp4 file, which is usually applied in video-qa method

### QA annotations
We also provided difference settings' annotations file:
- *tim_fullset.json*: 684 movies + 95 tropes QA (total 64980)
- *tim_vdset.json*: 246 movies(with subtitles) + 95 tropes QA (total 23370)
- *tim_mainset.json*: 50 movies(with subtitles) + 20 tropes QA (total 1000)
  
annotation format:
```json=
[
    {
        "video": "tt1637725",          # IMDB ID
        "num_option": 2,
        "a0": "yes",
        "a1": "no",
        "trope": "Big Bad",            # Trope name
        "category": "Character Trait", # Trope category
        "qid": "tt1637725_0",          # {IMDB ID}_{Trope ID}
        "answer": 1,                   # groundtruth
        "question": "Is the trope '{Trope name}', which means '{Trope definition}', relevant to the movie?"
    }
]
```

### Subtitles (for multi-modality)
*subtitles.zip* contains 246 json files, the filename corresponded to IMBb movie ID

json file format:
```json=
{
    "shot_{shot_idx}_img_{img_idx}": # correspond to image filename in keyframe folder
    {
        "bboxes": [], # deprecated
        "subtitles": 
        [
            subtitle1,
            subtitle2,
            ...
        ] # subtitles within the shot
    } 
}
```

## Usage
We made some modification on SOTA method and enable them accepting format of TiM dataset, the modification is detailed documented in [fevori](fevori/README.md). Once the data preparation is ready, you can reproduce the result by following the instruction step by step.

## SOTA Method on Different Settings
### Fullset (Single Modality)
| Method        | # Frames        | Pre.  | Rec.  | F1    | CT-F1 | RI-F1 | ST-F1 | SL-F1 |
|---------------|-----------------|-------|-------|-------|-------|-------|-------|-------|
| Random        | -               | 12.24 | 48.48 | 19.54 | 19.23 | 19.99 | 17.37 | 23.37 |
| LLoVi         | everyshot       | 20.47 | 17.67 | 18.97 | 13.46 | 16.67 | 15.22 | 25.58 |
| SeViLA†       | 120 → 16        | 12.35 | 96.71 | 21.90 | 25.12 | 19.02 | 22.38 | 20.96 |
| SeViLA        | 120 → 16        | 15.29 | 51.75 | 23.31 | 21.13 | 21.89 | 17.81 | 27.58 |
| Viper         | 16 (SeViLA†)    | 13.26 | 67.33 | 22.15 | 21.58 | 19.92 | 23.50 | 24.60 |
| Viper         | 16 (SeViLA)     | 14.09 | 68.70 | 23.39 | 21.41 | 24.62 | 20.99 | 26.85 |
| FEVoRI(Ours)  | 120             | 27.07 | 32.32 | 29.42 | 12.36 | 22.75 | 35.62 | 48.78 |
| Gemini 1.5    | 120             | 38.37 | 34.42 | 40.74 | 40.45 | 38.79 | 38.55 | 45.11 |
### Mainset (Multi-Modality)
| Method        | # Frames        | Pre.  | Rec.  | F1    | CT-F1 | RI-F1 | ST-F1 | SL-F1 |
|---------------|-----------------|-------|-------|-------|-------|-------|-------|-------|
| Random        | -               | 14.14 | 50.08 | 22.06 | 20.26 | 21.24 | 19.50 | 23.92 |
| LLoVi         | everyshot       | 31.35 | 17.21 | 18.78 | 20.20 | 24.40 | 35.95 | 40.63 |
| SeViLA†       | 120 → 16        | 17.30 | 89.33 | 28.98 | 22.64 | 24.76 | 32.83 | 35.79 |
| SeViLA        | 120 → 16        | 22.98 | 58.18 | 28.54 | 28.92 | 25.00 | 37.50 | 42.86 |
| LLaMA-VID     | 240             | 15.56 | 90.12 | 26.53 | 25.72 | 24.60 | 28.31 | 38.15 |
| Viper         | 16 (SeViLA†)    | 14.58 | 37.87 | 21.05 | 18.15 | 14.35 | 20.58 | 31.56 |
| Viper         | 16 (SeViLA)     | 14.38 | 38.79 | 20.98 | 24.39 | 15.22 | 18.02 | 24.76 |
| Viper         | 120             | 27.78 | 21.74 | 24.39 | 22.91 | 19.59 | 40.43 | 48.78 |
| FEVoRI        | 120             | 27.88 | 39.80 | 32.79 | 30.52 | 29.55 | 42.42 | 49.67 |
| FEVoRI+ConQueR | 120            | 32.11 | 51.28 | 39.64 | 42.80 | 34.48 | 39.78 | 55.17 |
### Ablation Study for FEVoRI on Mainset
| Method | Modality | # Frames  | VLM    | Coder | Pre.  | Rec.  | F1    | CT-F1 | RI-F1 | ST-F1 | SL-F1 |
|--------|----------|-----------|--------|-------|-------|-------|-------|-------|-------|-------|-------|
| FRVoRI | V+D      | 120       | BLIP-2 | GPT-4 | 27.88 | 39.80 | 32.79 | 30.52 | 29.55 | 42.42 | 49.67 |
|        | **V**     | 120      | BLIP-2 | GPT-4 | 27.07 | 32.23 | 29.42 | 12.36 | 22.75 | 35.62 | 48.00 |
|        | V+D      | **everyshot** | BLIP-2 | GPT-4 | 27.27 | 46.15 | 34.29 | 33.30 | 30.12 | 44.68 | 50.00 | 
|        | V+D      | **16**        | BLIP-2 | GPT-4 | 25.71 | 40.72 | 31.52 | 23.74 | 25.56 | 38.83 | 47.54 | 
|        | V+D      | 120       | **Gemini** | GPT-4 | 29.37 | 51.15 | 37.31 | 28.71 | 29.49 | 47.17 | 53.23 | 
|        | V+D      | 120       | BLIP-2 | **GPT-3.5** | 30.16 | 35.52 | 32.62| 27.18 | 30.34 | 39.56 | 38.65|

## Acknowledgement
Our reproduction of the methods is based on the respective official repositories, we thank the authors to release their code. If you use the related part, please cite the corresponding paper commented in the code.