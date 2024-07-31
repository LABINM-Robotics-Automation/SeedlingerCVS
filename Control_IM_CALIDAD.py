import time
from datetime import datetime

from multiprocessing.managers import ListProxy
import json
import csv

from src.entorno_MODBUS import Config_server_db_brazos
import seedlinger_cvs 

entorno=Config_server_db_brazos()
Variable_IR=entorno.Brazo1.Registro_input
Variable_HR=entorno.Brazo1.Registro_holding

LINE_CLEAR = '\x1b[2K'
LINE_UP_1 = '\033[1A'
LINE_UP_3 = '\033[3A'
LINE_UP_4 = '\033[4A'
LINE_DOWN_1 = '\033[1B'
LINE_DOWN_4 = '\033[4B'
LINE_RETURN='\r'
LINE_FORMWARE='\033[20C'


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
        #self.escribir_data()

    def create_file(self):
        hora=datetime.now()
        cdt = str(hora.strftime("%Y-%m-%d %H:%M:%S"))
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        fn= "LOGGER/Calidad_"+ fn+".csv"

        self.filename=fn
        print(f'Created Log File -> {self.filename}')

        with open(self.filename,'a') as file:
            self.file = csv.writer(file)
            self.file.writerow(['Tiempo','Agujero','calidad','Tiempo proceso'])          

    def create_new_file(self,path):
        hora=datetime.now()
        cdt = str(hora.strftime("%Y-%m-%d %H:%M:%S"))
        fn = cdt.replace(" ", "_")
        fn = fn.replace(":", "-")
        fn= path+"/Calidad_registrada_"+ fn+".csv"

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
        else:
            pass
            #print ("no data save")



class SIM_calidad:
    def __init__(self) -> None:
        self.agujero:int=99
        self.calidad:int=0
        self.altura:float=0
        self.angulo:float=0

        #self.t_0_0:datetime
        #self.t_0_1:datetime
        self.t_0_0:float=0.0
        self.t_0_1:float=0.0
        self.activation_time:datetime

        self.has_data:bool=False

        self.cuenta_c0:int=0
        self.cuenta_c1:int=0
        self.cuenta_c2:int=0
        self.cuenta_c3:int=0

