import torch
import torch.nn as nn
import numpy as np
import scipy.ndimage as snd
from torch.autograd import Variable
from torchvision.transforms import ToPILImage, ToTensor
import torchvision.transforms.functional as PIL
from dataset import VolumeDataset, BlockDataset
from torch.utils.data import DataLoader
from model import UNet2d
import os, sys
import nibabel as nib
import pickle
import argparse

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        self.exit(2)

def write_nifti(data, aff, shape, out_path):
    data=data[0:shape[0],0:shape[1],0:shape[2]]
    img=nib.Nifti1Image(data, aff)
    img.to_filename(out_path)

def estimate_dice(gt_msk, prt_msk, num_class):
    dice = np.zeros(num_class)
    for i in range(0, num_class):
        gt = gt_msk == i
        gt = gt * 1
        prt = prt_msk == i
        prt = prt * 1
        intersection=gt*prt
        dice[i]=2*float(intersection.sum())/float(gt.sum()+prt.sum())

    return dice

def estimate_fn_fp(gt_msk, prt_msk, num_class):
    msk_shape = prt_msk.shape
    fn_fp = np.zeros((num_class-1, msk_shape[0], msk_shape[1], msk_shape[2]))

    for i in range(1, num_class):
        gt = gt_msk == i
        gt = gt * 1

        prt = prt_msk == i
        prt = prt * 1

        fn_fp[i-1,:,:,:] = prt - gt

    return fn_fp

def extract_large_comp(prt_msk):
    labs, num_lab=snd.label(prt_msk) # ???
    c_size=np.bincount(labs.reshape(-1))
    c_size[0]=0
    max_ind=c_size.argmax()
    prt_msk=labs==max_ind
    return prt_msk

