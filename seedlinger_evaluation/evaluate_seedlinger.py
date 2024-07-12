import os
import numpy as np
import pandas as pd

quality_threshold = 50 #mm

def get_number_of_trays():
    return len([name for name in os.listdir('./csv')])

def sort_array_to_1D(td_np):
    tr, tc = td_np.shape
    c = True
    ntd_lt = []
    for r in range(tr):
        if c:
            ntd_lt.extend(list(np.flip(td_np[r,:])))
        else:
            ntd_lt.extend(list(td_np[r, :]))
        c = not c

    #print(ntd_lt)

    return np.array(ntd_lt)


def upload_tray_data(num_bandeja):
    #with open("./csv/bandeja{num_bandeja}.csv", "r") as f:
    cols = ["num_bandeja", "idx", "longitud_hoja"] #, "calidad", "pred_calidad", "evaluacion"]
    #res = True

    if num_bandeja == -1:
        print("Get all the trays")
        td_df = pd.DataFrame(data=[], columns=cols)
        nuot = get_number_of_trays()
        for t in range(1, nuot + 1):
            td_np = np.genfromtxt(f"./csv/bandeja{t}.csv", delimiter=',')
            ntd_np = sort_array_to_1D(td_np)
            idx = ["A"+str(i) for i in range(1, ntd_np.shape[0]+1)]
            data = {
                'num_bandeja': t,
                'idx': idx,
                'longitud_hoja': ntd_np
            }
            ttd_df = pd.DataFrame(data=data, columns=cols)
            td_df = pd.concat([td_df, ttd_df], ignore_index=True)
    else:
        td_np = np.genfromtxt(f"./csv/bandeja{num_bandeja}.csv", delimiter=',')
        ntd_np = sort_array_to_1D(td_np)
        idx = ["A"+str(i) for i in range(1, ntd_np.shape[0]+1)]
        data = {
            'idx': idx,
            'longitud_hoja': ntd_np
        }
        td_df = pd.DataFrame(data=data, columns=cols)

    print(td_df)

    return td_df

def apply_quality_threashold(otd_df):
    td_df = otd_df.copy()
    td_df.loc[td_df['longitud_hoja'] > quality_threshold, 'calidad_plantin'] = 3
    td_df.loc[td_df['longitud_hoja'] < quality_threshold, 'calidad_plantin'] = 2
    #td_df["calidad_plantin"]= td_df["longitud_hoja"] - quality_threshold
    print(td_df)

    return td_df

def get_quality_predictions(otd_df):
    td_df = otd_df.copy()
    nuot = get_number_of_trays()
    for t in range(1, nuot+1):
        fns = [name for name in os.listdir(f'./images/horizontal/bandeja{t}')]
        for fn in fns:
            q = int(fn.split('_C')[1].split('.')[0])
            idx = "A" + fn.split('_A')[1].split('_')[0]
            td_df.loc[
                (td_df['num_bandeja'] == t) & (td_df['idx'] == idx),
                'prediccion_calidad'
            ] = q

    print(td_df)

    return td_df

def get_prediction_evaluation(otd_df, eval_type):
    td_df = otd_df.copy()
    td_df["pre_eval"] = td_df["calidad_plantin"] - td_df["prediccion_calidad"]
    if eval_type == 0: #two class evaluation: good & not good
        td_df.loc[
            (td_df["pre_eval"] == 0) & (td_df["prediccion_calidad"] > 1),
            "evaluacion_prediccion"
        ] = 1
        td_df.loc[
            (td_df["pre_eval"] != 0) & (td_df["prediccion_calidad"] > 1),
            "evaluacion_prediccion"
        ] = 0
        td_df.dropna(subset=["evaluacion_prediccion"], how="any", inplace=True)
        td_df = td_df.reset_index()
    elif eval_type == 1: #three class evaluation: no presence, good & not good
        td_df.loc[
            (td_df["pre_eval"] == 0) & (td_df["prediccion_calidad"] > 0),
            "evaluacion_prediccion"
        ] = 1
        td_df.loc[
            (td_df["pre_eval"] != 0) & (td_df["prediccion_calidad"] > 0),
            "evaluacion_prediccion"
        ] = 0
        #Ones in prediccion_calidad are predictions of no seedling presence
        td_df.loc[
            (td_df["prediccion_calidad"] == 1),
            "evaluacion_prediccion"
        ] = 1

    print(td_df)

    return td_df

def get_stats(td_df):
    tot_true = len(td_df[td_df['evaluacion_prediccion'] == 1])
    tot_false = len(td_df[td_df['evaluacion_prediccion'] == 0])
    true_p = tot_true/(tot_true + tot_false)
    false_p = tot_false/(tot_true + tot_false)

    print(f"Total aciertos: {tot_true}")
    print(f"Porcentaje de aciertos: {true_p}")
    print(f"Total fallidos: {tot_false}")
    print(f"Porcentaje de fallidos: {false_p}")

    return tot_true, tot_false, true_p, false_p

def get_seedling_images_dataset(td_df):
    nuot = get_number_of_trays()
    for pov in ["horizontal", "vertical"]:
        for t in range(1, nuot+1):
            fns = [name for name in os.listdir(f'./images/{pov}/bandeja{t}')]
            for fn in fns:
                idx = "A" + fn.split('_A')[1].split('_')[0]
                pq = int(fn.split('_C')[1].split('.')[0])
                q_df = td_df[(td_df["idx"] == idx) & (td_df["num_bandeja"] == t)].reset_index()
                q = int(q_df.loc[0, "calidad_plantin"])
                if pq > 1: #we do not want empty photos
                    cmd_str = f"cp ./images/{pov}/bandeja{t}/{fn} " + \
                              f"./dataset/{q}/{pov}/{fn}"
                    print(cmd_str)
                    os.popen(cmd_str)

if __name__=="__main__":
    print("############## running seedlinger evaluation ##############")
    td_df = upload_tray_data(num_bandeja=-1)
    td2_df = apply_quality_threashold(td_df)
    td3_df = get_quality_predictions(td2_df)
    print("Prediction evaluation for a two class-based prediction")
    print("3: Good, 2: Not good")
    td4_0df = get_prediction_evaluation(td3_df, 0)
    res = get_stats(td4_0df)

    print("Prediction evaluation for a three class-based prediction")
    print("1: No presence, 3: Good, 2: Not good")
    td4_1df = get_prediction_evaluation(td3_df, 1)
    res = get_stats(td4_1df)

    print("Generate dataset")
    fns = len([n for n in os.listdir('./dataset/2/horizontal')])
    if fns < 1:
        print("Generating...")
        get_seedling_images_dataset(td4_1df)
    else:
        print("Dataset not generated,  there're images previously generated.")
        print("Delete them and run again the script")
