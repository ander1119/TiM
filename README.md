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
We made some modification on SOTA method and enable them accepting format of TiM dataset, the modification is detailed documented in each README. Once the data preparation is ready, you can reproduce the result by following the instruction step by step.

## Result on Different settings
TODO

## Acknowledgement
Our reproduction of the methods is based on the respective official repositories, we thank the authors to release their code. If you use the related part, please cite the corresponding paper commented in the code.