def predict_volumes(model, rimg_in=None, cimg_in=None, bmsk_in=None, suffix="pre_mask",
        save_dice=False, save_nii=False, nii_outdir=None, verbose=False, 
        rescale_dim=256, num_slice=3, num_class=7):
    use_gpu=torch.cuda.is_available()
    model_on_gpu=next(model.parameters()).is_cuda
    use_bn=True
    if use_gpu:
        if not model_on_gpu:
            model.cuda()
    else:
        if model_on_gpu:
            model.cpu()

    NoneType=type(None)
    if isinstance(rimg_in, NoneType) and isinstance(cimg_in, NoneType):
        print("Input rimg_in or cimg_in")
        sys.exit(1)

    if save_dice:
        dice_dict=dict()
    
    volume_dataset=VolumeDataset(rimg_in=rimg_in, cimg_in=cimg_in, bmsk_in=bmsk_in)
    volume_loader=DataLoader(dataset=volume_dataset, batch_size=1)
    
    for idx, vol in enumerate(volume_loader):
        if len(vol)==1: # just img
            ptype=1 # Predict
            cimg=vol
            bmsk=None
            block_dataset=BlockDataset(rimg=cimg, bfld=None, bmsk=None, num_slice=num_slice, rescale_dim=rescale_dim)
        elif len(vol)==2: # img & msk
            ptype=2 # image test
            cimg=vol[0]
            bmsk=vol[1]
            block_dataset=BlockDataset(rimg=cimg, bfld=None, bmsk=bmsk, num_slice=num_slice, rescale_dim=rescale_dim)
        elif len(vol==3): # img bias_field & msk
            ptype=3 # image bias correction test
            cimg=vol[0]
            bfld=vol[1]
            bmsk=vol[2]
            block_dataset=BlockDataset(rimg=cimg, bfld=bfld, bmsk=bmsk, num_slice=num_slice, rescale_dim=rescale_dim)
        else:
            print("Invalid Volume Dataset!")
            sys.exit(2)
        
        rescale_shape=block_dataset.get_rescale_shape()
        raw_shape=block_dataset.get_raw_shape()

        raw_shape_list=list(raw_shape)
        raw_shape_list.insert(0, num_class)
        raw_shape_expanded=torch.Size(raw_shape_list) 
        
        for od in range(3):
            backard_ind=np.arange(3)
            backard_ind=np.insert(np.delete(backard_ind, 0), od, 0)

            block_data, slice_list, slice_weight=block_dataset.get_one_directory(axis=od)
            pr_bmsk=torch.zeros([num_class, len(slice_weight), rescale_dim, rescale_dim])

            if use_gpu:
                pr_bmsk=pr_bmsk.cuda()
            for (i, ind) in enumerate(slice_list): # length of slice_list: 202
                if ptype==1:
                    rimg_blk=block_data[i]
                    if use_gpu:
                        rimg_blk=rimg_blk.cuda()
                elif ptype==2:
                    rimg_blk, bmsk_blk=block_data[i]
                    if use_gpu:
                        rimg_blk=rimg_blk.cuda()
                        bmsk_blk=bmsk_blk.cuda()
                else:
                    rimg_blk, bfld_blk, bmsk_blk=block_data[i]
                    if use_gpu:
                        rimg_blk=rimg_blk.cuda()
                        bfld_blk=bfld_blk.cuda()
                        bmsk_blk=bmsk_blk.cuda()
                pr_bmsk_blk=model(torch.unsqueeze(Variable(rimg_blk), 0)) # model!!!

                for i_class in range(0,num_class):
                    pr_bmsk[i_class, ind[1], :, :]=pr_bmsk_blk.data[0][i_class, :, :]

            if use_gpu:
                pr_bmsk=pr_bmsk.cpu()
            
            pr_bmsk=pr_bmsk.permute(0, backard_ind[0]+1, backard_ind[1]+1, backard_ind[2]+1)

            pr_bmsk=pr_bmsk[:, :rescale_shape[0], :rescale_shape[1], :rescale_shape[2]]
            
            pr_tmsk=torch.zeros(raw_shape_list)

            for i_class in range(0,num_class):
                uns_pr_bmsk=torch.unsqueeze(pr_bmsk[i_class,:,:,:], 0) # append one more dim at index 0, eg, uns_pr_bmsk torch.Size([1, 6, 204, 256, 256])
                uns_pr_bmsk=torch.unsqueeze(uns_pr_bmsk, 0) # torch.Size([1, 1, 6, 204, 256, 256])
                uns_pr_bmsk=nn.functional.interpolate(uns_pr_bmsk, size=raw_shape, mode="trilinear", align_corners=False)
                pr_tmsk[i_class,:,:,:]=torch.squeeze(uns_pr_bmsk)

            if od==0:
                pr_3_bmsk=torch.unsqueeze(pr_tmsk, 4)
            else:
                pr_3_bmsk=torch.cat((pr_3_bmsk, torch.unsqueeze(pr_tmsk, 4)), dim=4)

        pr_bmsk=pr_3_bmsk.mean(dim=4)
        
        pr_bmsk=pr_bmsk.numpy()

        pr_bmsk_final = np.argmax(pr_bmsk, axis=0)
        
        if isinstance(bmsk, torch.Tensor):
            bmsk=bmsk.data[0].numpy()
            dice=estimate_dice(bmsk, pr_bmsk_final, num_class)
            if verbose:
                print(dice)
            fn_fp=estimate_fn_fp(bmsk, pr_bmsk_final, num_class)

        t1w_nii=volume_dataset.getCurCimgNii()
        t1w_path=t1w_nii.get_filename()
        t1w_dir, t1w_file=os.path.split(t1w_path)
        t1w_name=os.path.splitext(t1w_file)[0]
        t1w_name=os.path.splitext(t1w_name)[0]

        if save_nii:
            t1w_aff=t1w_nii.affine
            t1w_shape=t1w_nii.shape

            if isinstance(nii_outdir, NoneType):
                nii_outdir=t1w_dir
            
            if not os.path.exists(nii_outdir):
                os.mkdir(nii_outdir)
            
            out_path=os.path.join(nii_outdir, t1w_name+"_"+suffix+".nii.gz")
            write_nifti(np.array(pr_bmsk_final, dtype=np.float32), t1w_aff, t1w_shape, out_path)

            """
            # plot FN/FP maps
            if isinstance(bmsk, torch.Tensor):
                # import pdb;pdb.set_trace()
                for i_class in range(0,num_class-1):
                    out_path=os.path.join(nii_outdir, t1w_name+"_"+suffix+"_fnfp_"+str(i_class)+".nii.gz")
                    write_nifti(np.array(fn_fp[i_class,:,:,:], dtype=np.float32), t1w_aff, t1w_shape, out_path)
            
            # plot probabiltiy maps 
            for i_class in range(0,num_class):
                out_path=os.path.join(nii_outdir, t1w_name+"_"+suffix+"_"+str(i_class)+".nii.gz")
                write_nifti(np.array(pr_bmsk[i_class,:,:,:], dtype=np.float32), t1w_aff, t1w_shape, out_path)
            """

        if save_dice:
            dice_dict[t1w_name]=dice

    if save_dice:
        return dice_dict

# Unit test
if __name__=='__main__':
    pass
