# FEVoRI
This is implementation of Face-Enhanced Viper of Role Interactions (FEVoRI) and Context Query Reduction (ConQueR) based on [ViperGPT](https://viper.cs.columbia.edu/)

## Installation
Please follow the Installation section in [ViperGPT](https://github.com/cvlab-columbia/viper) step by step

## Usage

### Prepare TiM QA Annotation
Please download TiM dataset from [here](https://github.com/ander1119/TiM) and place QA annotation under specific folder path

### Code Generation
To reduce the cost on repeatly generating same trope identification code when running on TiM. You can follow the sample code generation configuration in `configs/code_generation` to generate trope identification functions under different settings first:
For example, the below command generate code with **FEVoRI+ConQueR** method. The config naming convention is `{modality}_{face Identification}_{coder}_{ICL Example}`

```bash
CONFIG_NAMES=code_generation/v+d_df_gpt4_complex python main_batch.py
```

After code generation, there should be new `.csv` code file under `cached_code\v+d_df_gpt4_complex`.

### Run on TiM
Then you can run the same trope identification function on different movies
```bash
CUDA_VISIBLE_DEVICES=0 CONFIG_NAMES=ablations/v+d_df_gpt4_complex python main_batch.py
```

### Evaluation
The result file should be placed under `results/`, and you can use `eval.py` to evaluate the performance
```bash
python eval.py path/to/result.csv
```

## Citation

If you use this code, please consider citing the paper as:

```
@article{su2024investigating,
  title={Investigating Video Reasoning Capability of Large Language Models with Tropes in Movies},
  author={Su, Hung-Ting and Chao, Chun-Tong and Hsu, Ya-Ching and Lin, Xudong and Niu, Yulei and Lee, Hung-Yi and Hsu, Winston H},
  journal={arXiv preprint arXiv:2406.10923},
  year={2024}
}
```