import os
import sys
import warnings
import random
from datetime import datetime
import numpy as np

import cv2
import pyzed.sl as sl

sys.path.append('seedling_classifier')
sys.path.append('seedling_classifier/seedlingnet/modules')
sys.path.append('seedling_classifier/seedlingnet/modules/detectors')
sys.path.append('seedling_classifier/seedlingnet/modules/detectors/yolov7')
sys.path.append('seedling_classifier/seedlingnet/modules/classifiers')

from seedling_classifier.seedlingnet.modules.detector import Detector
from seedling_classifier.seedlingnet.modules.classifier import Classifier

global h_detector, v_detector, linear
h_detector = None
v_detector = None
cam_h = None
cam_v = None
linear = ""
h_wpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/modules/' + \
        'detectors/weights/yolov7-hseed.pt'
v_wpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/modules/' + \
        'detectors/weights/yolov7-vseed.pt'
dpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/seedlingnet/modules/' + \
        'detectors/weights/opt.yaml'

lmp = '/seedling_classifier/seedlingnet/modules/classifiers/weights/linearModel.pt'
CLASSIFIER_WEIGHTS = os.getcwd() + lmp

HORIZONTAL_DELIMITER = 240


def call_yolo_predict(axis, img, mask=None):
    global h_detector, v_detector
    v_pmask = None
    if axis == "h":
        print("Getting predictions for horizontal poit of view")
        if h_detector == None:
            h_detector = Detector(
                'yolo7',
                weights=h_wpath,
                data=dpath,
                device='cuda:0'
            )
        predictions = h_detector.predict(img, threshold=0.4)

        if predictions is not None:
            
            correct_predictions = []
            for pred in predictions:
                x1, y1, x2, y2 = pred.bbox
                #if y1<y2: y2 = y1
                if (y1) > 230: continue
                if (y2) > 315: continue
                correct_predictions.append(pred)
            
            predictions = correct_predictions
        else:
            predictions = None

    elif axis == "v":
        print("Getting predictions for vertical poit of view")
        if v_detector == None:
            v_detector = Detector(
                'yolo7',
                weights=v_wpath,
                data=dpath,
                device='cuda:0'
            )
        predictions = v_detector.predict(img)
        if predictions is not None:
            #there is v predictions
            pl = len(predictions)
            if pl == 1:
                v_pmask = cv2.resize(
                    predictions[0].mask*255,
                    (mask.shape[1], mask.shape[0]),
                    interpolation=cv2.INTER_LINEAR
                )
        else:
            v_pmask = np.zeros(img.shape, dtype = np.uint8)

    else:
        raise Exception("Invalid axis inserted")

    print(f"Prediction result: {predictions}")
    return predictions, v_pmask

def get_type_of_seedling(hp, vp, vm):
    global linear
    tos = 0
    if hp is None or vp is None or hp == [] or vp == []:
        tos = 1
        print("*"*100)
        print("NOT SEEDLING DETECTED")
        print("*"*100)

    else:
        if len(hp) > 1 or len(vp) > 1:
            print("*"*100)
            print("Issues with number of seedlings detected")
            print(f"Seedlings found in H view: {len(hp)}")
            print(f"Seedlings found in V view: {len(vp)}")
            print("*"*100)
        else:
            print("*"*100)
            print("Seedling detected properly")
            print("*"*100)

            v_pred_mask = cv2.resize(
                vm*255,
                (vm.shape[1], vm.shape[0]),
                interpolation=cv2.INTER_LINEAR
            )

            h_pred_mask = hp[0].mask

            #load the model if necessary
            if linear == "":
                linear = Classifier('linear',CLASSIFIER_WEIGHTS)
            #get prediction
            category = linear.predict(h_pred_mask, v_pred_mask)

            if category:
                tos = 3
            else:
                tos = 2
    print("*"*100)
    print(f"Result of getting the type of seedling: {tos}")
    print("*"*100)
    return tos

