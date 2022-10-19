from tkinter import*
from tkinter import messagebox, filedialog, ttk
import pandas as pd
from pandastable import Table, TableModel
import sys
import ezdxf
from ezdxf import recover
from ezdxf.math.construct2d import is_point_in_polygon_2d, Vec2
import xlrd
import math
import re


# raiz=Tk() #ventana almacenada en variable raiz

# #---> INICIO solucion problema color de celdas treeview encontrado en https://stackoverflow.com/questions/56628850/how-to-configure-ttk-treeview-item-color-in-python-3-7-3

# ##


# #from os import name as OS_Name
# ##if raiz.getvar('tk_patchLevel')=='8.6.9': #and OS_Name=='nt':
# ##    def fixed_map(option):
# ##        # Fix for setting text colour for Tkinter 8.6.9
# ##        # From: https://core.tcl.tk/tk/info/509cafafae
# ##        #
# ##        # Returns the style map for 'option' with any styles starting with
# ##        # ('!disabled', '!selected', ...) filtered out.
# ##        #
# ##        # style.map() returns an empty list for missing options, so this
# ##        # should be future-safe.
# ##        return [elm for elm in s.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]
# ##    s.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))
# ##

# #---> FIN solucion problema color celdas treeview

# raiz.geometry("900x700")
# raiz.resizable(width=False, height=False)

# raiz.title('Validador DXF')


# marco1 = Frame(raiz)
# marco1.config(bg="white",width="850",height="20")
# marco1.grid(padx=25, pady=1, row = 1, column=0)


# marco2 =LabelFrame(raiz,text='Validacion')
# marco2.grid(padx=25, pady=1, row = 0, column=0)
# marco2.config(bg="white",width="850",height="580")


# tv = ttk.Treeview(marco2, height=27)
# tv['columns']=("Nº","Validacion")
# tv.column("#0", width="0", stretch="NO")
# tv.column("Validacion",anchor="w", width="820")
# tv.column("Nº",anchor="w", width="20")
# #tv.column('Ver mas', anchor="w", width="50")
# #tv.heading("#0", text="Validación", anchor="w",)
# tv.heading("Validacion",text="Validación",anchor="w")
# tv.heading("Nº",text="Nº",anchor="w")
# #tv.heading("Ver mas",text="Ver Más",anchor="w")
# #tv.column("#0",text"Validación"stretch=True, width="850")



# #--- Abre DXF con explorador de windows y lo guarda en la variable DOC ---#

global botonProcesar
botonProcesar = document.getElementById('procesarArchivo')
botonProcesar.addEventListener("click",Procesar_Archivo())


def Abrir_Archivo():
    global doc
    global validaciones
    global validaciones2
    try:
        doc, auditor = recover.readfile(filedialog.askopenfilename(title="abrir", initialdir="C:/"))


    except IOError:
        sys.exit(1)

    except ezdxf.DXFStructureError:
        print(messagebox.showerror(message="El archivo selecciondo no es un archivo DXF o el mismo esta corrupto", title="Error"))
        sys.exit(2)

# DXF file can still have unrecoverable errors, but this is maybe just
# a problem when saving the recovered DXF file.
    if auditor.has_errors:
        auditor.print_error_report()
        print(doc)
        print(Archivo)
        validaciones = pd.DataFrame()
    validaciones2 = pd.DataFrame()
    validaciones = pd.read_excel('config_validaciones.xls') #data frame con archivo de Configuración de validaciones xls
    validaciones2 = validaciones.drop(['Validacion','Descripcion','Observaciones',],axis='columns') #borra columnas innecesarias del data frame validaciones
    del(validaciones)

    
def Procesar_Archivo():

    global tv
    global layouts
    global lados_parcelas_l
    global validaciones
    global validaciones2
    global resumen
    global colores
    colores = pd.read_csv('colores.csv')

    global sup_parc_poly #superficie de parcelas
    global sup_ces_poly #superficie de cesión
    global sup_mens_poly #superficie de mensura calculada como la suma de parcelas y cesiones
    global parcelas_poly_close #parcelas polilineas cerradas
    global lados_parcelas_l #ladoas de parcela
    global excedentes_poly #poligonos de excedente polilinea
    global mejoras_poly #poligonos de mejoras polilinea
    global cesion_poly #poligonos de cesiones polilinea
    global bloque_caratula #caratulas insertas
    global bloque_car_model #caratulas insertas en el model

    sup_parc_poly = 0
    sup_ces_poly = 0
    sup_mens_poly = 0


    lados_parcelas_l = list()
    model = doc.modelspace() #inserta el model espace en la variable model
    layouts = doc.layout_names()
    layouts.remove('Model') # crea una lista con los nombres de los layouts borrando el nombre dle model
    print (layouts) #imprime los layouts

    for i in tv.get_children():
        tv.delete(i)
    
    chequeo_archivo()
    chequeo_layers()
    chequeo_bloques()
    chequeo_model()
    chequeo_caratula()
    chequeo_cotas()
    chequeo_layout()

    tv.tag_configure(tagname="error",background = "#FEA9A9")
    tv.tag_configure(tagname="ok",background = "#ADFEA9")
    tv.tag_configure(tagname='NaN',background = "light grey")
    
    for i in range (0,len(validaciones2)):
        if  validaciones2.loc[i,'Resultado']== 0:
            tv.insert('',END,values=(i,validaciones2.loc[i,'Observacion']),tags=["ok",])

        elif validaciones2.loc[i,'Resultado'] <0:
            tv.insert('',END,values=(i,validaciones2.loc[i,'Observacion']),tags=["error",])

        else:
            tv.insert('',END,values=(i,validaciones2.loc[i,'Observacion']),tags=["NaN",])

        #tv.insert('',END,text=(validaciones2.loc[i,'Observacion']),

    tv.pack(fill="both", expand=True)



        

Boton_abrir= Button(marco1, text="Abrir archivo", command=Abrir_Archivo).pack()


#--- Abre DXF con explorador de windows y lo guarda en la variable DOC ---#

#--- 2 INICIO Validación del Archivo DXF ---#

#--- 2.1 INICIO  Validación de versión de archivo --#

def chequeo_archivo():

    global doc
    global validaciones2
    global tv
    
    version_arch = doc.header['$ACADVER']
    version_num = int(version_arch.replace("AC",""))
    version_no = ['AC1009','AC1012','AC1014','AC1015']
    print (version_num)

    if (version_num >= 1032) or (version_num <= 1015):
        validaciones2.loc[0,'Resultado']=-1
        validaciones2.loc[0,'Observacion']='Error: Las Versiones de DXF admitidas son 2004, 2007, 2010 y 2013'
    else:
        validaciones2.loc[0,'Resultado']=0
        validaciones2.loc[0,'Observacion']='OK: Versión de Archivo DXF correcta'
        

#--- 2.1 FIN  Validación de versión de archivo --#
    
#--- 2.1 INICIO  Validación de layers --#
def chequeo_layers():

    global doc
    global validaciones2
    global tv
    
    #inicio Carga Info de layers de archivo y de plantilla
    Layers_DXF = pd.DataFrame() #crea data frame para almacenar los layers del archivo con su configuración
    nombre_layers,color_layers,linea_layers, grosor_layers = list(), list(), list(), list() #crea listas que tendran datos de los layers del dxf y pasaran al data frame

    for layer in doc.layers:                 ##-- Guarda la configuración de los layers en listas
        nombre_layers.append(layer.dxf.name) ##-- guarda nombre de los layers en una lista
        color_layers.append(layer.dxf.color) ##-- guarda nombre de los layers en una lista
        linea_layers.append(layer.dxf.linetype) ##-- guarda nombre de los layers en una lista
        grosor_layers.append(layer.dxf.lineweight) ##-- guarda nombre de los layers en una lista

    Layers_DXF = pd.DataFrame(list(zip(nombre_layers,color_layers,linea_layers, grosor_layers)), columns = ['Nombre','Color','Tipo_Linea','Grosor_Linea']) #arma data frame con los layers y su configuracion
    Layers_DXF = Layers_DXF.sort_values('Nombre', ascending=True) #ordena la tabla de layers del DXF en forma ascdenete para poder comparar con la de la plantilla
    Layers_DXF.reset_index(inplace=True, drop=True) #resetea el indice de la tabla ordenada para poder comparar con la de la plantilla
    plantilla_2 = pd.read_csv('Config_Layers.csv') #data frame con archivo de ocnfiguración de layers csv
    del  nombre_layers,color_layers,linea_layers, grosor_layers ##-- Borra las listas de layers que ya no se usan

    layer_count_DXF = len(doc.layers) ##-- Cuenta el total de layers del archivo DXF
    layer_count_plantilla = len(plantilla_2) ##-- Cuenta el total de layers del archivo DXF

    nom_layers_dxf = Layers_DXF["Nombre"].tolist()
    nom_layers_plant = plantilla_2["Nombre"].tolist()
    band_dxf_plant = list()

    
    #FIN Carga Info de layers de archivo y de plantilla

    #Inicio Validar Layers


##    if layer_count_DXF < layer_count_plantilla:
##        validaciones2.loc[1,'Resultado']=-1
##        validaciones2.loc[1,'Observacion']='Error: Faltan Layers de la plantilla'
##        validaciones2.loc[2,'Resultado']=-1
##        validaciones2.loc[2,'Observacion']='Error: Configuración de layers incorrecta'
##
##    else:
    for layer in nom_layers_plant:
        if layer in nom_layers_dxf:
            band_dxf_plant.append('0')
        else:
            band_dxf_plant.append('-1')

    if '-1' in band_dxf_plant:
        validaciones2.loc[1,'Resultado']=-1
        validaciones2.loc[1,'Observacion']='Error: Faltan Layers de la plantilla'

    else:
        if len(nom_layers_dxf)==len(nom_layers_plant):
            validaciones2.loc[1,'Resultado']=0
            validaciones2.loc[1,'Observacion']='OK: Se han detectado todos los layers de la palantilla en el archivo DXF'
        else:
            validaciones2.loc[1,'Resultado']=-1
            validaciones2.loc[1,'Observacion']='Error: Existen más Layers en el archivo dxf que los admitidos en la plantilla'
                
            
#--- 2.1 FIN Validación de layers --#
            

#--- 2.2 INICIO Validación de bloques --#

def chequeo_bloques ():
    global doc
    nombre_bloque = list()
    global validaciones2

    for block in doc.blocks:                 ##-- Guarda información de los bloques en una lista
            nombre_bloque.append(block.dxf.name) ##-- guarda nombre de los bloques en una lista
    elim_bloque=list()

    for i in range (0,len(nombre_bloque)):      # Elimina los elementos que no son bloques del dxf y correconden al layout, model, etc.
       if '*' in nombre_bloque[i]:
            elim_bloque.append(nombre_bloque[i]) 

    for i in range (0,len(elim_bloque)):
        nombre_bloque.remove(elim_bloque[i])

    Plant_Bloques = pd.read_csv('Config_Bloques.csv') #data frame con archivo de configuración de bloques csv
    Bloques_DXF = pd.DataFrame(list(zip(nombre_bloque)), columns = ['Nombre']) #,'Color','Tipo_Linea','Grosor_Linea'])

    Bloques_DXF_count = len(Bloques_DXF)
    Plant_Bloques_count = len(Plant_Bloques)

    band_bloque_nombre = list()

##    if Bloques_DXF_count >  Plant_Bloques_count : #evalua si la cantidad de bloques configurados en el dibujo son mayores a los de las plantillas
##        validaciones2.loc[3,'Resultado']=-2
##        validaciones2.loc[3,'Observacion']='Error: Existen mas Bloqes que los admitidos por la plantilla'
##        validaciones2.loc[3,'Cetegoría']='Bloques'
##
##        validaciones2.loc[4,'Resultado']=-2
##        validaciones2.loc[4,'Observacion']='Error: Configuración de Bloques incorrecta'
##


    for bloque in Bloques_DXF:
        if bloque in Plant_Bloques:
            band_bloque_nombre.append('0')
        else:
            band_bloque_nombre.append('-1')

    if '-1' in band_bloque_nombre:
        validaciones2.loc[2,'Resultado']=-1
        validaciones2.loc[2,'Observacion']='Error: '
        validaciones2.loc[2,'Cetegoría']='Bloques'

    else:
        
        if Bloques_DXF_count==Plant_Bloques_count:
            validaciones2.loc[2,'Resultado']=0
            validaciones2.loc[2,'Observacion']='OK: Se han detectado todos los Bloques de la palantilla en el archivo DXF'
        else:
            validaciones2.loc[2,'Resultado']=-1
            validaciones2.loc[2,'Observacion']='Error: Existen más Bloques en el archivo dxf que los admitidos en la plantilla'


