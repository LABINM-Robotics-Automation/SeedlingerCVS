import torch
import torch.nn as nn

import os
import pandas as pd
from torchvision.io import read_image
from PIL import Image 
from torchvision.transforms import ToTensor
from torch.utils.data import Dataset
import numpy as np
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from torchvision import transforms
from tqdm import tqdm
from model import RegressionModel

def meanStdFromTensor(tensor):
    mean = tensor.mean(dim=-1, keepdim=True)
    std = tensor.std(dim=-1, unbiased=False, keepdim=True)
    return mean, std

def normalizeTensor(tensor, mean, std):
    return ((tensor - mean)/std).float()

def calculate_mask_area(pil_mask):
    mask_array = np.array(pil_mask)
    area = np.sum(mask_array != 0)
    return area

def tensor2image(tensor):
    reverse_transforms = transforms.Compose([
        transforms.Lambda(lambda t: (t + 1) / 2),
        transforms.Lambda(lambda t: t.permute(1, 2, 0)), # CHW to HWC
        transforms.Lambda(lambda t: t * 255.),
        transforms.Lambda(lambda t: t.numpy().astype(np.uint8)),
        transforms.ToPILImage(),
    ])

    return reverse_transforms(tensor)

def image2tensor(image):
    image2tensor_transformation = transforms.Compose([
            transforms.Resize(size = (224,224)),
            transforms.ToTensor(),
            transforms.Lambda(lambda t: (t * 2) - 1) # Scale between [-1, 1]
    ])

    return image2tensor_transformation(image)

def crop_image(image, bbox, outSize):
    # Read the image
    
    # Extract the coordinates from the bounding box
    x1, y1, x2, y2 = bbox
    x = (x1+x2)//2
    y = (y1+y2)//2
    
    # Calculate the region to be cropped around the center
    crop_left = x - outSize #max(0, )
    crop_upper = y - outSize #max(0, )
    crop_right = x + outSize #min(image.width, )
    crop_lower = y + outSize #min(image.height, )
    
    # Crop the image using the calculated region
    cropped_image = image.crop((crop_left, crop_upper, crop_right, crop_lower))
   
    return cropped_image

def getMaskArea(pilMask):
    mask_array = np.array(pilMask)
    area = np.sum(mask_array != 0)
    return area


class LinearModel:
    def __init__(self, weights_path):
        self.model = torch.load(weights_path)
        self.meanArea = 11126.129921259842 
        self.stdArea = 2670.4216664828896
        self.meanLength = 72.38188976377953 
        self.stdLength = 15.946278845775213
        self.treshold = 50
    
    @torch.no_grad()
    def classify(self, horizontalMask, verticalMask):

        horizontalMask = Image.fromarray(horizontalMask)
        horizontal_bbox = horizontalMask.getbbox()
        maskHorCrop = crop_image(horizontalMask, horizontal_bbox, 130)
        maskHorResz = maskHorCrop.resize((224,224), Image.LANCZOS)
        areaHor = np.array([float(getMaskArea(maskHorResz))]).reshape(1,1)

        verticalMask = Image.fromarray(verticalMask)
        vertical_bbox = verticalMask.getbbox()
        maskVerCrop = crop_image(verticalMask,vertical_bbox, 130)
        maskVerResz = maskVerCrop.resize((224,224), Image.LANCZOS)
        areaVer = np.array([float(getMaskArea(maskVerResz))]).reshape(1,1)

        areaTotal = areaVer + areaHor

        areaTotalNormalized = normalizeTensor(torch.tensor(areaTotal), torch.tensor(self.meanArea), torch.tensor(self.stdArea))
        lengthNormalized = self.model(areaTotalNormalized)
        estimatedLength = lengthNormalized*self.stdLength + self.meanLength
        
        return estimatedLength.item() > self.treshold
    


    
