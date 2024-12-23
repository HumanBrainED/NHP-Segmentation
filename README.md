# NHP-Segmentation (DeepSeg)

This repository includes U-Net tissue segmentation code for non-human primate structure MRI data. 

### Docker Image
1. Pull

The docker image has been uploaded onto DockerHub, download it by using the following command
```
docker pull xinhui1017/deepseg:latest
```

2. Run

Perform segmentation
```
docker run -v <NHP-Segmentation local dir>:/wd xinhui1017/deepseg:latest segment.py -in /wd/data/sub-032215_ses-001_run-1_T1w.nii.gz -model /wd/unet_model/nhp-model-04-epoch
```
U-Net result will be saved in `/wd/data/sub-032215_ses-001_run-1_T1w_pre_mask.nii.gz`

3. Helper

Check the helper page for more usage
```
docker run xinhui1017/deepseg:latest
```

4. Storage Requirement

~4GB hard disk space for whole docker image

### Set Up Environment

1. Clone repository
```
git clone https://github.com/HumanBrainED/NHP-Segmentation.git
```

2. Create a virtual environment and activate the environment
```
conda create --name nhpseg python=3.7
conda activate nhpseg
```

3. Install dependencies
```
cd NHP-Segmentation
pip3 install -r requirements.txt
```

### Organize Dataset

We first create three folders to store our training, validation and test set respectively. Within each folder, put all T1w images in one folder and all masks in another folder. One dataset structure example is below:
```
/root/data/
└── train
    └── T1w
        ├── sub-1_T1w.nii.gz
        └── sub-2_T1w.nii.gz
        └── ...
    └── mask
        ├── sub-1_mask.nii.gz
        └── sub-2_mask.nii.gz
        └── ...
└── valid
    └── T1w
        ├── sub-1_T1w.nii.gz
        └── ...
    └── mask
        ├── sub-1_mask.nii.gz
        └── ...
└── test
    └── T1w
        ├── sub-1_T1w.nii.gz
        └── ...
```

### Train U-Net Model

We can use the command line below to train the U-Net model:
```
python train_unet.py -trt1w <T1w training set path> -trmsk <mask training set path> -out <U-Net model output path> -epoch 10
```

Change paths based on your dataset structure. For example, if the data is organized as the example above, replace `<T1w training set path>` with `/root/data/train/T1w` and replace `<mask training set path>` with `/root/data/train/mask`.

If you want to resume training process based on an existing model, add the argument `-init <U-Net model path>` to the command line where `<U-Net model path>` is your previous model path.

### Test U-Net model

We can use the command line below to test the U-Net model:
```
python segment.py -in <T1w test set path> -out <U-Net mask output path> -model <U-Net model path>
```

The U-Net segmentation mask outputs will be stored in `<U-Net mask output path>`.

### Developer Notes

- dataset.py is used to change 3D MRI volume data to 2D slices as the input to U-Net model.

- model.py is used to define U-Net model architecture.

- function.py is used to define helper functions, such as mask prediction, FP/FN estimation, and dice coefficient calculation etc.

### References

```
@inproceedings{li2024deepseg,
  title={DeepSeg: A transfer-learning segmentation tool for limited sample training of nonhuman primate MRI},
  author={Li, Xinhui and Wang, Xindi and Mantell, Kathleen and Casillo, Estefania Cruz and Milham, Michael and Opitz, Alexander and Xu, Ting},
  booktitle={2024 46th Annual International Conference of the IEEE Engineering in Medicine and Biology Society (EMBC)},
  pages={1--4},
  year={2024},
  organization={IEEE}
}

@article{wang2021,
  title={U-net model for brain extraction: Trained on humans for transfer to non-human primates},
  author={Wang, Xindi and Li, Xin-Hui and Cho, Jae Wook and Russ, Brian E and Rajamani, Nanditha and Omelchenko, Alisa and Ai, Lei and Korchmaros, Annachiara and Sawiak, Stephen and Benn, R Austin and others},
  journal={Neuroimage},
  volume={235},
  pages={118001},
  year={2021},
  publisher={Elsevier}
}
```