##        if Bloques_DXF.equals(Plant_Bloques): #evalua si la configuración de bloques en el dibujo es igual a la de las plantilla
##            validaciones2.loc[4,'Resultado']=0
##            validaciones2.loc[4,'Observacion']='OK: Configuración de Bloques correcta'
##            validaciones2.loc[4,'Cetegoría']='Bloques'
##        else:
##            validaciones2.loc[4,'Resultado']=-1
##            validaciones2.loc[4,'Observacion']='Error: Configuración de Bloques incorrecta'
##            validaciones2.loc[4,'Cetegoría']='Bloques'


    #------>

#--- 2.2 FIN Validación de bloques --#


layer_caratula_1="01-P-PLANO-CARATULA"
layer_cotas_parc_1="03-P-MEDIDAS-PARCELA"



#--- 2.4 INICIO Validación de elementos de Layout --#
    


    #--- 2.4.3 INICIO Validación de Cotas --#

def chequeo_cotas():
    global layer_cotas_parc_1
    cotas= doc.query('DIMENSION')
    cotas_parc= doc.query('DIMENSION[layer=="03-P-MEDIDAS-PARCELA"]')

    band_cparc_model = list()
    band_cpol_model = list()
    band_cparc_med = list()
    band_cpol_med = list()
    band_cota_lineal = list()
    band_parc_arc = list()
    global lados_parcelas_l
    global validaciones2

    global parcelas_poly_close


    lados_parcelas=0
    print("cotas parc")
    print(len(cotas_parc))
    
    cotas_parc_lado = list()
    cotas_parc_ang = list()

    for parcela in parcelas_poly_close:
        if parcela.has_arc:
            band_parc_arc.append("1")
        else:
            band_parc_arc.append("0")
    

    if len (cotas)>0:

        #verifica que tipo de acotaciones se utilizo para la parcela 162 = angular, 32 = lineal, 33 = alineado, 
        for cota in cotas_parc:

            print("cota dimtype")
            print(cota.dxf.dimtype)

            if cota.dxf.dimtype == 162:
                cotas_parc_ang.append(cota)

            elif (cota.dxf.dimtype == 33) or (cota.dxf.dimtype == 8):
                cotas_parc_lado.append(cota)

            elif (cota.dxf.dimtype ==32):
                band_cota_lineal.append('-1')
                
            else:
                pass
