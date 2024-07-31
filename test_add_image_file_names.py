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

    def test_add_image_file_names(self):
        print("Test add image file names")
        td_df = upload_tray_data(num_bandeja=-1)
        td2_df = apply_quality_threashold(td_df)
        res = add_image_file_names(td2_df).loc[0, "h_filename"]
        expected_res = "h-2024-07-04_15-57-41.134221_ll_A1_C3.jpg"

        self.assertEqual(res, expected_res)


if __name__=="__main__":
    unittest.main()

