# Change Log

## [1.0.1] 2024-07-11
## Add
- Stable version. Seedlinger working properly and generating logs for image and detection.

## [1.0.0] 2024-06-08
## Add
- First stable version of the Seedlinger Computer Vision Sytem running properly. Test *test_seedlinger_cvs.py* will run the main module to get the seedling classificacion prediction.
- Integration with the robot system through the MODBUS module *server_im_calidad.py* which is the main program to run to let the PLC gain access to the Seedlinger module. 
- Classificacion model working properly. Test *detectionClassification.py* will take corresponding images to predict the artichoke seedling quality class.
- Models for detecting seedling in the horizontal and vertical point of view workin properly. Test of horizontal detection *horizontalDetectionWithCamera*. Test of vertical detection *verticalDetectionWithCamera*. 
