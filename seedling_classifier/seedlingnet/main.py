import sys

sys.path.append('modules')
sys.path.append('modules/detectors')
sys.path.append('modules/detectors/yolov7')

from seedling_classifier.seedlingnet.modules.detector import Detector

import cv2

if __name__=='__main__':


    img = cv2.imread('./modules/detectors/gallery/horizontal.jpg')
    detector = Detector('yolo7', weights='./modules/detectors/weights/yolov7-hseed.pt', data='weights/opt.yaml', device='cuda:0')  # eg: 'yolov7' 'maskrcnn'
    predictions = detector.predict(img)

    for pred in predictions:
        x1, y1, x2, y2 = pred.bbox
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
        
    
    cv2.imshow('awd',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()