class Variables_Control:
    class Status:
        def __init__(self) -> None:
            self.status_word:int=0

            self.verificador:bool   =False
            self.libre:bool         =False
            self.trabajando:bool    =False
            self.terminado:bool     =False
            self.falla:bool         =False

        def set_libre(self):
            if not self.falla:
                print("SET LIBRE")
                self.libre      =True
                self.trabajando =False
                self.terminado  =False
        def set_trabajando(self):
            if not self.falla:
                print("SET TRABAJANDO")
                self.libre      =False
                self.trabajando =True
                self.terminado  =False
        def set_terminado(self):
            if not self.falla:
                print("SET TERMINADO")
                self.libre      =False
                self.trabajando =False
                self.terminado  =True
        def set_fallo(self):
            print("SET FALLA")
            self.libre      =False
            self.trabajando =False
            self.terminado  =False
            self.falla      =True
        def caso_reset(self):
            print("SET RESET")
            self.libre      =False
            self.trabajando =False
            self.terminado  =False
            self.falla      =False

    class Control:
        def __init__(self) -> None:
            self.control_word:int=0

            self.iniciar_calidad:bool=False
            self.reset:bool=False
            self.actualizar_id:bool=False
    class Falla_code:
        def __init__(self) -> None:
            self.falla_word:int=0
            self.err_no_data:bool=False
        
        def reset_falla(self):
            self.err_no_data=False

    def __init__(self) -> None:
        self.estado =self.Status()
        self.control=self.Control()
        self.fallo  =self.Falla_code()

        self.id_bandeja:int=0

        self.flag_calculado:bool=False
        self.flag_procesando:bool=False
        self.flag_actualizar:bool=False

    def update_status_WORD(self):
        self.estado.verificador=True
        b0=self.estado.verificador
        b1=self.estado.libre
        b2=self.estado.trabajando
        b3=self.estado.terminado
        b4=self.estado.falla
        b5=False
        b6=False
        b7=False
        b8=False
        b9=False
        b10=False
        b11=False
        b12=False
        b13=False
        b14=False
        b15=False

        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]

        self.estado.status_word=self.convert_bool_array_to__word(array_bool)

    def update_fallo_WORD(self):
        b0=self.fallo.err_no_data
        b1=False
        b2=False
        b3=False
        b4=False
        b5=False
        b6=False
        b7=False
        b8=False
        b9=False
        b10=False
        b11=False
        b12=False
        b13=False
        b14=False
        b15=False

        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]

        self.fallo.falla_word=self.convert_bool_array_to__word(array_bool)

    def caso_reset(self):
        if self.control.reset:
            self.estado.set_libre()
            self.fallo.reset_falla()
            self.flag_calculado=False
            self.flag_procesando=False

    def update_control(self,control_word:int):
        self.control.control_word=control_word
        b_array=self.convert_word_to_bool_array(control_word)
        self.control.iniciar_calidad=   b_array[1]
        self.control.reset=             b_array[2]
        self.control.actualizar_id=     b_array[3]

        #print(self.control.control_word)

    def convert_word_to_bool_array(self,word:int):
        b0  =bool(word&1)
        b1  =bool(word&2)
        b2  =bool(word&4)
        b3  =bool(word&8)
        b4  =bool(word&16)
        b5  =bool(word&32)
        b6  =bool(word&64)
        b7  =bool(word&128)
        b8  =bool(word&256)
        b9  =bool(word&512)
        b10 =bool(word&1024)
        b11 =bool(word&2048)
        b12 =bool(word&4096)
        b13 =bool(word&8192)
        b14 =bool(word&16384)
        b15 =bool(word&32768)
        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]
        #print(f"CONTROL ARRAY:{array_bool}")
        return array_bool

    def convert_bool_array_to__word(self,array_bool:list):
        mult=[1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768]
        bit=array_bool
        data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for i in range(len(bit)):
            data[i]=mult[i]*bit[i]
        w0=sum(data)

        #print(f"STATUS WORD:{w0}")
        return w0

varaible=Variables_Control()
proc_cal=SIM_calidad()
guardar_inforamcion=Almacenar_data()

def update_bandeja_id():
    if varaible.control.actualizar_id:
        if not varaible.flag_actualizar:
            varaible.id_bandeja=Variable_HR.id_bandeja

            Variable_IR.id_bandeja=varaible.id_bandeja

            varaible.flag_actualizar=True
    else:
        varaible.flag_actualizar=False

def contador_calidad(calidad):
    if calidad==0:
        proc_cal.cuenta_c0+=1
    elif calidad==1:
        proc_cal.cuenta_c1+=1
    elif calidad==2:
        proc_cal.cuenta_c2+=1
    elif calidad==3:
        proc_cal.cuenta_c3+=1

