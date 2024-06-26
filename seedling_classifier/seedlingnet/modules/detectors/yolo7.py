import torch
import sys

sys.path.insert(1, 'yolov7')
from yolov7.models.common import DetectMultiBackend
from yolov7.utils.torch_utils import select_device, smart_inference_mode
from yolov7.utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams, PassImage
from yolov7.utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression,scale_segments, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from yolov7.utils.segment.general import process_mask, scale_masks, masks2segments

import matplotlib.pyplot as plt
import numpy as np
import cv2
import numpy as np
import os

import tkinter
import matplotlib
#matplotlib.use('TkAgg')


from object import my_object

class Yolo7:
    def __init__(self, weights, data, device):
        # parameters of the model (definition, weights, device)
        self.weights = weights
        self.data = data
        self.device = select_device(device)
        self.model = DetectMultiBackend(self.weights, device=self.device, dnn=False, data=self.data, fp16=False)
        
        # properties of the model (stride, names, pt)
        self.stride = self.model.stride
        self.names = self.model.names
        self.pt = self.model.pt

        # configuration of inferences
        self.max_det = 1000
        self.augment = False
        self.visualize = False
        self.classes = None
        self.agnostic_nms = False
        self.imgsz = [640, 640]
    

    def yolo7_prediction_to_objects(self, mask, det, conf, cls):
        mask = mask.cpu().numpy().astype(np.uint8)
        area = mask.sum()
        bbox = det[0:4].cpu().detach().numpy()
        conf = conf.cpu().detach().numpy()
        cls = cls.cpu().detach().numpy()
        return my_object(mask=mask, area=area, bbox=bbox, conf=conf, cls=cls)

    def plot_prediction(self, img, predictions):
        
        for pred in predictions:
            x, y, w, h = pred.bbox
            cv2.rectangle(img, (int(x), int(y)), (int(w), int(h)), (0,255,0), 2)

        return img

    def predict(self, img_source, conf_thres=0.1, iou_thres=0.5):
        #dataset = LoadImages(img_source, img_size = self.imgsz, stride = self.stride, auto = self.pt)
        dataset = PassImage(img_source, img_size = self.imgsz, stride = self.stride, auto = self.pt)
        self.model.warmup(imgsz=(1 if self.pt else self.bs, 3, *self.imgsz))  # warmup
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        image = []

        for idx, (path, im, im0s, vid_cap, s) in enumerate(dataset):

            with dt[0]:
                im = torch.from_numpy(im).to(self.device)
                im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim
            # Inference
            with dt[1]:
                pred, out = self.model(im, augment=False, visualize=False)
                proto = out[1]
            
            # NMS
            with dt[2]:
                pred = non_max_suppression(pred, conf_thres, iou_thres, self.classes, self.agnostic_nms, max_det=self.max_det, nm=32)
            
            for i, det in enumerate(pred):  # per image
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)
                
                if len(det):
                    masks = process_mask(proto[i], det[:, 6:], det[:, :4], im.shape[2:], upsample=True)  # HWC
                    det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()
                    conf = pred[0][:,4]
                    cls = pred[0][:,5]
                    
                    predictions = list(map(self.yolo7_prediction_to_objects, masks, det, conf, cls))

                    return predictions
        return None


if __name__ =='__main__':

    detector = Yolo7(weights='./weights/yolov7-hseed.pt',
                    data='./yolov7/opt.yaml', 
                    device='cuda:0')
    
    img = cv2.imread('gallery/horizontal.jpg')
    predictions = detector.predict(img)
    result = detector.plot_prediction(img, predictions)

    cv2.imshow('Vertical Seedling',result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



