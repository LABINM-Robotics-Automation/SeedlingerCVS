# import sys
# import warnings
# import numpy as np
# # caution: path[0] is reserved for script path (or '' in REPL)
# sys.path.insert(1, 'detectors')
# sys.path.insert(2, 'detectors/yolov7')

# # from detectors.maskrcnn import MaskRCNN
# from detectors.yolo7 import Yolo7
# import cv2

# class Detector:
#     def __init__(self, detector_name, weights, data, device):
#         print("Detector in building............!!!")
#         self.model = None

#         if detector_name is None:
#             warnings.warn('detector_name is a  object')
#             return

#         elif detector_name == 'yolo7':
#             self.model = Yolo7(weights=weights, data=data, device=device)

#         else:
#             warnings.warn('Model is not available')
#             return

#     def predict(self, input_rgb, input_depth):
#         if self.model is None:
#             warnings.warn('self.Model is a NoneType object, please select an available model')
#             return

#         predictions = self.model.predict(input_rgb)

#         if predictions is None:
#             warnings.warn('No predictions were made')
#             return None

#         depth_gray = cv2.cvtColor(input_depth, cv2.COLOR_BGR2GRAY)

#         closest_distance = float('inf')
#         closest_bbox = None

#         for pred in predictions:
#             x1, y1, x2, y2 = pred.bbox

#             # Calculate the centroid of the bounding box
#             centroid_x = (x1 + x2) / 2
#             centroid_y = (y1 + y2) / 2

#             # Get the depth value at the centroid
#             depth_value = depth_gray[int(centroid_y), int(centroid_x)]

#             # If depth value is valid (not NaN), consider it
#             if not np.isnan(depth_value):
#                 if depth_value < closest_distance:
#                     closest_distance = depth_value
#                     closest_bbox = pred.bbox

#         return closest_bbox


# if __name__ == '__main__':
#     img_rgb = cv2.imread('/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/scripts/capture_rgb/rgb_1.png')
#     img_depth = cv2.imread('/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/scripts/capture_depth/depth_1.png')

#     detector = Detector('yolo7', weights='./detectors/weights/yolov7-vseed.pt', data='./weights/opt.yaml', device='cuda:0')
#     closest_bbox = detector.predict(img_rgb, img_depth)

#     if closest_bbox is not None:
#         x1, y1, x2, y2 = closest_bbox
#         cv2.rectangle(img_rgb, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
#     else:
#         print("No plant detected or couldn't determine closest plant")

#     cv2.imshow('Detected Plant', img_rgb)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()


import sys
import warnings
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, 'detectors')
sys.path.insert(2, 'detectors/yolov7')

# from detectors.maskrcnn import MaskRCNN
from detectors.yolo7 import Yolo7
import cv2
import numpy as np


class Detector:
    def __init__(self, detector_name, weights, data, device):

        print("Detector in building............!!!")

        self.model = None

        # '''''''''' Warning: NoneType variable '''''''''''
        if detector_name is None:
            warnings.warn('detector_name is a NoneType object')
            return

        # # ''''''''''''''''' Mask RCNN ''''''''''''''''
        # elif detector_name == 'maskrcnn':
        #     self.model = MaskRCNN(weights= './detectors/maskrcnn/model_final.pth',
        #                           data="./detectors/maskrcnn/IS_cfg.pickle", 
        #                           device='cuda:0')

        # '''''''''''''''''' YoloV7 '''''''''''''''''''
        elif detector_name == 'yolo7':
            self.model = Yolo7(weights = weights, 
                               data = data, 
                               device = device)

        # '''''''''' Warning: Not available model '''''''''''
        else:
            warnings.warn('Model is not in available')
            return


    def predict(self, input, threshold=0.1):
        if self.model is None:
            warnings.warn('self.Model is a NoneType object, please select an available model')
            return
        
        predictions = self.model.predict(input, conf_thres=threshold)
        if predictions == None: return None
        bestPred = np.argmax([pred.conf for pred in predictions])  
        return [predictions[bestPred]]


if __name__=='__main__':

    img = cv2.imread('/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/gallery/horizontal.jpg')
    detector = Detector('yolo7', weights='./detectors/weights/yolov7-hseed.pt', data='./weights/opt.yaml', device='cuda:0')  # eg: 'yolov7' 'maskrcnn'
    predictions = detector.predict(img)

    for pred in predictions:
        x1, y1, x2, y2 = pred.bbox
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
        
        
    cv2.imshow('awd',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()