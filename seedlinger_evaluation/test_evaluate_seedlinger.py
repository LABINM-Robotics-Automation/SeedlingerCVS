import os
import sys
import time
import unittest

import pandas as pd
from evaluate_seedlinger import *

class test_evaluate_seedlinger(unittest.TestCase):
    def test_get_number_of_trays(self):
        print("Test for get number of trays")
        res = get_number_of_trays()
        expected_res = 4

        self.assertEqual(res, expected_res)

    def test_apply_quality_threashold(self):
        print("Test for apply quality threashold")
        td_df = upload_tray_data(num_bandeja=-1)
        res = apply_quality_threashold(td_df).loc[0,"calidad_plantin"]
        expected_res = 3

        self.assertEqual(res, expected_res)

    def test_get_quality_predictions(self):
        print("Test get quality predictions")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        res = get_quality_predictions(td2_df).loc[0, "prediccion_calidad"]
        expected_res = 3

        self.assertEqual(res, expected_res)

    def test_get_prediction_evaluation(self):
        print("Test get prediction evaluation")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        td3_df = get_quality_predictions(td2_df)
        res = get_prediction_evaluation(td3_df, 0).loc[0, "evaluacion_prediccion"]
        expected_res = 1

        self.assertEqual(res, expected_res)

    def test_get_stats_4_eval_type_0(self):
        print("Test get stats")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        td3_df = get_quality_predictions(td2_df)
        td4_df = get_prediction_evaluation(td3_df, 0)
        res = get_stats(td4_df)
        expected_res = 63

        self.assertEqual(res[0], expected_res)

    def test_get_stats_4_eval_type_1(self):
        print("Test get stats")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        td3_df = get_quality_predictions(td2_df)
        td4_df = get_prediction_evaluation(td3_df, 1)
        res = get_stats(td4_df)
        expected_res = 163

        self.assertEqual(res[0], expected_res)

    def test_get_seedling_images_dataset(self):
        print("Test get seedling images dataset")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        td3_df = get_quality_predictions(td2_df)
        td4_df = get_prediction_evaluation(td3_df, 1)
        get_seedling_images_dataset(td4_df)
        fns = len([n for n in os.listdir('./dataset/2/horizontal')])
        if fns > 0:
            res = True
        else:
            res = False
        expected_res = True

        self.assertEqual(res, expected_res)


if __name__=="__main__":
    unittest.main()

