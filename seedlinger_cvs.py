import os
import sys
import time
import random
import warnings
from datetime import datetime
import csv

import cv2
import numpy as np
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
linear = ""
h_wpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/' + \
          'seedlingnet/modules/detectors/weights/240723/hseed.pt'

v_wpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/' + \
          'seedlingnet/modules/detectors/weights/240723/vseed.pt'

dpath = '/home/robot/seedlinger/SeedlingerCVS/seedling_classifier/' + \
        '/seedlingnet/modules/detectors/weights/opt.yaml'

lmp = '/seedling_classifier/seedlingnet/modules/' + \
      'classifiers/weights/240723/classifier.pt'

CLASSIFIER_WEIGHTS = os.getcwd() + lmp

HORIZONTAL_DELIMITER = 240
VERTICAL_DELIMITER = 330

class Almacenar_data:
    def __init__(self) -> None:
        self.bandejaID:int=0
        self.agujero:int=9999
        self.calidad:int=0
        self.tiempo:datetime=datetime.now()
        self.tiempo_proceso:float=0
        self.filename:str
        self.is_save:bool=False
        self.create_file()
        self.escribir_data()

    def create_file(self):
        cdt = str(datetime.now())
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        fn= "LOGGER/Calidad_"+ fn+".csv"

        self.filename=fn
        print(f'Created Log File -> {self.filename}')

        with open(self.filename,'a') as file:
            self.file = csv.writer(file)
            self.file.writerow(['Tiempo','Agujero','calidad','Tiempo proceso'])           
        
    
    def escribir_data(self):
        if self.is_save:
            with open(self.filename,'a') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow([self.tiempo,self.agujero,self.calidad,self.tiempo_proceso])
            
            print("Linea: {},{},{},{}".format(self.tiempo,self.agujero,self.calidad,self.tiempo_proceso))
            self.is_save=False


class carpetas:
    def __init__(self) -> None:
        hora=datetime.now()
        cdt = str(hora.strftime("%Y-%m-%d %H:%M:%S"))
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        self.path= os.getcwd()+"/imagenes/"+ fn
        self.bandeja=1


    def crearpath(self,bandeja:int):
        self.bandeja=bandeja
        self.path_vertical      =self.path+"/"+str(bandeja)+"/vertical"
        self.path_horizontal    =self.path+"/"+str(bandeja)+"/horizontal"
        self.path_mask          =self.path+"/"+str(bandeja)+"/mask"
        self.path_proc_vertical     =self.path+"/"+str(bandeja)+"/procesadas/vertical"
        self.path_proc_horizontal   =self.path+"/"+str(bandeja)+"/procesadas/horizontal"
        self.path_logger            =self.path+"/"+str(bandeja)
        os.makedirs(self.path_vertical,exist_ok=True)
        os.makedirs(self.path_horizontal,exist_ok=True)
        os.makedirs(self.path_mask,exist_ok=True)
        os.makedirs(self.path_proc_vertical,exist_ok=True)
        os.makedirs(self.path_proc_horizontal,exist_ok=True)
        

