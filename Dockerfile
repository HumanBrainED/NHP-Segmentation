# Use PyTorch Latest Version
FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime
MAINTAINER Xinhui Li <xinhui.li@childmind.org>

# Install Scipy Nibabel Libary
RUN pip install scipy nibabel

# Copy UNet Codes and Models into Image
COPY *.py /unet_model/
COPY unet_model/* /unet_model/models/

# Add UNet Path into ENV
ENV DIMGNAME="xinhui1017/deepseg" \
    PYTHONPATH="/unet_model:$PYTHONPATH" \
    PATH="/unet_model:/unet_model/models/:$PATH"

WORKDIR /unet_model/models
CMD python3 /unet_model/docker_Help.py