##        if "-1" in band_cota_lineal:
##            validaciones2.loc[27,'Resultado']=-1 # si hay un -1 en la bandera arroja error 
##            validaciones2.loc[27,'Observacion']="OK: Se acoto con dimensionado 'lineal' en lugar de 'alineado'"
##            validaciones2.loc[27,'Cetegoría']='Acotaciones'
##        else:
##            validaciones2.loc[27,'Resultado']=0 # si hay un -1 en la bandera arroja error 
##            validaciones2.loc[27,'Observacion']="OK: Se acoto con dimensionado 'alineado'"
##            validaciones2.loc[27,'Cetegoría']='Acotaciones'
            
            

        print("cotas parc ang")
        print(len(cotas_parc_ang))

        print("cotas parc lado")
        print(len(cotas_parc_lado))

        for i in range (len(lados_parcelas_l)):         #Para todas las parcelas suma la cantidad de lados que tiene para comparar con la cantidad de cotas realizadas 
            lados_parcelas=lados_parcelas+lados_parcelas_l[i]

        print ("lados_parcelas")
        print (lados_parcelas)
            
        for cota in cotas:        
            if cota.dxf.paperspace==0:
                band_cparc_model.append('-1')
            else:
                band_cparc_model.append('0')

            if len(cota.dxf.text)==0:
                band_cparc_med.append('0')
            else:
                band_cparc_med.append('-1')

                
        if '-1' in  band_cparc_model:
            validaciones2.loc[3,'Resultado']=-1 # si hay un -1 en la bandera arroja error 
            validaciones2.loc[3,'Observacion']="Error: Se acoto en el model"
            validaciones2.loc[3,'Cetegoría']='Acotaciones'
        else:
            validaciones2.loc[3,'Resultado']=0 # si hay un -1 en la bandera arroja error 
            validaciones2.loc[3,'Observacion']="OK: Se acoto en el Layout"
            validaciones2.loc[3,'Cetegoría']='Acotaciones'
        if '-1' in  band_cparc_med:
            validaciones2.loc[4,'Resultado']=-1 # si hay un -1 en la bandera arroja error 
            validaciones2.loc[4,'Observacion']="Error: Se modificó el valor real de alguna de las cotas de parcelas"
            validaciones2.loc[4,'Cetegoría']='Acotaciones'
        else:
            validaciones2.loc[4,'Resultado']=0 # si hay un -1 en la bandera arroja error 
            validaciones2.loc[4,'Observacion']="OK: No se han modificado los valores reales de las cotas de parcelas"
            validaciones2.loc[4,'Cetegoría']='Acotaciones'
            
        if (lados_parcelas==len(cotas_parc_lado)) and (lados_parcelas==len(cotas_parc_ang)):
            validaciones2.loc[5,'Resultado']=0 # si hay un -1 en la bandera arroja error 
            validaciones2.loc[5,'Observacion']="OK: Se acotó correctamente"
            validaciones2.loc[5,'Cetegoría']='Acotaciones'            
        else:
            if "1" in band_parc_arc:
                validaciones2.loc[5,'Resultado']=0 # si hay un -1 en la bandera arroja error 
                validaciones2.loc[5,'Observacion']="OK: Se acotó correctamente"
                validaciones2.loc[5,'Cetegoría']='Acotaciones'   
            else:
                validaciones2.loc[5,'Resultado']=-1 # si hay un -1 en la bandera arroja error 
                validaciones2.loc[5,'Observacion']="Error: No coinciden la cantidad de lados de la/s parcelas con la cantidad de acotaciones realizadas para angulos o lados, o las mismas no estan en el layer '03-P-MEDIDAS-PARCELA'"
                validaciones2.loc[5,'Cetegoría']='Acotaciones'
    else:
        validaciones2.loc[3,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
        validaciones2.loc[3,'Observacion']="Error: No se uso un Dimensionado para acotar"
        validaciones2.loc[3,'Cetegoría']='Acotaciones'

        validaciones2.loc[4,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
        validaciones2.loc[4,'Observacion']="Error: No se uso un Dimensionado para acotar"
        validaciones2.loc[4,'Cetegoría']='Acotaciones'

        validaciones2.loc[5,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
        validaciones2.loc[5,'Observacion']="Error: No se uso un Dimensionado 'Alineado' 'Angular' o 'de arco' para acotar"
        validaciones2.loc[5,'Cetegoría']='Acotaciones'        
    
    #--- 2.4.3 FIN Validación de Cotas --#

    
#--- 2.4 FIN Validación de elementos de Layout --#

#--- 2.5 INICIO Validación de elementos del model --#

def chequeo_model():
    global model
    global lados_parcelas_l
    global lados_parcelas
    global validaciones2
    global colores
    global sup_parc_poly
    global sup_ces_poly
    global sup_mens_poly
    global parcelas_poly_close



    #--- 2.5.1 INICIO Validación de Parcela--#
    parcelas = doc.modelspace().query('*[layer=="09-M-PARCELA"]')#  Busca las polylineas en el layer PARCELA
    parcelas_poly=list()
    parcelas_poly_close=list()
    band_poly_parc=list()   #lista de banderas para validar todas las entidades del layer parcela sean polilineas
    band_poly_cer_parc=list() #lista de banderas para validar que todas las las polylineas del layer parcela sean cerradas
    band_poly_gro_parc=list()
    band_poly_color_parc=list()
    band_parc_arc = list()
    
    global colores

    
    if len(parcelas): #si hay entindades en el layer patrcela comienza la validacion de las mismas sino arroja error que no hay nada en ese layer
        for parcela in parcelas:
            if parcela.dxftype()!= "LWPOLYLINE": # agrega -1 a la bandera cuando la entidas no es lwpolyline
                band_poly_parc.append('-1')
            else:
                band_poly_parc.append('0') # agrega 0 a la bandera cuando la entidad es lwpolyline
                parcelas_poly.append(parcela)

        if "-1" in band_poly_parc: # si hay un -1 en la bandera arroja error 
            validaciones2.loc[6,'Resultado']=-1
            validaciones2.loc[6,'Observacion']="Error: Existen entidades distintas de Polylineas en el Layer PARCELA"
            validaciones2.loc[6,'Cetegoría']='Parcela/s'  
        else:
            for parcela in parcelas_poly:
                if parcela.has_arc:
                    band_parc_arc.append("1")
                else:
                    band_parc_arc.append("0")
                if parcela.closed:
                    band_poly_cer_parc.append('0')  # agrega 0 a la bandera cuando la polylinea es cerrada
                else:
                    band_poly_cer_parc.append('-1') # agrega -1 a la bandera cuando la polylinea es abierta

            if '-1' in band_poly_cer_parc:
                validaciones2.loc[6,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
                validaciones2.loc[6,'Observacion']="Error: Se dibujaron polylineas Abiertas en el layer parcela"
                validaciones2.loc[6,'Cetegoría']='Parcela/s'  

            else:# si no hay un -1 en la bandera sigue validando color y grosor de polylineas.

                validaciones2.loc[6,'Resultado']=0 # si hay un -1 en la bandera arroja error 
                validaciones2.loc[6,'Observacion']="OK: Se dibujaron polylineas Cerradass en el layer parcela"
                validaciones2.loc[6,'Cetegoría']='Parcela/s'
                

        for parcela in parcelas:
            if parcela.dxf.color==colores.at[0,'Parcela']:   
                band_poly_color_parc.append('0')
            else:
                band_poly_color_parc.append('-1')

            if parcela.dxf.lineweight==-1:
                band_poly_gro_parc.append('0')
            else:
                band_poly_gro_parc.append('-1')
##                lados_parcelas_l.append(parcela.dxf.count)
                
        if '0' in band_poly_color_parc and '0' in band_poly_gro_parc:
            validaciones2.loc[7,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[7,'Observacion']="OK: Se dibujaron polylineas Cerradas configuradas correctamente en el layer PARCELA"
            validaciones2.loc[7,'Cetegoría']='Parcela/s'  

        elif '0' in band_poly_color_parc and '-1' in band_poly_gro_parc:
            validaciones2.loc[7,'Resultado']=-5 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[7,'Observacion']="Error: Grosor de polylineas erroneo en layer PARCELA"

        elif '-1' in band_poly_color_parc and '0' in band_poly_gro_parc:
            validaciones2.loc[7,'Resultado']=-4 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[7,'Observacion']="Error: Color de polylineas erroneo en layer PARCELA"
            validaciones2.loc[7,'Cetegoría']='Parcela/s'  

        elif '-1' in band_poly_color_parc and '-1' in band_poly_gro_parc:
            validaciones2.loc[7,'Resultado']=-3 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[7,'Observacion']="Error: Color y grosor de polylineas erroneo en layer PARCELA"
            validaciones2.loc[7,'Cetegoría']='Parcela/s'


                
    else:
        validaciones2.loc[6,'Resultado']=-1 #si no hay entindades en el layer parcela arroja error de validación
        validaciones2.loc[6,'Observacion']="Error: No se ecuentra diibujada la PARCELA en el Layer PARCELA"
        validaciones2.loc[6,'Cetegoría']='Parcela/s'

        validaciones2.loc[7,'Resultado']=-1 #si no hay entindades en el layer parcela arroja error de validación
        validaciones2.loc[7,'Observacion']="Error: No se ecuentra diibujada la PARCELA en el Layer PARCELA"
        validaciones2.loc[7,'Cetegoría']='Parcela/s'


    #--- 2.5.1 FIN Validación de Parcela --#

    #--- 2.5.2 INICIO Validación de Excedente--#
    excedentes = doc.modelspace().query('*[layer=="11-M-EXCEDENTE"]')#  Busca las polylineas en el layer EXCEDENTE

    band_poly_exc=list()   #lista de banderas para validar todas las entidades del layer excedente sean polilineas
    band_poly_cer_exc=list() #lista de banderas para validar que todas las las polylineas del layer parcela sean cerradas
    band_poly_gro_exc=list()
    band_poly_color_exc=list()

    global excedentes_poly
    global excedentes_poly_close

    excedentes_poly = list()
    excedentes_poly_close = list()


    if len(excedentes): #si hay entindades en el layer patrcela comienza la validacion de las mismas sino arroja error que no hay nada en ese layer
        for excedente in excedentes:
            if excedente.dxftype()!= "LWPOLYLINE": # agrega -1 a la bandera cuando la entidas no es lwpolyline
                band_poly_exc.append('-1')
            else:
                band_poly_exc.append('0') # agrega 0 a la bandera cuando la entidad es lwpolyline

        if "-1" in band_poly_exc: # si hay un -1 en la bandera arroja error 
            validaciones2.loc[8,'Resultado']=-1
            validaciones2.loc[8,'Observacion']="Error: Existen entidades distintas de Polylineas en el Layer EXCEDENTE"
            validaciones2.loc[8,'Cetegoría']='Parcela/s'  
        else:

            for excedente in excedentes:
                if excedente.dxftype()== "LWPOLYLINE":
                    if excedente.closed:
                        band_poly_cer_exc.append('0')  # agrega 0 a la bandera cuando la polylinea es cerrada
                        excedentes_poly_close.append(excedente)
                    else:
                        band_poly_cer_exc.append('-1') # agrega -1 a la bandera cuando la polylinea es abierta
                else:
                    pass
                
            if '-1' in band_poly_cer_exc:
                    validaciones2.loc[8,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
                    validaciones2.loc[8,'Observacion']="Error: Se dibujaron polylineas Abiertas en el layer EXCEDENTE"
                    validaciones2.loc[8,'Cetegoría']='Parcela/s'
            else:
                validaciones2.loc[8,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[8,'Observacion']="OK: Se dibujaron polylineas Cerradas en el layer EXCEDENTE"
                validaciones2.loc[8,'Cetegoría']='Parcela/s'#si la polylinea es cerrada sigue validando que tengan el color y grosor bylayer

                
        for excedente in excedentes: 
            if excedente.dxf.color==256:   
                band_poly_color_exc.append('0')
            else:
                band_poly_color_exc.append('-1')

            if excedente.dxf.lineweight==-1:
                        band_poly_gro_exc.append('0')
            else:
                band_poly_gro_exc.append('-1')

        if '0' in band_poly_color_exc and '0' in band_poly_gro_exc:
            validaciones2.loc[8,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[8,'Observacion']="OK: Se dibujaron polylineas Cerradas configuradas correctamente en el layer EXCEDENTE"
            validaciones2.loc[8,'Cetegoría']='Parcela/s'
            
        elif '0' in band_poly_color_exc and '-1' in band_poly_gro_exc:
            validaciones2.loc[9,'Resultado']=-5 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[9,'Observacion']="Error: Grosor de polylineas erroneo en layer EXCEDENTE"
            validaciones2.loc[9,'Cetegoría']='Parcela/s'
            
        elif '-1' in band_poly_color_exc and '0' in band_poly_gro_exc:
            validaciones2.loc[9,'Resultado']=-4 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[9,'Observacion']="Error: Color de polylineas erroneo en layer EXCEDENTE"
            validaciones2.loc[9,'Cetegoría']='Parcela/s'
            
        elif '-1' in band_poly_color_exc and '-1' in band_poly_gro_exc:
            validaciones2.loc[9,'Resultado']=-3 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[9,'Observacion']="Error: Color y grosor de polylineas erroneo en layer EXCEDENTE"
            validaciones2.loc[9,'Cetegoría']='Parcela/s'
        ## INICIO VERIFICACIÓN EXCEDENTE ESTE COMPLETAMENTE DENTRO DEL POLIGONO DE PARCELA.

        excedentes_poly= excedentes.query('LWPOLYLINE')
        parcelas_poly= parcelas.query('LWPOLYLINE')
        band_exc_dentro=list() #inicia bandera de control si cada uno de los excedentes estan dentro de una parcela
        for excedente in excedentes_poly: #reccorre poligonos de excedentes
            vertices_e1 = excedente.get_points('xy') #para cada excedente obtiene los vertices y los prepara para la función de control
            vertices_e2 = Vec2.list(vertices_e1)
            band_parc_dentro=list() #bandera que controla si el excedente x esta dentro de laguna de las parcelas
            for parcela in parcelas_poly: #fijado un excedente reccorre poligonos de parcelas para comparar vertices
                vertices_p1 = parcela.get_points('xy')  #para cada parcela obtiene los vertices y los prepara para la función de control
                vertices_p2 = Vec2.list(vertices_p1)
                vertices_p3 = list(ezdxf.math.offset_vertices_2d(vertices_p2,offset=-0.0001, closed=True))

                band_vert_dentro=list() #inicia bandera que valida si los vertices del excedente caen dentro de el polig. de parcela
                for i in range (0,len(vertices_e2)): 
                    
                    if ezdxf.math.is_point_in_polygon_2d(vertices_e2[i],vertices_p3,abs_tol=1e-3)==-1: #validación de vertices arroja -1 si cae fuera, 0 si cae en los limites y 1 si cae dentro

                        band_vert_dentro.append('-1') 
                    else:
                        band_vert_dentro.append('0')
                        
                if '-1' in band_vert_dentro:
                    band_parc_dentro.append('-1')
                else:
                    band_parc_dentro.append('0')
                del band_vert_dentro
                    
            if '0' in band_parc_dentro:
                band_exc_dentro.append('0')
                
            else:
                band_exc_dentro.append('-1')

            del band_parc_dentro

        if '-1' in band_exc_dentro:
            validaciones2.loc[10,'Resultado']=-1 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[10,'Observacion']="Error: Existe al menos un excedente fuera de la o las Parcelas mensuradas"
            validaciones2.loc[10,'Cetegoría']='Parcela/s'
        else:
            validaciones2.loc[10,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
            validaciones2.loc[10,'Observacion']="OK: El o los excedentes se encuentran completamente dentro de la/las Parcelas Mensuradas"
            validaciones2.loc[10,'Cetegoría']='Parcela/s'

            ## FIN VERIFICACIÓN EXCEDENTE ESTE COMPLETAMENTE DENTRO DEL POLIGONO DE PARCELA.
    else:
        
        validaciones2.loc[8,'Resultado']=99 # si no hay un -1 en la bandera indica que la validación es correcta.
        validaciones2.loc[8,'Observacion']="OK: Validacion de excedente no corresponde por encontrase el layer vacío, verifique que no se constituya excedenteo ya exista uno para la/s parcela mensuradas"
        validaciones2.loc[8,'Cetegoría']='Parcela/s'

        validaciones2.loc[9,'Resultado']=99 # si no hay un -1 en la bandera indica que la validación es correcta.
        validaciones2.loc[9,'Observacion']="OK: Validacion de excedente no corresponde por encontrase el layer vacío, verifique que no se constituya excedenteo ya exista uno para la/s parcela mensuradas"
        validaciones2.loc[9,'Cetegoría']='Parcela/s'

        validaciones2.loc[10,'Resultado']=99 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
        validaciones2.loc[10,'Observacion']="OK: Validacion de excedente no corresponde por encontrase el layer vacío, verifique que no se constituya excedenteo ya exista uno para la/s parcela mensuradas"
        validaciones2.loc[10,'Cetegoría']='Parcela/s'
     

    #--- 2.5.2 FIN Validación de Excedente --#

    #--- 2.5.3 INICIO Validación de Bloque NOmenclatura Parcela --#

    #Validar que se encuentre inserto y completo el bloque "PARCELA_VIGENTE" tantas veces como poligonos cerrados de parcela haya. 

    bloque_PARCELA_SURGENTE = doc.modelspace().query('INSERT[name=="PARCELA_SURGENTE"]')
    patron_parc = re.compile('(^([0-9]{3})|([0-9]{3}[a-z]{1}))$') #patron para validar el formato de la parcela escrito en el bloque mensura
    nom_parc_list=list()
    band_nom_par = list() #bandera que guarda si la nomenclatura del bloque parc. vigente se coloco correctamente formato "000a"
    print ("bloque parc:") 
    print (len(bloque_PARCELA_SURGENTE))

    for parcela in parcelas_poly:
        if parcela.close:
            parcelas_poly_close.append(parcela)
        else:
            pass
    
    #valida que haya la misma cantidad de bloques de parcela insertos en el dxf que la cantidad de parcelas del layer parcelas.    
    if len(bloque_PARCELA_SURGENTE)>0:

        if len(bloque_PARCELA_SURGENTE)==len(parcelas_poly_close):
            validaciones2.loc[11,'Resultado']=0
            validaciones2.loc[11,'Observacion']='OK: Exiten tantos bloques "PARCELA_VIGENTE" como parcelas que surgen o se mantienen vigentes con el presente plano'
            validaciones2.loc[11,'Cetegoría']='Bloques' 

        elif len(bloque_PARCELA_SURGENTE)>len(parcelas_poly_close):
            validaciones2.loc[11,'Resultado']=-2
            validaciones2.loc[11,'Observacion']='Error: Exiten más bloques de "PARCELA_VIGENTE" que parcelas como parcelas que surgen o se mantienen vigentes con el presente plano'
            validaciones2.loc[11,'Cetegoría']='Bloques' 

        elif len(bloque_PARCELA_SURGENTE)<len(parcelas_poly_close):
            validaciones2.loc[11,'Resultado']=-3
            validaciones2.loc[11,'Observacion']='Error: Exiten menos bloques de "PARCELA_VIGENTE" que parcelas como parcelas que surgen o se mantienen vigentes con el presente plano'
            validaciones2.loc[11,'Cetegoría']='Bloques' 
 #valida que haya la misma cantidad de bloques de parcela insertos en el dxf que la cantidad de parcelas del layer parcelas

        else:
            pass

        ban_bparc_comp=list()
        band_nom_parc = list()
                
        for bloque in (bloque_PARCELA_SURGENTE):
                for attrib in bloque.attribs:
                    if attrib.dxf.tag=="NPARC":
                        nom_parc_list.append(attrib.dxf.text)
                        if attrib.dxf.text == None:
                            ban_bparc_comp.append(-1)
                        else:
                            ban_bparc_comp.append(0)

                if -1 in ban_bparc_comp:
                    validaciones2.loc[12,'Resultado']=-1
                    validaciones2.loc[12,'Observacion']='ERROR: El o los bloques "PARCELA_SURGENTE" estan vacíos'
                    validaciones2.loc[12,'Cetegoría']='Bloques' 

                else:

                    #validar que la nomenclatura del bloque Parc_vig tegnga elformato correcto 000a#

                    for i in nom_parc_list:
                        band_nom_parc.append(patron_parc.match(i))                                            
            

                    if None in band_nom_parc:
                        validaciones2.loc[12,'Resultado']=-1
                        validaciones2.loc[12,'Observacion']='Error: La nomenclatura indicada en el/alguno de los bloque/s "PARCELA_SURGENTE" no respeta el formato 000a'
                        validaciones2.loc[12,'Cetegoría']='Bloques'
                    else:
                        validaciones2.loc[12,'Resultado']=0
                        validaciones2.loc[12,'Observacion']='OK: La nomenclatura indicada los bloque/s "PARCELA_SURGENTE" respeta el formato 000a'
                        validaciones2.loc[12,'Cetegoría']='Bloques'
            
                    #validar que la nomenclatura del bloque Parc_vig tegnga elformato correcto 000a#

        #Validar que el bloque de nomenclatura este en el model y adentro de una parcela#

        

                        

        #Validar que el bloque de nomenclatura este en el model y adentro de una parcela#
        

    else:
        validaciones2.loc[11,'Resultado']=-1
        validaciones2.loc[11,'Observacion']='Error: No se encuentra inserto el bloque "PARCELA_SURGENTE" por cada una de las parcelas que surgen o se mantienen vigentes con este plano'
        validaciones2.loc[11,'Cetegoría']='Bloques'

        validaciones2.loc[12,'Resultado']=99
        validaciones2.loc[12,'Observacion']='ERROR: No se puede validar el bloque "PARCELA_SURGENTE" dado que no se encuentra inserto'
        validaciones2.loc[12,'Cetegoría']='Bloques'

            
    #--- 2.5.3 FIN Validación de Bloque Nomenclatura Parcela --#  


    #--- 2.5.4 INICIO Validación de MEJORAS--#

    mejoras = doc.modelspace().query('*[layer=="MEJORAS"]') #  Busca las polylineas en el layer MEJORAS
    band_poly_mej=list()   #lista de banderas para validar todas las entidades del layer excedente sean polilineas
    band_poly_cer_mej=list() #lista de banderas para validar que todas las las polylineas del layer parcela sean cerradas
    band_poly_gro_mej=list()
    band_poly_color_mej=list()

    print(len(mejoras))
    print(mejoras)
    if len(mejoras): #si hay entindades en el layer parcela comienza la validacion de las mismas sino arroja error que no hay nada en ese layer
        for mejora in mejoras:
            if mejora.dxftype()!= "LWPOLYLINE": # agrega -1 a la bandera cuando la entidas no es lwpolyline
                band_poly_mej.append('-1')
            else:
                band_poly_mej.append('0') # agrega 0 a la bandera cuando la entidad es lwpolyline

        if "-1" in band_poly_mej: # si hay un -1 en la bandera arroja error 
            validaciones2.loc[13,'Resultado']=-1
            validaciones2.loc[13,'Observacion']="Error: Existen entidades distintas de Polylineas en el Layer MEJORAS"
            validaciones2.loc[13,'Cetegoría']='Mejoras'  
        else:
            for mejora in mejoras:
                if mejora.closed:
                    band_poly_cer_mej.append('0')  # agrega 0 a la bandera cuando la polylinea es cerrada
                    
                else:
                    band_poly_cer_mej.append('-1') # agrega -1 a la bandera cuando la polylinea es abierta
            
            if '-1' in band_poly_cer_mej:
                    validaciones2.loc[13,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
                    validaciones2.loc[13,'Observacion']="Error: Se dibujaron polylineas Abiertas en el layer MEJORAS"
                    validaciones2.loc[13,'Cetegoría']='Mejoras'
            else:
                    validaciones2.loc[13,'Resultado']=0 # si hay un -1 en la bandera arroja error 
                    validaciones2.loc[13,'Observacion']="OK: Se dibujaron polylineas Cerradas en el layer MEJORAS"
                    validaciones2.loc[13,'Cetegoría']='Mejoras'

                #si la polylinea es cerrada sigue validando que tengan el color y grosor bylayer                    
            for mejora in mejoras:
                if mejora.dxf.color==256:   
                    band_poly_color_mej.append('0')
                else:
                    band_poly_color_mej.append('-1')

                if mejora.dxf.lineweight==-1:
                    band_poly_gro_mej.append('0')
                else:
                    band_poly_gro_mej.append('-1')

            if '0' in band_poly_color_mej and '0' in band_poly_gro_mej:
                validaciones2.loc[14,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[14,'Observacion']="OK: Se dibujaron polylineas Cerradas configuradas correctamente en el layer MEJORAS"
                validaciones2.loc[14,'Cetegoría']='Mejoras'
                
            elif '0' in band_poly_color_mej and '-1' in band_poly_gro_mej:
                validaciones2.loc[14,'Resultado']=-5 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[14,'Observacion']="Error: Grosor de polylineas erroneo en layer MEJORAS"
                validaciones2.loc[14,'Cetegoría']='Mejoras'

            elif '-1' in band_poly_color_mej and '0' in band_poly_gro_mej:
                validaciones2.loc[14,'Resultado']=-4 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[14,'Observacion']="Error: Color de polylineas erroneo en layer MEJORAS"

            elif '-1' in band_poly_color_mej and '-1' in band_poly_gro_mej:
                validaciones2.loc[14,'Resultado']=-3 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[14,'Observacion']="Error: Color y grosor de polylineas erroneo en layer MEJORAS"
                validaciones2.loc[14,'Cetegoría']='Mejoras'
                        
            ## INICIO VERIFICACIÓN MEJORA ESTE COMPLETAMENTE DENTRO DEL POLIGONO DE PARCELA.

            global mejoras_poly

            mejoras_poly= mejoras.query('LWPOLYLINE')
            parcelas_poly= parcelas.query('LWPOLYLINE')
            band_mej_dentro=list() #inicia bandera de control si cada uno de las mejoras estan dentro de una parcela
            for mejora in mejoras_poly: #reccorre poligonos de mejoras
                vertices_e1 = mejora.get_points('xy') #para cada mejora obtiene los vertices y los prepara para la función de control
                vertices_e2 = Vec2.list(vertices_e1)
                band_parc_dentro=list() #bandera que controla si la mejora x esta dentro de alguna de las parcelas
                for parcela in parcelas_poly: #fijado una mejora reccorre poligonos de parcelas para comparar vertices
                    vertices_p1 = parcela.get_points('xy')  #para cada parcela obtiene los vertices y los prepara para la función de control
                    vertices_p2 = Vec2.list(vertices_p1)
                    vertices_p3 = list(ezdxf.math.offset_vertices_2d(vertices_p2,offset=-0.0001, closed=True))

                    band_vert_dentro=list() #inicia bandera que valida si los vertices de la mejora caen dentro de el polig. de parcela
                    for i in range (0,len(vertices_e2)): 
                        
                        if ezdxf.math.is_point_in_polygon_2d(vertices_e2[i],vertices_p3,abs_tol=1e-3)==-1: #validación de vertices arroja -1 si cae fuera, 0 si cae en los limites y 1 si cae dentro

                            band_vert_dentro.append('-1') 
                        else:
                            band_vert_dentro.append('0')
                            
                    if '-1' in band_vert_dentro:
                        band_parc_dentro.append('-1')
                    else:
                        band_parc_dentro.append('0')
                    del band_vert_dentro
                        
                if '0' in band_parc_dentro:
                    band_mej_dentro.append('0')
                    
                else:
                    band_mej_dentro.append('-1')

                del band_parc_dentro

            if '-1' in band_mej_dentro:
                validaciones2.loc[15,'Resultado']=-1 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[15,'Observacion']="Error: Existe Mejora fuera de los limites de Parcela"
                validaciones2.loc[15,'Cetegoría']='Mejoras'
            else:
                validaciones2.loc[15,'Resultado']=0 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
                validaciones2.loc[15,'Observacion']="OK: La o las mejoras estan completamente contenidas dentro de alguna Parcela"
                validaciones2.loc[15,'Cetegoría']='Mejoras'

            ## FIN VERIFICACIÓN EXCEDENTE ESTE COMPLETAMENTE DENTRO DEL POLIGONO DE PARCELA.

    else:
        validaciones2.loc[13,'Resultado']=99 # si no hay un -1 en la bandera indica que la validación es correcta.
        validaciones2.loc[13,'Observacion']="OK: Validacion de Mejoras no corresponde por encontrase el layer vacío, verifique que se trate de un inmueble baldío"
        validaciones2.loc[13,'Cetegoría']='Mejoras'

        validaciones2.loc[14,'Resultado']=99 # si no hay un -1 en la bandera indica que la validación es correcta.
        validaciones2.loc[14,'Observacion']="OK: Validacion de Mejoras no corresponde por encontrase el layer vacío, verifique que se trate de un inmueble baldío"
        validaciones2.loc[14,'Cetegoría']='Mejoras'

        validaciones2.loc[15,'Resultado']=99 # si no hay un -1 en la bandera indica que la validación es correcta.
        validaciones2.loc[15,'Observacion']="OK: Validacion de Mejoras no corresponde por encontrase el layer vacío, verifique que se trate de un inmueble baldío"
        validaciones2.loc[15,'Cetegoría']='Mejoras'


    #--- 2.5.4 FIN Validación de MEJORAS--#

    #--- 2.5.5 INICIO Validación de cesiones--#

    global cesion_poly
    global cesion_poly_close
    cesiones = doc.modelspace().query('*[layer=="12-M-CESION"]') #  Busca las polylineas en el layer MEJORAS
    band_poly_ces=list()    #lista de banderas para validar todas las entidades del layer cesiones sean polilineas
    band_poly_cer_ces=list() #lista de banderas para validar que todas las las polylineas del layer cesiones sean cerradas
    band_poly_gro_ces=list()
    band_poly_color_ces=list()
    cesion_poly=list()
    cesion_poly_close=list()

    if len(cesiones): #si hay entindades en el layer parcela comienza la validacion de las mismas sino arroja error que no hay nada en ese layer
        for cesion in cesiones:
            if cesion.dxftype()!= "LWPOLYLINE": # agrega -1 a la bandera cuando la entidas no es lwpolyline
                band_poly_ces.append('-1')
            else:
                band_poly_ces.append('0')# agrega 0 a la bandera cuando la entidad es lwpolyline
                cesion_poly.append(cesion)
        if "-1" in band_poly_ces: # si hay un -1 en la bandera arroja error 
            validaciones2.loc[16,'Resultado']=-1
            validaciones2.loc[16,'Observacion']="Error: Existen entidades distintas de Polylineas en el Layer CESIONES"
            validaciones2.loc[16,'Cetegoría']='Cesiones'
        else:
            for cesion in cesiones:
                if cesion.closed:
                    band_poly_cer_ces.append('0')  # agrega 0 a la bandera cuando la polylinea es cerrada
                    cesion_poly_close.append(cesion)
                else:
                    band_poly_cer_ces.append('-1') # agrega -1 a la bandera cuando la polylinea es abierta
            
            if '-1' in band_poly_cer_ces:
                    validaciones2.loc[16,'Resultado']=-2 # si hay un -1 en la bandera arroja error 
                    validaciones2.loc[16,'Observacion']="Error: Se dibujaron polylineas Abiertas en el layer CESIONES"
                    validaciones2.loc[16,'Cetegoría']='Cesiones'

            else: #si la polylinea es cerrada sigue validando que tengan el color y grosor bylayer                    

                    validaciones2.loc[16,'Resultado']=0 # si hay un -1 en la bandera arroja error 
                    validaciones2.loc[16,'Observacion']="OK: Se dibujaron polylineas Cerradas en el layer CESIONES"
                    validaciones2.loc[16,'Cetegoría']='Cesiones'


            for cesion in cesiones:
                if cesion.dxf.color==256:   
                    band_poly_color_ces.append('0')
                else:
                    band_poly_color_ces.append('-1')

                if cesion.dxf.lineweight==-1:
                    band_poly_gro_ces.append('0')
                else:
                    band_poly_gro_ces.append('-1')

            if '0' in band_poly_color_ces and '0' in band_poly_gro_ces:
                validaciones2.loc[17,'Resultado']=0 # Valida si las polilineas del layer CESIONES tienen el grosor y color bylayer
                validaciones2.loc[17,'Observacion']="OK: Se dibujaron polylineas Cerradas configuradas correctamente en el layer CESIONES"
                validaciones2.loc[17,'Cetegoría']='Cesiones'

            elif '0' in band_poly_color_ces and '-1' in band_poly_gro_ces:
                validaciones2.loc[17,'Resultado']=-5 # Valida si las polilineas del layer CESIONES tienen el grosor y color bylayer
                validaciones2.loc[17,'Observacion']="Error: Grosor de polylineas erroneo en layer CESIONES"
                validaciones2.loc[17,'Cetegoría']='Cesiones'

            elif '-1' in band_poly_color_ces and '0' in band_poly_gro_ces:
                validaciones2.loc[17,'Resultado']=-4 # Valida si las polilineas del layer CESIONES tienen el grosor y color bylayer
                validaciones2.loc[17,'Observacion']="Error: Color de polylineas erroneo en layer CESIONES"
                validaciones2.loc[17,'Cetegoría']='Cesiones'

            elif '-1' in band_poly_color_ces and '-1' in band_poly_gro_ces:
                validaciones2.loc[17,'Resultado']=-3 # Valida si las polilineas del layer CESIONES tienen el grosor y color bylayer
                validaciones2.loc[17,'Observacion']="Error: Color y grosor de polylineas erroneo en layer CESIONES"
                validaciones2.loc[17,'Cetegoría']='Cesiones'

                        
    else:
        validaciones2.loc[16,'Resultado']=99 # Valida si las polilineas del layer parcela tienen el grosor y color bylayer
        validaciones2.loc[16,'Observacion']="OK: Validacion de CESIONES no corresponde por encontrase el layer vacío, verifique que no se deba realizar ninguna cesion en la mensura"
        validaciones2.loc[16,'Cetegoría']='Cesiones'

        validaciones2.loc[17,'Resultado']=99 # Valida si las polilineas del layer CESIONES tienen el grosor y color bylayer
        validaciones2.loc[17,'Observacion']="OK: Validacion de CESIONES no corresponde por encontrase el layer vacío, verifique que no se  deba realizar ninguna cesion en la mensura"
        validaciones2.loc[17,'Cetegoría']='Cesiones'
           
#----------- 2.5.5 FIN Validación de cesiones----------------#


#----------- 2.5.6 INICIO Validación de Balance--------------#
    
    #<--- INICIO valida que el balance este compelto en todas las caratulas ---->


    ban_bloque_supmen=list()
    ban_bloque_suptit=list()
    ban_bloque_supdif=list()

    bloque_supmen_list=list()
    bloque_suptit_list=list()
    bloque_supdif_list=list()
    bloque_tipodif_list=list()

    global bloque_caratula
    global bloque_car_model
    
    bloque_caratula = doc.query('INSERT[name=="CARATULA-CABA"]')
    if len(bloque_caratula)>0:

        for bloque in (bloque_caratula):
            ban_supmen_vacio=list()
            ban_suptit_vacio=list()
            ban_supdif_vacio=list()

            for attrib in bloque.attribs:
                if attrib.dxf.tag=="SUPS/M":
                    bloque_supmen_list.append(attrib.dxf.text)
                    if len(attrib.dxf.text) == 0:
                        ban_supmen_vacio.append('-1')
                    else:
                        ban_supmen_vacio.append('0')

                elif attrib.dxf.tag=="SUPS/T-P":
                    bloque_suptit_list.append(attrib.dxf.text)
                    if len(attrib.dxf.text)==0:
                        ban_suptit_vacio.append('-1')
                    else:
                        ban_suptit_vacio.append('0')

                elif attrib.dxf.tag=="DIFBALANCE":
                    bloque_supdif_list.append(attrib.dxf.text)
                    if len(attrib.dxf.text) == 0:
                        ban_supdif_vacio.append('-1')
                    else:
                        ban_supdif_vacio.append('0')
                elif attrib.dxf.tag=="TIPODIF":
                    bloque_tipodif_list.append(attrib.dxf.text)
                else:
                    pass

            if '-1' in ban_supmen_vacio:
                ban_bloque_supmen.append('-1')

            else:
                ban_bloque_supmen.append('0')


            if '-1' in ban_suptit_vacio:
                ban_bloque_suptit.append('-1')

            else:
                ban_bloque_suptit.append('0')

            if '-1' in ban_supdif_vacio:
                ban_bloque_supdif.append('-1')

            else:
                ban_bloque_supdif.append('0')
                
                    
            del ban_supmen_vacio
            del ban_suptit_vacio
            del ban_supdif_vacio

                
        if (('-1' in ban_bloque_supmen) or ('-1' in ban_bloque_suptit) or ('-1' in ban_bloque_supdif)):
            validaciones2.loc[18,'Resultado']=-1
            validaciones2.loc[18,'Observacion']='ERROR: Se encuentran vacíos algunos de los campos SUPS/M, SUPS/T-P y DIFBALANCE de almenos una de las caratulas insertadas'
            validaciones2.loc[18,'Cetegoría']='Caratula'
        else:
            validaciones2.loc[18,'Resultado']=0
            validaciones2.loc[18,'Observacion']='OK: Se encuentra comepletos los campos del balance de las caratulas insertadas'
            validaciones2.loc[18,'Cetegoría']='Caratula'
    else:
        validaciones2.loc[18,'Resultado']=-1
        validaciones2.loc[18,'Observacion']='ERROR: no hay bloque caratula inserto en el plano'
        validaciones2.loc[18,'Cetegoría']='Caratula'
    #<----- valida que coincica la sup de mensura del balance con la suma de la sup de los poligonos de parcela y cesiones ------->


    cesiones_poly_closed = list()
    cesiones_poly = cesiones.query('LWPOLYLINE')

    ban_dif_sup=list()

 

    for parcela in parcelas_poly_close:
        vertices_p1 = parcela.get_points('xy')  #para cada parcela obtiene los vertices y los prepara para la función de control
        vertices_p2 = Vec2.list(vertices_p1)
        sup_parc_poly = sup_parc_poly + round(ezdxf.math.area(vertices_p2),2) #suma la superficie de todas las parcelas redondeadas previamente a los 2 decimales.

        del vertices_p1
        del vertices_p2


    for cesion in cesiones_poly:
        if cesion.closed:
            cesiones_poly_closed.append(cesion)
        else:
            pass
    if len(cesiones_poly_closed)!= 0:       

        for cesion in cesiones_poly_closed:
            vertices_c1 = cesion.get_points('xy')  #para cada cesion obtiene los vertices y los prepara para la función de control
            vertices_c2 = Vec2.list(vertices_c1)
            sup_ces_poly = sup_ces_poly + round(ezdxf.math.area(vertices_c2),2) #suma la superficie de todas las cesiones redondeadas previamente a los 2 decimales.      del vertices_c1
            del vertices_c2
    else:
        pass


    sup_mens_poly = round((sup_parc_poly + sup_ces_poly),2)




#<---------- FIN valida que el balance este compelto en todas las caratulas ----->


#<----------- 2.5.6 FIN Validación de Balance----------------------------------->#

    #--- 2.5.7 INICIO Validación de Georreferenciación--#
                
    CABA_DF = pd.DataFrame()
    CABA_DF = pd.read_excel('coordenadas_caba.xls') #data frame con archivo de coordenadas de CABA xls
    Caba_poly = list()
    for i in range (len(CABA_DF)):
        Caba_poly.append([CABA_DF.iat[i,0],CABA_DF.iat[i,1]]) #Arma lista con coordenadas de CABA

    parcelas_poly= parcelas.query('LWPOLYLINE')

    vertices_p2 = Vec2.list(Caba_poly)  #para la Caba obtiene los vertices y los prepara para la función de control
    vertices_p3 = list(ezdxf.math.offset_vertices_2d(vertices_p2,offset=-0.0001, closed=True)) #arma un poligono un poquito mas grande para resolver el problema que ocurre cuando los poligonos se tocan en sus lados

    band_caba_dentro=list() #bandera que controla si la parcela x esta dentro de caba

    for parcela in parcelas_poly: #reccorre poligonos de parcelas
        vertices_e1 = parcela.get_points('xy') #para cada parcela obtiene los vertices y los prepara para la función de control
        vertices_e2 = Vec2.list(vertices_e1)
        band_vert_dentro=list()

        for i in range (0,len(vertices_e2)): 
                        
            if ezdxf.math.is_point_in_polygon_2d(vertices_e2[i],vertices_p3,abs_tol=1e-3)==-1: #validación de vertices arroja -1 si cae fuera, 0 si cae en los limites y 1 si cae dentro

                band_vert_dentro.append('-1') 
            else:
                band_vert_dentro.append('0')
                            
        if '-1' in band_vert_dentro:
            band_caba_dentro.append('-1')
        else:
            band_caba_dentro.append('0')
        del band_vert_dentro
                    

    if '-1' in band_caba_dentro:
        validaciones2.loc[19,'Resultado']=-1 # Valida si las parcelas se georreferenciarion
        validaciones2.loc[19,'Observacion']="Error: Existe parcela que no ha sido georreferenciada en el sistema de Coordenadas oficial de la Ciudad"
        validaciones2.loc[19,'Cetegoría']='Caratula'

    else:
        validaciones2.loc[19,'Resultado']=0 # Valida si las parcelas se georreferenciarion
        validaciones2.loc[19,'Observacion']="OK: Se ha georreferenciado la/s Parcelas en el sistema de Coordenadas oficial de la Ciudad"
        validaciones2.loc[19,'Cetegoría']='Caratula'
    #--- 2.5.7 FIN Validación de Georreferenciación---#
        

#--- 2.5 FIN Validación de elementos del model --#

#--- 2.6 INICIO Validación de Caratula --#

def chequeo_caratula():
    global layouts
    caratulas=doc.query('INSERT[name=="CARATULA-CABA"]') #consulta el bloque caratula (todas las veces que se inserto)
    model_1 = list()
    point_model = list()
    model = doc.modelspace()
    bloque_caratula_model = doc.modelspace().query('INSERT[name=="CARATULA-CABA"]')
            
    bandera_layer=list()
    bandera_model=list()
    global validaciones2

    # INICIO Validar que este inserto el bloque caratula, en el/los layouts, en el layer correcto 
    print("leng caratulas")
    print(len(caratulas))

    print("Caratula model")
    print(len(bloque_caratula_model))

    print("Layout caratula model_1")
    print(model_1)

    print("Layout caratula point insert")
    print(point_model)



    if len(caratulas)>0: #Valida si se está inserto el bloque caratula
    
        validaciones2.loc[20,'Resultado']=0
        validaciones2.loc[20,'Observacion']='OK: Se encuentra inserto el Bloque Caratula'
        validaciones2.loc[20,'Cetegoría']='Caratula'
        

        for caratula in caratulas:              

            #Inicio validar que la caratula este inserta en layer que corresponde
            if caratula.dxf.layer=="01-P-PLANO-CARATULA": 
                bandera_layer.append('0')
            else:
                bandera_layer.append('-1')
            #Fin validar que la caratula este inserta en layer que corresponde

            #Inicio validar que la caratula este inserta en los Layouts

##            if caratula.dxf.paperspace==0:
##                bandera_model.append('-1')
##            else:
##                bandera_model.append('0')
            #Fin validar que la caratula este inserta en los Layouts

        if len(bloque_caratula_model)>0:
            bandera_model.append('-1')
        else:
            bandera_model.append('0')

        print("bandera model")
        print(bandera_model)

                
        if '-1' in bandera_layer:

            validaciones2.loc[21,'Resultado']=-1
            validaciones2.loc[21,'Observacion']='Error: La caratula se encuentra inserta en el Layer Incorrecto'
            validaciones2.loc[21,'Cetegoría']='Caratula'
        else:

            validaciones2.loc[21,'Resultado']=0
            validaciones2.loc[21,'Observacion']='OK: La caratula se encuentra inserta en el Layer correcto'
            validaciones2.loc[21,'Cetegoría']='Caratula'

        if '-1' in bandera_model:

            validaciones2.loc[22,'Resultado']=-1
            validaciones2.loc[22,'Observacion']='Error: Existe caratula inserta en el espacio modelo'
            validaciones2.loc[22,'Cetegoría']='Caratula'
        else:

            validaciones2.loc[22,'Resultado']=0
            validaciones2.loc[22,'Observacion']='OK: La o las caratulas se encuentran insertas en el/los Layout/s'
            validaciones2.loc[22,'Cetegoría']='Caratula'
    else:

        validaciones2.loc[20,'Resultado']=-1
        validaciones2.loc[20,'Observacion']='Error: No se encuentra inserto el Bloque Caratula'
        validaciones2.loc[20,'Cetegoría']='Caratula'
        
        validaciones2.loc[21,'Resultado']=-2
        validaciones2.loc[21,'Observacion']='Error: No es posible validar la caratula dado que no se encuentra inserto el bloque caratula'
        validaciones2.loc[21,'Cetegoría']='Caratula'

        validaciones2.loc[22,'Resultado']=-2
        validaciones2.loc[22,'Observacion']='Error: No es posible validar la caratula dado que no se encuentra inserto el bloque caratula'
        validaciones2.loc[22,'Cetegoría']='Caratula'
    # FIN Validar que este inserto el bloque caratula, en el/los layouts, en el layer correcto 

    #INICIO validar que la caratula tenga los atributos completos y que sean coherentes excepto el balance que se valida mas adelante

    atributos_tag = list()
    caratulas_valores = pd.DataFrame() #ver como cargar los atributos de la lista en las columnas del dataframe
    bloque_caratula = doc.query('INSERT[name=="CARATULA-CABA"]')

    #variables que leen las distintas caratulas y guardan un dato especifico para cada caratula

#recolectores de atributos de varias caratulas ára comparar que sean iguales y que no esten vacios#

    global car_manz
    global car_parc

    car_circ = list()
    car_sec = list()
    car_manz = list()
    car_parc = list()
    car_direc = list()
    car_prop = list ()
    car_dominio = list()
    car_fecha_mens = list()
    car_cur = list()
    car_partida = list()
    car_num_plano = list()
    car_tipo_plano = list()
    car_año_plano = list()
    car_hoja = list()
    car_objeto = list()
    car_agrim = list()
    car_cuit = list()
    car_mens = list()
    car_tit = list()
    car_dif = list()
    car_tipo_dif = list()


    
#recolectores de atributos de varias caratulas#

#Banderas de igualdad de atributos en varias caratulas#
    
    band_circ = list()
    band_sec = list()
    band_manz = list()
    band_parc = list()
    band_direc = list()
    band_prop = list ()
    band_domino = list()
    band_fecha_mens = list()
    band_cur = list()
    band_partida = list()
    band_num_plano = list()
    band_tipo_plano = list()
    band_año_plano = list()
    band_hoja = list()
    band_objeto = list()
    band_agrim = list()
    band_cuit = list()
    band_mens = list()
    band_tit = list()
    band_dif = list()
    band_tipo_dif = list()


    
#Banderas de igualdad de atributos en varias caratulas#

#Banderas de vacio de atributos#
    
    band_vac_circ = list()
    band_vac_sec = list()
    band_vac_manz = list()
    band_vac_parc = list()
    band_vac_direc = list()
    band_vac_prop = list ()
    band_vac_domino = list()
    band_vac_fecha_mens = list()
    band_vac_cur = list()
    band_vac_partida = list()
    band_vac_num_plano = list()
    band_vac_tipo_plano = list()
    band_vac_año_plano = list()
    band_vac_tipo_plano = list()
    band_vac_año_plano = list()
    band_vac_hoja = list()
    band_vac_objeto = list()
    band_vac_agrim = list()
    band_vac_cuit = list()
    band_vac_mens = list()
    band_vac_tit = list()
    band_vac_dif = list()
    band_vac_tipo_dif = list()

#Banderas de vacio de atributos#
    
    #variables que leen las distintas caratulas y guardan un dato especifico para cada caratula

    for caratula in bloque_caratula:

        for attribs in caratula.attribs:
        
            if attribs.dxf.tag == "0201-CIRC.":
                
                car_circ.append(attribs.dxf.text)
                
            elif attribs.dxf.tag == "0202-SECC.":
                
               car_sec.append(attribs.dxf.text)
               
            elif attribs.dxf.tag == "0203-MANZ.":
                
                car_manz.append(attribs.dxf.text)
                
            elif attribs.dxf.tag == "0204-PARC.":
                
                car_parc.append(attribs.dxf.text)
                
            elif attribs.dxf.tag == "0205-CALLE":
                
                car_direc.append(attribs.dxf.text)
                
            elif attribs.dxf.tag == "0206-PROPIETARIOS":
                
                car_prop.append(attribs.dxf.text)
                
            elif attribs.dxf.tag == "0208-RPI":

                car_dominio.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0801-FECHA":

                car_fecha_mens.append(attribs.dxf.text)
            
            elif attribs.dxf.tag == "0302-C.U.R":

                car_cur.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0207-PARTIDA":

                car_partida.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0901-TIPO":

                car_tipo_plano.append(attribs.dxf.text)

            elif attribs.dxf.tag =="0902-NUM":
                car_num_plano.append(attribs.dxf.text)

            elif attribs.dxf.tag =="0903-AÑO":
                car_año_plano.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0102-HOJA":

                car_hoja.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0103-PLANO":

                car_objeto.append(attribs.dxf.text)            

            elif attribs.dxf.tag == "0802-AGRIMENSOR":

                car_agrim.append(attribs.dxf.text)

            elif attribs.dxf.tag == "0807-CUIT-AGRIM.":

                car_cuit.append(attribs.dxf.text)
                
            elif attribs.dxf.tag =="SUPS/M":
                
                car_mens.append(attribs.dxf.text)

            elif attribs.dxf.tag =="SUPS/T-P":
                
                car_tit.append(attribs.dxf.text)

            elif attribs.dxf.tag =="DIFBALANCE":
                
                car_dif.append(attribs.dxf.text)

            elif attribs.dxf.tag =="TIPODIF":
                car_tipo_dif.append(attribs.dxf.text)
            else: 
                pass
    print("car_num_plano")
    print(car_num_plano)

    print("car_tipo_plano")
    print(car_tipo_plano)

    print("car_año_plano")
    print(car_año_plano)


    #si tiene mas de una caratula verifica que se hayan puesto los mismos datos para el mismo campo en todas las caratulas#

    if len(bloque_caratula)>1:

        for i in range (len(bloque_caratula)):
            if car_circ[i-1] == car_circ[i]: #Evalua que todos los valores de circunscripción, sean iguales
                band_circ.append('0')
            else:
                band_circ.append('-1')

            if car_sec[i-1] == car_sec[i]: #Evalua que todos los valores de sección, sean iguales
                band_sec.append('0')
            else:
                band_sec.append('-1')

            if car_manz[i-1] == car_manz[i]: #Evalua que todos los valores de manzana, sean iguales
                band_manz.append('0')
            else:
                band_manz.append('-1')

            if car_parc[i-1] == car_parc[i]: #Evalua que todos los valores de parcela, sean iguales
                band_parc.append('0')
            else:
                band_parc.append('-1')

            #if car_direc[i-1] == car_direc[i]: #Evalua que todos los valores de dirección, sean iguales, EL valor de calle en la caratula es MTEXT, y por esa razón no se carga en car_direc
             #   band_direc.append('0')
            #else:
             #   band_direc.append('-1')

            #if car_prop[i-1] == car_prop[i]: #Evalua que todos los valores de propietarios, sean iguales, no se carga bien car_prop por ser mtext
             #   band_prop.append('0')
            #else:
             #   band_prop.append('-1')

            #if car_dominio[i-1] == car_dominio[i]: #Evalua que todos los valores de dominio, sean iguales, no se carga bien car_dominio por ser mtext
             #   band_dominio.append('0')
           # else:
            #    band_dominio.append('-1')

            if car_fecha_mens[i-1] == car_fecha_mens[i]: #Evalua que todos los valores de fecha de mensura, sean iguales
                band_fecha_mens.append('0')
            else:
                band_fecha_mens.append('-1')

            #if car_cur[i-1] == car_cur[i]: #Evalua que todos los valores de CUR, sean iguales, no se carga bien por ser un valor mtext
             #   band_cur.append('0')
            #else:
             #   band_cur.append('-1')

            if car_partida[i-1] == car_partida[i]: #Evalua que todos los valores de partida , sean iguales
                band_partida.append('0')
            else:
                band_partida.append('-1')

            if car_num_plano[i-1] == car_num_plano[i]: #Evalua que todos los valores de numero de plano, sean iguales
                band_num_plano.append('0')
            else:
                band_num_plano.append('-1')

            if car_tipo_plano[i-1] == car_tipo_plano[i]: #Evalua que todos los valores de numero de plano, sean iguales
                band_tipo_plano.append('0')
            else:
                band_tipo_plano.append('-1')

            if car_año_plano[i-1] == car_año_plano[i]: #Evalua que todos los valores de numero de plano, sean iguales
                band_año_plano.append('0')
            else:
                band_año_plano.append('-1')               

            if car_dif[i-1] == car_dif[i]: #Evalua que todos los valores de numero de plano, sean iguales
                band_dif.append('0')
            else:
                band_dif.append('-1')

    ##        if car_hoja[i-1] == car_hoja[i]: #Evalua que todos los valores de diferencia de superficie entre mensura y titulo, sean iguales
    ##            band_hoja.append('0')
    ##        else:
    ##            band_hoja.append('-1')

            if car_objeto[i-1] == car_objeto[i]: #Evalua que todos los valores de dobjeto de plano, sean iguales
                band_objeto.append('0')
            else:
                band_objeto.append('-1')
                
            #if car_agrim[i-1] == car_agrim[i]: #Evalua que todos los valores de nombre agrimensor, sean iguales, no se carga bien car_agrim por ser mtext
             #   band_agrim.append('0')
            #else:
             #   band_agrim.append('-1')   

            #if car_cuit[i-1] == car_cuit[i]: #Evalua que todos los valores de cuit, sean iguales, no se carga bien por ser 
             #   band_cuit.append('0')
            #else:
             #   band_cuit.append('-1')

            if car_mens[i-1] == car_mens[i]: #Evalua que todos los valores de Sup s/m, sean iguales
                band_mens.append('0')
            else:
                band_mens.append('-1')

            if car_tit[i-1] == car_tit[i]: #Evalua que todos los valores de Sup s/t, sean iguales
                band_tit.append('0')
            else:
                band_tit.append('-1')

            if car_tipo_dif[i-1] == car_tipo_dif[i]: #Evalua que todos los valores de dif balance, sean iguales
                band_tipo_dif.append('0')
            else:
                band_tipo_dif.append('-1')

        #consulta las banderas de os distintos valores buscando que se haya detectado una diferencia. Si hay diferencia tirra erroro sino se fija que los campos no esten vacios

        if (("-1" in band_circ) or ("-1" in band_sec) or ("-1" in  band_manz) or ("-1" in  band_parc) or
                   ("-1" in band_fecha_mens) or ("-1" in  band_partida) or ("-1" in band_tipo_dif)or ("-1" in  band_num_plano) or ("-1" in band_objeto) or ("-1" in band_mens) or ("-1" in band_tit) or ("-1" in band_dif)):
            
            validaciones2.loc[23,'Resultado']=-1
            validaciones2.loc[23,'Observacion']="Error: No se ingresaron los mismos datos en las caratulas insertas"
            validaciones2.loc[23,'Cetegoría']='Caratula'
            
        else:

            for i in range (len(bloque_caratula)):

                if car_circ[i]==None:
                    band_vac_circ.append("-1")
                else:
                    band_vac_circ.append("0")

                if car_sec[i]==None:
                    band_vac_sec.append("-1")
                else:
                    band_vac_sec.append("0")

                if car_manz[i]==None:
                    band_vac_manz.append("-1")
                else:
                    band_vac_manz.append("0")

                if car_parc[i]==None:
                    band_vac_parc.append("-1")
                else:
                    band_vac_parc.append("0")
                    
                #if car_direc[i]==None:
                 #   band_vac_direc.append("-1")
                #else:
                 #   band_vac_direc.append("0")

                #if car_prop[i]==None:
                 #   band_vac_prop.append("-1")
                #else:
                 #   band_vac_prop.append("0")

                #if car_dominio[i]==None:
                 #   band_vac_dominio.append("-1")
                #else:
                 #   band_vac_dominio.append("0")

                if car_fecha_mens[i]==None:
                    band_vac_fecha_mens.append("-1")
                else:
                    band_vac_fecha_mens.append("0")

                #if car_cur[i]==None:
                 #   band_vac_cur.append("-1")
                #else:
                 #   band_vac_cur.append("0")

                if car_partida[i]==None:
                    band_vac_partida.append("-1")
                else:
                    band_vac_partida.append("0")

                if car_num_plano[i]==None:
                    band_vac_num_plano.append("-1")
                else:
                    band_vac_num_plano.append("0")

                if car_tipo_plano[i]==None:
                    band_vac_tipo_plano.append("-1")
                else:
                    band_vac_tipo_plano.append("0")

                if car_año_plano[i]==None:
                    band_vac_año_plano.append("-1")
                else:
                    band_vac_año_plano.append("0")

                if car_mens[i]==None:
                    band_vac_mens.append("-1")
                else:
                    band_vac_mens.append("0")

                if car_tit[i]==None:
                    band_vac_tit.append("-1")
                else:
                    band_vac_tit.append("0")

                if car_dif[i]==None:
                    band_vac_dif.append("-1")
                else:
                    band_vac_dif.append("0")

                if car_tipo_dif[i]==None:
                    band_vac_tipo_dif.append("-1")
                else:
                    band_vac_tipo_dif.append("0") 

            if (("-1" in band_vac_circ) or ("-1" in band_vac_sec) or ("-1" in band_vac_manz) or ("-1" in band_vac_parc) or ("-1" in band_vac_fecha_mens) or ("-1" in band_vac_tipo_dif) 
                or ("-1" in band_vac_partida) or ("-1" in band_vac_mens) or ("-1" in band_vac_tit) or ("-1" in band_vac_dif) or ("-1" in band_vac_num_plano)):

                
                validaciones2.loc[23,'Resultado']=-1
                validaciones2.loc[23,'Observacion']="Error: Existen campos vacios en las caratulas insertas"
                validaciones2.loc[23,'Cetegoría']='Caratula'

            else:
                validaciones2.loc[23,'Resultado']=0
                validaciones2.loc[23,'Observacion']="OK: Los campos de las caratulas se encuentran completos"
                validaciones2.loc[23,'Cetegoría']='Caratula'


                patron_circ = re.compile('^[0-9]{1,3}$')
                patron_sec = re.compile('^[0-9]{3}$')
                patron_maz_parc = re.compile('(^([0-9]{3})|([0-9]{3}[a-z]{1}))|(\D{3,}(\.)*(Plano|PLANO|plano)\D{0,})$')
                patron_fecha_mens = re.compile('^([0-9]{2}/[0-9]{2}/[0-9]{4})|([0-9]{2}-[0-9]{2}-[0-9]{4})$')
                patron_balance = re.compile('^[0-9]{1,}\.[0-9]{1,}$')
                patron_plano = re.compile('^(MH-|M-|MS-)[0-9]{4}-[0-9]{4}$')

                band_pat_circ = list()
                band_pat_sec = list()
                band_pat_manz = list()
                band_pat_parc = list()
                band_pat_fecha_mens = list()
                band_pat_plano = list()

                band_pat_mens = list()
                band_pat_tit = list()
                band_pat_dif = list()

                for i in range(len(bloque_caratula)):
                    band_pat_circ.append(patron_circ.match(car_circ[i]))#recolecta como salio la validacion en las distintas caratulas para el campo circunscripión
                    band_pat_sec.append(patron_sec.match(car_sec[i]))#recolecta como salio la validacion en las distintas caratulas para el campo sección
                    band_pat_manz.append(patron_maz_parc.match(car_manz[i]))#recolecta como salio la validacion en las distintas caratulas para el campo manzana
                    band_pat_parc.append(patron_maz_parc.match(car_parc[i]))          #recolecta como salio la validacion en las distintas caratulas para el campo parcela
                    band_pat_fecha_mens.append(patron_fecha_mens.match(car_fecha_mens[i])) #recolecta como salio la validacion en las distintas caratulas para el campo feha mensura 
                    band_pat_plano.append(patron_plano.match(car_num_plano[i]))
                    band_pat_mens.append(patron_balance.match(car_mens[i]))
                    band_pat_tit.append(patron_balance.match(car_tit[i]))
                    band_pat_tit.append(patron_balance.match(car_dif[i]))

                    print("banderas patrones")
                    print(band_pat_circ)
                    print(band_pat_sec)
                    print(band_pat_manz)
                    print(band_pat_parc)
                    print(band_pat_fecha_mens)
                    print(band_pat_plano)

                    print("patron balance")
                    print(band_pat_mens)
                                            
                if None in (band_pat_circ) or (None in band_pat_sec) or (None in band_pat_manz) or (None in band_pat_parc) or (None in band_pat_fecha_mens) or (None in band_pat_plano):
                    validaciones2.loc[24,'Resultado']=-1
                    validaciones2.loc[24,'Observacion']="Error: Alguno de los campos Circ, Sec, Manz, Parc, fecha de mensura no se han completado correctamente"
                    validaciones2.loc[24,'Cetegoría']='Caratula'
                else:
                    validaciones2.loc[24,'Resultado']=0
                    validaciones2.loc[24,'Observacion']="OK: Los campos Circ, Sec, Manz, Parc, fecha de mensura se han completado correctamente"
                    validaciones2.loc[24,'Cetegoría']='Caratula'

                if None in (band_pat_mens) or (None in band_pat_tit) or (None in band_pat_dif):
                    validaciones2.loc[25,'Resultado']=-1
                    validaciones2.loc[25,'Observacion']='Error: Alguno de los valores de superficies del balance no son numericos o se utilizó un separador distinto de "."'
                    validaciones2.loc[25,'Cetegoría']='Caratula'
                else:
                    validaciones2.loc[25,'Resultado']=0
                    validaciones2.loc[25,'Observacion']="OK: Los campos del Balance de superficie se completaron correctamente"
                    validaciones2.loc[25,'Cetegoría']='Caratula'

                    band_dif_sup=list()
                    band_men_tit = list()


                    for i in range (len(car_mens)):
                        sup_men = car_mens[i]
                        
                        if abs(float(sup_mens_poly) - float(sup_men)) <= 0.01: #evalua que la supericie que puso como sup. de mensura en el balance de la primer caratula no difiera mas de 1cm2 de la suma de todos los poligonos de parcela y cesiones
                            band_dif_sup.append('0')
                        else:
                            band_dif_sup.append('-1')

                    if '-1' in band_dif_sup:
                        validaciones2.loc[26,'Resultado']=-1
                        validaciones2.loc[26,'Observacion']='Error: La superficie según mensura del balance de alguna de las caratulas no coincide con la suma de las supercicies de los poligonos Parcelas y Cesiones o no se ha podido validar por no ser un número'
                        validaciones2.loc[26,'Cetegoría']='Caratula'
                    else:
                        validaciones2.loc[26,'Resultado']=0
                        validaciones2.loc[26,'Observacion']='OK: La superficie según mensura del balance coincide con la superficie de los polignos los poligonos Parcelas y Cesiones'
                        validaciones2.loc[26,'Cetegoría']='Caratula'

                    for i in range (len(car_dif)):

                        print("diferencia balance caratula")
                        print(car_dif[i])
                        print("deferencia mensura titulo caratula")
                        print(float(car_mens[i])-float(car_tit[i]))

                        if abs(float(car_dif[i]) - abs((float(car_mens[i]) - float(car_tit[i])))) <= 0.01:
                            band_men_tit.append("0")
                        else:
                            band_men_tit.append("-1")
                        
                       
                    if "-1" in band_men_tit:
                        validaciones2.loc[27,'Resultado']=-3
                        validaciones2.loc[27,'Observacion']="ERROR: En la o alguna de las caratulas no coincide el valor indicado con la diferencia real entre las superficies según Mensura y título/plano"
                        validaciones2.loc[27,'Cetegoría']='Caratula'
                    else:
                        validaciones2.loc[27,'Resultado']=0
                        validaciones2.loc[27,'Observacion']="OK: El valor de la diferencia de superficie entre mensura y titulo se indicó correctamente en los valances de la/s caratula/s"
                        validaciones2.loc[27,'Cetegoría']='Caratula'


                    #<----- Valida que se haya colocado Diferenci en Menos Más o Excedente segúh corresponda------>#

                    band_excedente = list()
                    band_dif_mas = list()
                    band_dif_menos = list()
                    band_dif = list()

                    for i in range (len(car_mens)):
                        if (len(car_mens[i])>0) and (len(car_tit[i])>0):
                            if (float(car_mens[i]) - float(car_tit[i])) >= (0.05 * float(car_tit[i])):
                                if ("EXCEDENTE" in car_tipo_dif[i]) or ("Excedente" in car_tipo_dif[i]) or ("excedente" in car_tipo_dif[i]):
                                    band_excedente.append("0")
                                else:
                                    band_excedente.append("-1")
                            elif ((float(car_mens[i]) - float(car_tit[i])>0)) and ((float(car_mens[i]) - float(car_tit[i]))<(0.05 * float(car_tit[i]))):
                                if ("MAS" in car_tipo_dif[i]) or ("Más" in car_tipo_dif[i]) or ("Mas" in car_tipo_dif[i]) or ("mas" in car_tipo_dif[i]):
                                    band_dif_mas.append("0")
                                else:
                                    band_dif_mas.append("-1")
                            elif (float(car_mens[i]) - float(car_tit[i])<0):
                                if ("Menos" in car_tipo_dif[i]) or ("menos" in car_tipo_dif[i]) or ("MENOS" in car_tipo_dif[i]):
                                    band_dif_menos.append("0")
                                else:
                                    band_dif_menos.append("-1")
                            elif ((float(car_mens[i]) - float(car_tit[i])==0)):
                                if ("Dif." in car_tipo_dif[i]) or ("Diferencia" in car_tipo_dif[i]) or ("DIFERENCIA" in car_tipo_dif[i]) or ("DIF." in car_tipo_dif[i]):
                                    band_dif.append("0")
                                else:
                                    band_dif.append("-1")
                        else:
                            validaciones2.loc[28,'Resultado']=-1
                            validaciones2.loc[28,'Observacion']="ERROR: Se han consignado valores negativos en la Sup. S/ Mensura o Sup S/ Tit."
                            validaciones2.loc[28,'Cetegoría']='Caratula'
                        
                    if ("-1" in band_excedente) or ("-1" in band_dif_menos) or ("-1" in band_dif_mas) or ("-1" in band_dif):
                        validaciones2.loc[28,'Resultado']=-1
                        validaciones2.loc[28,'Observacion']="ERROR: No coincide el Tipo de diferencia del balance (Diferencia, Diferencia en más, Diferencia en Menos, Excedente), con el valor de la dif. entre titulo y mensura del balance"
                        validaciones2.loc[28,'Cetegoría']='Caratula'
                    else:
                        validaciones2.loc[28,'Resultado']=0
                        validaciones2.loc[28,'Observacion']="OK: El tipo de diferencia declarada en el balance coincide con la diferencia de valor entre Mensura y Título"
                        validaciones2.loc[28,'Cetegoría']='Caratula'

                        #VALIDAR QUE LA SUPERF DEL BALANCE SEA IGUAL A LAS DE MENSURAS

    #verificar que los datos de los distintos atributos no esten vacios si estan vacios hacer alerta sino seguir verificando que los datos sean coherentes

   #verificar que los datos de los distintos atributos no esten vacios si estan vacios hacer alerta sino seguir verificando que los datos sean coherentes                
    else:
        for i in range (len(bloque_caratula)):

            if car_circ[i]==None:
                band_vac_circ.append("-1")
            else:
                band_vac_circ.append("0")

            if car_sec[i]==None:
                band_vac_sec.append("-1")
            else:
                band_vac_sec.append("0")

            if car_manz[i]==None:
                band_vac_manz.append("-1")
            else:
                band_vac_manz.append("0")

            if car_parc[i]==None:
                band_vac_parc.append("-1")
            else:
                band_vac_parc.append("0")
                
##            if car_direc[i]==None:
##                band_vac_direc.append("-1")
##            else:
##                band_vac_direc.append("0")
##
##            if car_prop[i]==None:
##                band_vac_prop.append("-1")
##            else:
##                band_vac_prop.append("0")

##            if car_dominio[i]==None:
##                band_vac_dominio.append("-1")
##            else:
##                band_vac_dominio.append("0")

            if car_fecha_mens[i]==None:
                band_vac_fecha_mens.append("-1")
            else:
                band_vac_fecha_mens.append("0")

##            if car_cur[i]==None:
##                band_vac_cur.append("-1")
##            else:
##                band_vac_cur.append("0")

            if car_partida[i]==None:
                band_vac_partida.append("-1")
            else:
                band_vac_partida.append("0")

            if car_num_plano[i]==None:
                band_vac_num_plano.append("-1")
            else:
                band_vac_num_plano.append("0")

            if car_tipo_plano[i]==None:
                band_vac_tipo_plano.append("-1")
            else:
                band_vac_tipo_plano.append("0")

            if car_año_plano[i]==None:
                band_vac_año_plano.append("-1")
            else:
                band_vac_año_plano.append("0")

            if car_mens[i]==None:
                band_vac_mens.append("-1")
            else:
                band_vac_mens.append("0")

            if car_tit[i]==None:
                band_vac_tit.append("-1")
            else:
                band_vac_tit.append("0")

            if car_dif[i]==None:
                band_vac_dif.append("-1")
            else:
                band_vac_dif.append("0")

            if car_tipo_dif[i]==None:
                band_vac_tipo_dif.append("-1")
            else:
                band_vac_tipo_dif.append("0") 

        if (("-1" in band_vac_circ) or ("-1" in band_vac_sec) or ("-1" in band_vac_manz) or ("-1" in band_vac_parc) or 
                    ("-1" in band_vac_fecha_mens) or ("-1" in band_vac_mens) or ("-1" in band_vac_tipo_dif) or ("-1" in band_vac_tit) or ("-1" in band_vac_dif) or ("-1" in band_vac_partida) or ("-1" in band_vac_num_plano)):
            
            validaciones2.loc[23,'Resultado']=-1
            validaciones2.loc[23,'Observacion']="Error: Existen campos vacios en las caratulas insertas"
            validaciones2.loc[23,'Cetegoría']='Caratula'

        else:
            validaciones2.loc[23,'Resultado']=0
            validaciones2.loc[23,'Observacion']="OK: Los campos de las caratulas se encuentran completos"
            validaciones2.loc[23,'Cetegoría']='Caratula'

            #Genrea los patrones para comparar los campos cargados con lo que se espera#

            patron_circ = re.compile('^[0-9]{1,3}$')
            patron_sec = re.compile('^[0-9]{3}$')
            patron_maz_parc = re.compile('(^([0-9]{3})|([0-9]{3}[a-z]{1}))|(\D{3,}(\.)*(Plano|PLANO|plano)\D{0,})$')
            patron_fecha_mens = re.compile('^([0-9]{2}/[0-9]{2}/[0-9]{4})|([0-9]{2}-[0-9]{2}-[0-9]{4})$')
            patron_balance = re.compile('^[0-9]{1,}\.[0-9]{1,}$')
            patron_plano = re.compile('^(MH-|M-|MS-)[0-9]{4}-[0-9]{4}$')

            #Genrea los patrones para comparar los campos cargados con lo que se espera#

            #Genera las banderas para guardar el resultado de la validacion de los patrones#

            band_pat_circ = list()
            band_pat_sec = list()
            band_pat_manz = list()
            band_pat_parc = list()
            band_pat_fecha_mens = list()
            band_pat_plano = list()
            band_pat_mens = list()
            band_pat_tit = list()
            band_pat_dif = list()

            #Genera las banderas para guardar el resultado de la validacion de los patrones#

            for i in range (len(bloque_caratula)):
                band_pat_circ.append(patron_circ.match(car_circ[i]))#recolecta como salio la validacion en las distintas caratulas para el campo circunscripión
                band_pat_sec.append(patron_sec.match(car_sec[i]))#recolecta como salio la validacion en las distintas caratulas para el campo sección
                band_pat_manz.append(patron_maz_parc.match(car_manz[i]))#recolecta como salio la validacion en las distintas caratulas para el campo manzana
                band_pat_parc.append(patron_maz_parc.match(car_parc[i]))          #recolecta como salio la validacion en las distintas caratulas para el campo parcela
                band_pat_fecha_mens.append(patron_fecha_mens.match(car_fecha_mens[i])) #recolecta como salio la validacion en las distintas caratulas para el campo feha mensura 
                band_pat_plano.append(patron_plano.match(car_num_plano[i]))
                band_pat_mens.append(patron_balance.match(car_mens[i]))
                band_pat_tit.append(patron_balance.match(car_tit[i]))
                band_pat_dif.append(patron_balance.match(car_dif[i]))

                print("banderas patrones")
                print(band_pat_circ)
                print(band_pat_sec)
                print(band_pat_manz)
                print(band_pat_parc)
                print(band_pat_fecha_mens)
                print(band_pat_plano)

                print("patrones balance")
                print(band_pat_mens)
                print(band_pat_tit)
                print(band_pat_dif)
            
            if None in (band_pat_circ) or (None in band_pat_sec) or (None in band_pat_manz) or (None in band_pat_parc) or (None in band_pat_fecha_mens) or (None in band_pat_plano):
                validaciones2.loc[24,'Resultado']=-1
                validaciones2.loc[24,'Observacion']="Error: Alguno de los campos Circ, Sec, Manz, Parc, fecha de mensura no se han completado correctamente"
                validaciones2.loc[24,'Cetegoría']='Caratula'
            else:
                validaciones2.loc[24,'Resultado']=0
                validaciones2.loc[24,'Observacion']="OK: Los campos Circ, Sec, Manz, Parc, fecha de mensura se han completado correctamente"
                validaciones2.loc[24,'Cetegoría']='Caratula'

            if None in (band_pat_mens) or (None in band_pat_tit) or (None in band_pat_dif):
                validaciones2.loc[25,'Resultado']=-1
                validaciones2.loc[25,'Observacion']='Error: Alguno de los campos del balance de superficie no son numericos o se utilizó un separador distinto de "."'
                validaciones2.loc[25,'Cetegoría']='Caratula'

                validaciones2.loc[26,'Resultado']=99
                validaciones2.loc[26,'Observacion']='Error: No se puede validar el balance porque los campos completados no son numericos o se utilizó un separador distinto de "."'
                validaciones2.loc[26,'Cetegoría']='Caratula'

                validaciones2.loc[27,'Resultado']=99
                validaciones2.loc[27,'Observacion']='Error: No se puede validar el balance porque los campos completados no son numericos o se utilizó un separador distinto de "."'
                validaciones2.loc[27,'Cetegoría']='Caratula'

                validaciones2.loc[28,'Resultado']=99
                validaciones2.loc[28,'Observacion']='Error: No se puede validar el balance porque los campos completados no son numericos o se utilizó un separador distinto de "."'
                validaciones2.loc[28,'Cetegoría']='Caratula'
            else:
                validaciones2.loc[25,'Resultado']=0
                validaciones2.loc[25,'Observacion']="OK: Los campos del Balance de superficie se completaron correctamente"
                validaciones2.loc[25,'Cetegoría']='Caratula'

                band_dif_sup=list()
                band_men_tit = list()


                for i in range (len(car_mens)):
                    sup_men = car_mens[i]
                           
                    if abs(float(sup_mens_poly) - float(sup_men)) <= 0.01: #evalua que la supericie que puso como sup. de mensura en el balance de la primer caratula no difiera mas de 1cm2 de la suma de todos los poligonos de parcela y cesiones
                        band_dif_sup.append('0')
                    else:
                        band_dif_sup.append('-1')

                         

                if '-1' in band_dif_sup:
                    validaciones2.loc[26,'Resultado']=-1
                    validaciones2.loc[26,'Observacion']='Error: La superficie según mensura del balance de alguna de las caratulas no coincide con la suma de las supercicies de los poligonos Parcelas y Cesiones o no se ha podido validar por no ser un nmero'
                    validaciones2.loc[26,'Cetegoría']='Caratula'
                else:
                    validaciones2.loc[26,'Resultado']=0
                    validaciones2.loc[26,'Observacion']='OK: La superficie según mensura del balance coincide con la superficie de los polignos los poligonos Parcelas y Cesiones'
                    validaciones2.loc[26,'Cetegoría']='Caratula'

                for i in range (len(car_dif)):
                    
                    if abs(float(car_dif[i]) - abs((float(car_mens[i]) - float(car_tit[i]))))<=0.01:
                        band_men_tit.append("0")
                    else:
                        band_men_tit.append("-1")
                   
                if "-1" in band_men_tit:
                    validaciones2.loc[27,'Resultado']=-3
                    validaciones2.loc[27,'Observacion']="ERROR: En la o alguna de las caratulas no coincide el valor indicado con la diferencia real entre las superficies según Mensura y título/plano"
                    validaciones2.loc[27,'Cetegoría']='Caratula'
                else:
                    validaciones2.loc[27,'Resultado']=0
                    validaciones2.loc[27,'Observacion']="OK: El valor de la diferencia de superficie entre mensura y titulo se indicó correctamente en los valances de la/s caratula/s"
                    validaciones2.loc[27,'Cetegoría']='Caratula'


                #<----- Valida que se haya colocado Diferenci en Menos Más o Excedente segúh corresponda------>#

                band_excedente = list()
                band_dif_mas = list()
                band_dif_menos = list()
                band_dif=list()

                for i in range (len(car_mens)):
                    if (len(car_mens[i])>0) and (len(car_tit[i])>0):
                        if (float(car_mens[i]) - float(car_tit[i])) >= (0.05 * float(car_tit[i])):
                            if ("EXCEDENTE" in car_tipo_dif[i]) or ("Excedente" in car_tipo_dif[i]) or ("excedente" in car_tipo_dif[i]):
                                band_excedente.append("0")
                            else:
                                band_excedente.append("-1")
                        elif ((float(car_mens[i]) - float(car_tit[i])>=0)) and ((float(car_mens[i]) - float(car_tit[i]))<(0.05 * float(car_tit[i]))):
                            if ("MAS" in car_tipo_dif[i]) or ("Más" in car_tipo_dif[i]) or ("Mas" in car_tipo_dif[i]) or ("mas" in car_tipo_dif[i]):
                                band_dif_mas.append("0")
                            else:
                                band_dif_mas.append("-1")
                        elif (float(car_mens[i]) - float(car_tit[i])<0):
                            if ("Menos" in car_tipo_dif[i]) or ("menos" in car_tipo_dif[i]) or ("MENOS" in car_tipo_dif[i]):
                                band_dif_menos.append("0")
                            else:
                                band_dif_menos.append("-1")
                        elif ((float(car_mens[i]) - float(car_tit[i])==0)):
                            if ("Dif." in car_tipo_dif[i]) or ("Diferencia" in car_tipo_dif[i]) or ("DIFERENCIA" in car_tipo_dif[i]) or ("DIF." in car_tipo_dif[i]):
                                band_dif.append("0")
                            else:
                                band_dif.append("-1")
                    else:
                        validaciones2.loc[28,'Resultado']=-1
                        validaciones2.loc[28,'Observacion']="ERROR: Se han consignado valores negativos en la Sup. S/ Mensura o Sup S/ Tit."
                        validaciones2.loc[28,'Cetegoría']='Caratula'
                    
                if ("-1" in band_excedente) or ("-1" in band_dif_menos) or ("-1" in band_dif_mas):
                    validaciones2.loc[28,'Resultado']=-1
                    validaciones2.loc[28,'Observacion']="ERROR: No coincide el Tipo de diferencia del balance (Diferencia, Diferencia en más, Diferencia en Menos, Excedente), con el valor de la dif. entre titulo y mensura del balance"
                    validaciones2.loc[28,'Cetegoría']='Caratula'
                else:
                    validaciones2.loc[28,'Resultado']=0
                    validaciones2.loc[28,'Observacion']="OK: El tipo de diferencia declarada en el balance coincide con la diferencia de valor entre Mensura y Título"
                    validaciones2.loc[28,'Cetegoría']='Caratula'
                    
                #<----- Valida que se haya colocado Diferenci en Menos Más o Excedente segúh corresponda------>#

        #verificar que los datos de los distintos atributos no esten vacios si estan vacios hacer alerta sino seguir verificando que los datos sean coherentes

        
        #FIN validar que la caratula tenga los atributos completos y que que sean coherentes excepto el balance que se valida mas adelante


#--- 2.6 FIN Validación de Caratula --#

#--- INICIO Validación Layout-----#

def chequeo_layout():

    global layout
    global parcelas_poly_close
    global cesion_poly_close
    global excedentes_poly_close

    global car_manz
    global car_parc

    #1- INICIO Validar que el layout tenga las unidades que queremos


    
    #1- FIN Validar que el layout tenga las unidades que queremos
        
    #2- INICIO Validar que el layout tenga la medida que indica las normas

        
    #2- FIN Validar que el layout tenga la medida que indica las normas

    #3- INICIO Validar que si en la caratula dice Ver Int. plano en parcela busque inserto el bloque tabla de "parcelas"
    tabla_parc = doc.query('INSERT[name=="TBL_NOMENCLATURA_PARTIDA"]')

    if (("plano" in car_parc) or ("Plano" in car_parc) or ("PLANO" in car_parc)
        or ("Ver" in car_parc) or ("ver" in car_parc)or ("VER" in car_parc)) or (("plano" in car_manz) or ("Plano" in car_manz) or ("PLANO" in car_manz)
        or ("Ver" in car_manz) or ("ver" in car_manz)or ("VER" in car_manz)):

        if len(tabla_parc)>0:
            validaciones2.loc[29,'Resultado']=0
            validaciones2.loc[29,'Observacion']="OK: se insertó el bloque de nomenclatura de parcelas"
            validaciones2.loc[29,'Cetegoría']='Caratula'
            #validar tabla_parc que este completada correctamente
        else:
            if (("plano" in car_parc) or ("Plano" in car_parc) or ("PLANO" in car_parc)
                or ("Ver" in car_parc) or ("ver" in car_parc)or ("VER" in car_parc)):

                if len(tabla_parc)>0:
                    validaciones2.loc[29,'Resultado']=0
                    validaciones2.loc[29,'Observacion']="OK: se insertó el bloque de nomenclatura de parcelas"
                    validaciones2.loc[29,'Cetegoría']='Caratula'
                    #validar tabla_parc que este completada correctamente
                else:
                    validaciones2.loc[29,'Resultado']=-1
                    validaciones2.loc[29,'Observacion']="ERROR: No se insertó el bloque de nomenclatura de parcelas"
                    validaciones2.loc[29,'Cetegoría']='Caratula'
    else:
        validaciones2.loc[29,'Resultado']=99
        validaciones2.loc[29,'Observacion']='OK: No corresponde validar Tabla de nomenclaturas por no haberse detectado "Ver Plano" en la caratula'
        validaciones2.loc[29,'Cetegoría']='Layout'
        
                    


    #3- FIN alidar que si en la caratula dice Ver Int. plano en parcela busque inserto el bloque tabla de "parcelas"

    #4- INICIO validar que si tiene cesión, o hay mas de una parcela, o hay excedente busque que este inserto el bloque tabla "Detalle de Superficie según mensura"

    detalle_titulo = doc.query('INSERT[name=="TBL_DETALLE_SUP_TITULO"]')
    detalle_mensura = doc.query('INSERT[name=="TBL_DETALLE_SUP_MENSURA"]')

    if (len(cesion_poly_close)>0) or (len(excedentes_poly_close)>0) or (len(parcelas_poly_close)>1):

        if len(detalle_mensura)>0:
            validaciones2.loc[30,'Resultado']=0
            validaciones2.loc[30,'Observacion']='OK: Se insertó el bloque "TBL_DETALLE_SUP_MENSURA"'
            validaciones2.loc[30,'Cetegoría']='Caratula'
        else:
            validaciones2.loc[30,'Resultado']=-1
            validaciones2.loc[30,'Observacion']='ERROR: No se insertó el bloque "TBL_DETALLE_SUP_MENSURA'
            validaciones2.loc[30,'Cetegoría']='Caratula'
    else:
        validaciones2.loc[30,'Resultado']=99
        validaciones2.loc[30,'Observacion']="OK: No corresponde validar Tabla de Superficies por no haberse detectado poligonos de excedente, cesiones o varias parcelas"
        validaciones2.loc[30,'Cetegoría']='Layout'

    #4- FIN validar que si tiene cesión, o hay mas de una parcela, o hay excedente busque que este inserto el bloque tabla "Detalle de Superficie según mensura"

    #5- INICIO validar que los viewports de los layouts esten en la misma escala que la declarada

##    viewports = dict() #crea eñ diccionario de viewporst donde se almacenaran todos los viewporst de cada layout
##    view_lay= list() #crea la lista de viewports donde se almacenaran los viewporst de cada layout
##
##    for lay in layout: #completa el diccionario para cada layout la lista de viewporst asociados
##        view_lay=lay.viewport()
##        viewports.setdefault['layout',view_lay]
##    view_scale=list()
##    for i in viewports.keys(): #en una lista va agregando todos los viewporsts
##        for j in i:
##            view_scale.append(j)
##    
##
##    for i in range(len(view_scale):
        
                   
    
        

    #5- FIN validar que los viewports de los layouts esten en la misma escala que la declarada 



#--- FIN Validación Layout-----#

                    

#--- 2.7 Resumen --#

    
    

#--- 2.7 Resumen --#
                    


#--- 2 FIN Validación del Archivo DXF ---#

 

Boton_Chequear_layers= Button(marco1, text="Procesar DXF", command=Procesar_Archivo).pack()




raiz.mainloop()