def print_prediction_info(predictions, img, top):
    cv2.line(img, (10, HORIZONTAL_DELIMITER), (100, HORIZONTAL_DELIMITER), (0, 255, 0), thickness=2)

    if predictions is None or predictions == []:
        print(f"Point of view: {top}")
        print('Image Shape:',(img.shape), 'does not contains a seedling')

    else:
        for pred in predictions:
            x1, y1, x2, y2 = pred.bbox
            print(f'Image with shape: {img.shape}')
            print('contains a seedling with bounding box:')
            print(f'{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}')

            x, y, w, h = pred.bbox
            cv2.rectangle(img, (int(x), int(y)), (int(w), int(h)), (0,255,0), 2)


    cv2.imshow('Image',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def init_h_cam():
    global cam_h
    while True:
        try:
         #Instantiate the camera object      
            cam_h = cv2.VideoCapture(0)
            #Warming up the camera, sort of
            for i in range(5):
                cam_h.read()
                # Check if the camera opened successfully
            if not cam_h.isOpened():
                raise Exception("Error: Unable to open X-axis camera.") 
            break
        except Exception as e:
            # Optionally handle the exception in some way, like logging
            print(f"An error occurred: {e}")

    #return cam_h

def init_and_capture_v_cam():
    global cam_v

    if cam_v == None:
        cam_v = sl.Camera()

        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD1080
        init_params.camera_fps = 30
        init_params.depth_mode = sl.DEPTH_MODE.NEURAL
        init_params.coordinate_units = sl.UNIT.METER
        init_params.depth_minimum_distance = 0.4
        init_params.depth_maximum_distance = 0.8
        init_params.camera_image_flip = sl.FLIP_MODE.AUTO
        init_params.depth_stabilization = 1 
        runtime_params = sl.RuntimeParameters(
            confidence_threshold=50,
            enable_fill_mode=True,
            texture_confidence_threshold=200
        )

        err = cam_v.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            print(err)
            sys.exit()
        
        assert cam_v.grab(runtime_params) == sl.ERROR_CODE.SUCCESS, \
        'La cámara Zed no esta ejecutandose correctamente,' + \
        'verificar su conexion'

    depth_map = sl.Mat()
    image = sl.Mat()


    threshold_value = 130
    cam_v.retrieve_image(depth_map, sl.VIEW.DEPTH)
    numpy_depth_map = depth_map.get_data()
    gray = cv2.cvtColor(numpy_depth_map[:,:,0:3], cv2.COLOR_BGR2GRAY)
    gray = gray[290:890, 670:1550]
    _, mask = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    assert len(mask.shape) == 2, 'Verificar que se reciba una mascara' + \
                                 f'se recibe {mask.shape}'

    cam_v.retrieve_image(image, sl.VIEW.LEFT)
    numpy_image = image.get_data()
    img = numpy_image[:,:,0:3]
    img = img[290:890, 670:1550,:]

    assert len(img.shape) == 3, 'Verificar que se reciba una imagen RGB' + \
                                f', se recibe {img.shape}'

    img = cv2.bitwise_and(img,img,mask=mask)

    return img, mask

def save_image(h_img, v_img, mask=None):
    try:
        cdt = str(datetime.now())
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        fn += ".jpg"
        fn2= fn
        #if mask is None: 
        fn1 = "v-" + fn
        imgpath = os.getcwd() + "/imagenes/vertical/" + fn1
        cv2.imwrite(imgpath, v_img)
        #else: #img with mask
        fn2 = "h-" + fn
        imgpath = os.getcwd() + "/imagenes/horizontal/" + fn2
        cv2.imwrite(imgpath, h_img)
        fnv= "v-mask-" + fn
        mn = fn.split(".jpg")[0] + "mask" + ".jpg"
        imgpath = os.getcwd() + "/imagenes/vertical/mask/" + fnv
        cv2.imwrite(imgpath, mask)
    except Exception as e:
        print(f"ERROR found when saving the image: {e}")

    return True

def save_image_v2(h_img, v_img, mask=None,agujero=0,calidad=0):
    try:
        cdt = str(datetime.now())
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        fn += "_ll_"
        fn= fn + "A" + str(agujero) + "_C" + str(calidad)  +".jpg"

        #if mask is None: 
        fn1 = "v-"+ fn
        imgpath = os.getcwd() + "/imagenes/vertical/" + fn1
        cv2.imwrite(imgpath, v_img)
        #else: #img with mask
        fn2 = "h-" + fn
        imgpath = os.getcwd() + "/imagenes/horizontal/" + fn2
        cv2.imwrite(imgpath, h_img)
        fnv= "v-mask-" + fn
        imgpath = os.getcwd() + "/imagenes/mask/" + fnv
        cv2.imwrite(imgpath, mask)
    except Exception as e:
        print(f"ERROR found when saving the image: {e}")

    return True


def run(agujero=0):
    global cam_h, cam_v
    #Camara horizontal
    if cam_h == None:
        #cam_h = init_h_cam()
        init_h_cam()
    # Capture an image
    ret, h_img = cam_h.read()
    print('imagen horizontal:',type(h_img))
    #save_image_h(h_img)
    
    # horizontal (x) axis prediction
    h_predictions, _ = call_yolo_predict("h", h_img)
    print('predicción horizontal', type(h_predictions))
    print(h_predictions[0].bbox) if not(h_predictions is None) else None
    print(h_predictions[0].mask) if not(h_predictions is None) else None
    # Print prediction info
    print_prediction_info(h_predictions, h_img, 'horizontal')

    #Camera vertical
    # Capture an imamge
    v_img, v_mask = init_and_capture_v_cam()
    print('imagen vertical:',type(v_img))
    #save_image_v(v_img)
    #save_image_MASK(v_mask)

    # vertical (z) axis prediction
    v_predictions, v_pmask = call_yolo_predict("v", v_img, v_mask)
    print('predicción vertical', type(v_predictions))
    print(v_predictions[0].bbox) if not(v_predictions is None) else None 
    print(v_predictions[0].mask) if not(h_predictions is None) else None
    
    # Print prediction info
    print_prediction_info(v_predictions, v_img, 'vertical')

    #Get type of seedling
    tos = get_type_of_seedling(h_predictions, v_predictions, v_pmask)
    # Save h and v images
    save_image_v2(h_img, v_img, v_mask, agujero, tos) 

    return tos

if __name__ == "__main__":
    run()
