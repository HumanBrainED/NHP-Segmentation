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

#### Code

- dataset.py is used to change 3D MRI volume data to 2D slices as the input to U-Net model.

- model.py is used to define U-Net model architecture.

- function.py is used to define helper functions, such as mask prediction, FP/FN estimation, and dice coefficient calculation etc.

#### CMI Server Data

- [Document](https://docs.google.com/document/d/1_LHjuYDsaXAJn5XrTBV70_s7d9sL3r7eQZobXxzcIlo/edit?usp=sharing)

### References

[1] [Wang et al., U-net model for brain extraction: Trained on humans for transfer to non-human primates, 2021, NeuroImage](https://www.sciencedirect.com/science/article/pii/S1053811921002780)

[2] [Li et al., Toward Automatic Segmentation for Non-human Primates, 2021, NIBS Workshop](https://nibs-workshop.umn.edu/sites/nibs-workshop.umn.edu/files/2021-06/Xinhui_Li.pdf)
