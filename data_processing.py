
import pickle
import pandas as pd 


file = open("seguimiento_aplicaciones.pkl",'rb')
object_file = pickle.load(file)
file.close()
fechas_pendientes = pd.concat(object_file.values()).query('fecha_ejecucion in [@pd.NaT]')[["aplicacion","bloque","fechas"]]
fechas_pendientes["lote"] = 1
fechas_pendientes=fechas_pendientes[["aplicacion","lote","bloque","fechas"]]
fechas_pendientes["retraso"]=pd.Timestamp.today() - fechas_pendientes["fechas"]
fechas_pendientes["retraso"] = fechas_pendientes.retraso.dt.days
fechas_pendientes.query("retraso>0",inplace=True)
fechas_pendientes.sort_values(by="retraso",ascending=False,inplace=True)
fechas_pendientes["fechas"] = fechas_pendientes.fechas.dt.date
fechas_pendientes.rename(columns={"fechas":"fecha prevista aplicación","retraso":"dias de retraso"},inplace= True)
fechas_pendientes["comentarios"] = ""

lista_descartes = ["Visita previa 9","Visita previa 10","Visita previa 10"]
fechas_pendientes.query("aplicacion not in @lista_descartes",inplace=True)

fechas_pendientes.drop_duplicates(subset=["aplicacion"],inplace=True,ignore_index=True)
fechas_pendientes.drop(["bloque"],axis=1,inplace=True)


historia_bloques = pd.read_csv("historico_estados_blocks.csv",delimiter=";",parse_dates=["primera","produccion_semilla","segunda","produccion_semilla2","barrido"])
historia_bloques.drop(["dif_fechas_pc_a_semillero","dif_fechas_semillero_a_sc","dif_fechas_sc_a_semillero","dif_fechas_semillero2_a_barrido"],axis=1,inplace=True)
historia_bloques.rename(columns={"bloque":"id"},inplace=True)
historia_bloques["lote"]=historia_bloques.id.str.slice(start=0,stop=2)
historia_bloques["bloque"]=historia_bloques.id.str.slice(start=2,stop=4)
historia_bloques["año"]=historia_bloques.id.str.slice(start=4,stop=6)
historia_bloques.query("año!=''",inplace=True)
historia_bloques["año"]=historia_bloques["año"].astype(int)
columnas_de_fecha = ['primera', 'produccion_semilla', 'segunda', 'produccion_semilla2',"barrido"]
for columna in columnas_de_fecha:
    historia_bloques[columna]=historia_bloques[columna].dt.date
historia_bloques = historia_bloques[['lote', 'bloque', 'año', 'primera', 'produccion_semilla','segunda','produccion_semilla2','barrido']]
# historia_bloques = pd.read_excel("historia_por_bloque.xlsx")
# historia_bloques.columns=["id","lote","año","bloque","siembra","inducción PC","inducción SC","grupo","fecha apl PC","fecha apl SM1","fecha apl SC","fecha apl SM2","barrido"]
# historia_bloques["fecha apl PC"] = historia_bloques["fecha apl PC"].dt.date
# historia_bloques["fecha apl SM1"] = historia_bloques["fecha apl SM1"].dt.date
# historia_bloques["fecha apl SC"] = historia_bloques["fecha apl SC"].dt.date
# historia_bloques["fecha apl SM2"] = historia_bloques["fecha apl SM2"].dt.date
# historia_bloques["barrido"] = historia_bloques["barrido"].dt.date
# historia_bloques["siembra"]  = pd.to_datetime(historia_bloques["siembra"],infer_datetime_format=True).dt.date
# historia_bloques["inducción PC"]  = pd.to_datetime(historia_bloques["inducción PC"],infer_datetime_format=True).dt.date
# historia_bloques["inducción SC"]  = pd.to_datetime(historia_bloques["inducción SC"],infer_datetime_format=True).dt.date
#Reordenar columnas