def proceso_calidad(vision:seedlinger_cvs.calidad):
    plantin=Variable_HR.ind_agujero+1
    if varaible.estado.terminado and not varaible.control.iniciar_calidad:
        varaible.estado.set_libre()
        varaible.flag_procesando=False
        varaible.flag_calculado=False

        
    if varaible.flag_calculado and varaible.estado.trabajando:
        print("calculando")
        plantin=Variable_HR.ind_agujero+1
        # TODO: here it comes the seedlinger computer vision system
        try:
            #calidad = seedlinger_cvs.run(agujero=Variable_HR.ind_agujero+1) 
            calidad = vision.run(agujero=plantin)
        except Exception as error:
            calidad = 0
            import sys
            print("IMAGEN An error occurred:", sys.exc_info()[0])

            print("PROBLEMA IMAGEN, AVISAR ERICK: ",error)
            
        contador_calidad(calidad)

        #calidad=3   #fuerza a que haga recojo

        proc_cal.calidad = calidad #random.randint(1, 3)

        #proc_cal.altura=random.uniform(-10, 10)
        #proc_cal.angulo=random.uniform(-180, 180)

        proc_cal.altura=0
        proc_cal.angulo=0
        
        proc_cal.agujero=Variable_HR.ind_agujero
        varaible.flag_calculado=False
        proc_cal.has_data=True

    if varaible.flag_procesando and not varaible.flag_calculado:
        #proc_cal.t_0_1=datetime.now()
        proc_cal.t_0_1=time.time()
        time_Delta=proc_cal.t_0_1 - proc_cal.t_0_0
        print("/"*80)
        print("Agujero:{}".format(Variable_HR.ind_agujero+1))
        print("time total:{:0.3f}".format(time_Delta))
        print("Cuenta:")
        print(f"C0={proc_cal.cuenta_c0}\tC1={proc_cal.cuenta_c1}\tC2={proc_cal.cuenta_c2}\tC3={proc_cal.cuenta_c3}")
        print("/"*80)
        
        guardar_inforamcion.agujero=Variable_HR.ind_agujero+1
        guardar_inforamcion.calidad=proc_cal.calidad
        guardar_inforamcion.tiempo=proc_cal.activation_time
        guardar_inforamcion.tiempo_proceso=time_Delta
        guardar_inforamcion.bandejaID=Variable_HR.id_bandeja
        guardar_inforamcion.is_save=True


        if varaible.estado.trabajando:
            #print(f"termino ya: {time_Delta.microseconds}")
            varaible.estado.set_terminado()

            varaible.flag_procesando=False
            guardar_inforamcion.escribir_data()

            if plantin ==72:
                vision.carpetas.crearpath(vision.carpetas.bandeja+1)
                guardar_inforamcion.create_new_file(vision.carpetas.path_logger)
    
    if varaible.control.iniciar_calidad and not varaible.control.reset and varaible.estado.libre:
        print ("inicio")
        varaible.estado.set_trabajando()
        varaible.flag_calculado=True
        varaible.flag_procesando=True
        proc_cal.has_data=False
        #proc_cal.t_0_0=datetime.now()
        proc_cal.t_0_0=time.time()
        proc_cal.activation_time=datetime.now()
    
def reset_estado():
    if varaible.control.reset:
        varaible.caso_reset()

def main(list_ir:ListProxy,list_hr:ListProxy,debug=False):
    print("control_br activo")
    data_cero=(0,0,0)

    Variable_HR.update_variables2(data_cero)
    varaible.estado.set_libre()

    vision=seedlinger_cvs.calidad()
    vision.carpetas.crearpath(1)
    guardar_inforamcion.create_new_file(vision.carpetas.path_logger)
    
    #list_ir=Variable_IR.update_list_data()

    while True:
        try:
            #start = datetime.now()
            
            ###Lectura de registro HR
            
            data_hr=list_hr[0]
            Variable_HR.update_variables2(tuple(data_hr))
            
            ###Interpretacion de registro CONTROL de HR
            varaible.update_control(Variable_HR.control)
            
            ### Codigo aqui

            update_bandeja_id()

            proceso_calidad(vision)

            
            reset_estado()           
            
            
            ###Escritura de registro STATUS del IR
            varaible.update_status_WORD()
            varaible.update_fallo_WORD()

            if not varaible.flag_procesando:

                Variable_IR.agujero=proc_cal.agujero
                Variable_IR.calidad=proc_cal.calidad
                Variable_IR.cal_altura=proc_cal.altura
                Variable_IR.cal_angulo=proc_cal.angulo

            Variable_IR.status=varaible.estado.status_word
            Variable_IR.falla=varaible.fallo.falla_word

            ###Escritura de registro IR
            data=Variable_IR.update_list_data()
            list_ir[0]=data


            ###SAVE DATA
            #guardar_inforamcion.escribir_data()

            ###debug###

            if debug:
                print(f"Data control IR:{list_ir[0]}")
                print(f"Data control HR:{data_hr}")

            time.sleep(0.02)
            if debug:
                print(LINE_UP_1,end=LINE_CLEAR)
                print(LINE_UP_1,end=LINE_CLEAR)

        except KeyboardInterrupt:
            print("Control interrumpido")
            break

        except Exception as error:
            print("Control fallo: ",type(error).__name__)
            break

        #end = datetime.now()
        #time_taken = end - start
        #print('Time: ',time_taken)