class calidad:
    def __init__(self) -> None:
        self.carpetas=carpetas()
        self.cam_h=cv2.VideoCapture(0)
        self.cam_h_ok=False
        self.init_horizontal()
        self.cam_v=sl.Camera()
        self.cam_v_ok=False
        self.init_vertical()

    def init_horizontal(self):
        #Instantiate the camera object  
        while True:
            try:
                time.sleep(1)
                #Warming up the camera, sort of
                for i in range(5):
                    self.cam_h.read()
                # Check if the camera opened successfully
                if not self.cam_h.isOpened():
                    raise Exception("Error: Unable to open X-axis camera.") 
                break
            except Exception as e:
                # Optionally handle the exception in some way, like logging
                print(f"An error occurred during openning camera: {e}")
        self.cam_h_ok=True

    def h_cam_capture_img(self):
        for i in range(5):
            ret, frame = self.cam_h.read()
        return frame

    def init_vertical(self):
        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD1080
        init_params.camera_fps = 30
        init_params.depth_mode = sl.DEPTH_MODE.NEURAL
        init_params.coordinate_units = sl.UNIT.METER
        init_params.depth_minimum_distance = 0.4
        init_params.depth_maximum_distance = 0.8
        init_params.camera_image_flip = sl.FLIP_MODE.AUTO
        init_params.depth_stabilization = 1 
        self.runtime_params = sl.RuntimeParameters(
            confidence_threshold=50,
            enable_fill_mode=True,
            texture_confidence_threshold=200
        )
        err = self.cam_v.open(init_params)
        
        if err != sl.ERROR_CODE.SUCCESS:
            print(err)
            sys.exit()

        assert self.cam_v.grab(self.runtime_params) == sl.ERROR_CODE.SUCCESS, \
        'La cámara Zed no esta ejecutandose correctamente,' + \
        'verificar su conexion'
        self.cam_v_ok=True
        
    def v_cam_capture_img(self):
        depth_map = sl.Mat()
        image = sl.Mat()

        assert self.cam_v.grab(self.runtime_params) == sl.ERROR_CODE.SUCCESS, \
        'La cámara Zed no esta ejecutandose correctamente,' + \
        'verificar su conexion'

        self.cam_v.retrieve_image(depth_map, sl.VIEW.DEPTH)
        self.cam_v.retrieve_image(image, sl.VIEW.LEFT)

        threshold_value = 130
        numpy_depth_map = depth_map.get_data()
        gray = cv2.cvtColor(numpy_depth_map[:,:,0:3], cv2.COLOR_BGR2GRAY)
        gray = gray[290:890, 670:1550]
        _, mask = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
        assert len(mask.shape) == 2, 'Verificar que se reciba una mascara' + \
                                    f'se recibe {mask.shape}'

        numpy_image = image.get_data()
        img = numpy_image[:,:,0:3]
        img = img[290:890, 670:1550,:]

        assert len(img.shape) == 3, 'Verificar que se reciba una imagen RGB' + \
                                    f', se recibe {img.shape}'

        img = cv2.bitwise_and(img,img,mask=mask)

        return img, mask

    def _call_yolo_predict(self,axis, img, mask=None):
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
            predictions = h_detector.predict(img, threshold=0.3)

            if predictions is not None:
                correct_predictions = []
                for pred in predictions:
                    x1, y1, x2, y2 = pred.bbox
                    if (y1) > 230: continue
                    if (y2) > 315: continue
                    correct_predictions.append(pred)
                predictions = correct_predictions
                if len(predictions) == 0:
                    predictions = None
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
                if pl == 0:
                    predictions = None
            else:
                v_pmask = np.zeros(img.shape, dtype = np.uint8)
        else:
            raise Exception("Invalid axis inserted")

        print(f"Prediction result: {predictions}")
        return predictions, v_pmask

    def _get_type_of_seedling(self,hp, vp, vm):
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

    def print_prediction_info(self,predictions, img, top):
        cv2.line(img, (10, HORIZONTAL_DELIMITER), (300, HORIZONTAL_DELIMITER),
                 (0, 255, 0), thickness=2)
        cv2.line(img, (10, VERTICAL_DELIMITER), (300, VERTICAL_DELIMITER),
                 (0, 255, 0), thickness=2)

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
                cv2.rectangle(img, (int(x), int(y)),
                              (int(w), int(h)), (0,255,0), 2)

        img_s=self.ResizeWithAspectRatio(img,width=480)
        cv2.imshow("Image_{}".format(top),img_s)
        cv2.waitKey(150)

    def print_prediction_info_VERTICAL(self,predictions, img, mask, top):
        cv2.line(img, (10, HORIZONTAL_DELIMITER), (300, HORIZONTAL_DELIMITER),
                 (0, 255, 0), thickness=2)
        cv2.line(img, (10, VERTICAL_DELIMITER), (300, VERTICAL_DELIMITER),
                 (0, 255, 0), thickness=2)

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

        img_s=self.ResizeWithAspectRatio(img,width=480)
        mask_s=self.ResizeWithAspectRatio(mask,width=480)

        cv2.imshow("Image_vertical_mask",mask_s)
        cv2.waitKey(100)
        cv2.imshow("Image_vertical",img_s)
        cv2.waitKey(100)

    def _save_image(self,h_img, v_img, mask=None,agujero=0,calidad=0):
        try:
            hora=datetime.now()
            cdt = str(hora.strftime("%Y-%m-%d %H:%M:%S"))
            fn = cdt.replace(" ", "_")
            fn = fn.replace(":", "-")
            fn += "_ll_"
            fn= fn + "A" + str(agujero) + "_C" + str(calidad)  +".jpg"
            fn1 = "v-"+ fn
            
            #imgpath = os.getcwd() + "/imagenes/vertical/" + fn1
            imgpath = self.carpetas.path_vertical + "/" + fn1
            cv2.imwrite(imgpath, v_img)
            fn2 = "h-" + fn
            #imgpath = os.getcwd() + "/imagenes/horizontal/" + fn2
            imgpath = self.carpetas.path_horizontal + "/" + fn2
            cv2.imwrite(imgpath, h_img)
            fn3= "v-mask-" + fn
           # imgpath = os.getcwd() + "/imagenes/mask/" + fn3
            imgpath = self.carpetas.path_mask + "/" + fn3
            cv2.imwrite(imgpath, mask)
        except Exception as e:
            print(f"ERROR found when saving the image: {e}")

        return True

    def _save_image_proc(self,h_img, v_img,agujero=0,calidad=0):
        try:
            hora=datetime.now()
            cdt = str(hora.strftime("%Y-%m-%d %H:%M:%S"))
            fn = cdt.replace(" ", "_")
            fn = fn.replace(":", "-")
            fn += "_ll_"
            fn= fn + "A" + str(agujero) + "_C" + str(calidad)  +".jpg"
            fn1 = "v-"+ fn
            #imgpath = os.getcwd() + "/imagenes/procesadas/vertical/" + fn1
            imgpath = self.carpetas.path_proc_vertical + "/" + fn1
            cv2.imwrite(imgpath, v_img)
            fn2 = "h-" + fn
            #imgpath = os.getcwd() + "/imagenes/procesadas/horizontal/" + fn2
            imgpath = self.carpetas.path_proc_horizontal + "/" + fn2
            cv2.imwrite(imgpath, h_img)
        except Exception as e:
            print(f"ERROR found when saving the image: {e}")

        return True

    def ResizeWithAspectRatio(self,image, width=None, height=None, inter=cv2.INTER_AREA):
        dim = None
        h = image.shape[0]
        w = image.shape[1]

        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))

        return cv2.resize(image, dim, interpolation=inter)

    def run(self, agujero=0):
        #Camara horizontal
        # Capture an image
        h_img=self.h_cam_capture_img()
        s_h_img = h_img.copy() #para asegurar que la imagen guardada no tenga recuadros

        # horizontal (x) axis prediction
        h_predictions, _ = self._call_yolo_predict("h", h_img)

        # Print prediction info
        self.print_prediction_info(h_predictions, h_img, 'horizontal')

        #Camera vertical
        # Capture an imamge
        v_img, v_mask =self.v_cam_capture_img()
        s_v_img = v_img.copy() #para asegurar que la imagen guardada no tenga recuadros

        # vertical (z) axis prediction
        v_predictions, v_pmask = self._call_yolo_predict("v", v_img, v_mask)

        # Print prediction info
        self.print_prediction_info_VERTICAL(v_predictions,v_img, v_mask, 'vertical')

        #Get type of seedling
        tos = self._get_type_of_seedling(h_predictions, v_predictions, v_pmask)

        # Save h and v images
        self._save_image_proc(h_img, v_img, agujero, tos)
        self._save_image(s_h_img, s_v_img, v_mask, agujero, tos) 

        return tos


if __name__ == "__main__":
    carpe=carpetas()