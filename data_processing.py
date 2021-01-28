
from numpy.lib.shape_base import column_stack
import pandas as pd 
import numpy as np
from datetime import datetime
from datetime import timedelta  
import locale 
import psycopg2
import sqlalchemy
import database_queries as query
from functools import reduce
from sqlalchemy import event
import plotly.express as px
import sys
from pandas.api.types import is_datetime64_any_dtype as is_datetime

locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

#Conexión PPC remota
try:
    connection = psycopg2.connect(user="postgres",
                                    password="Guapa.2020*",
                                    host="35.237.147.235",
                                    port="5432",
                                    database='ppc',
                                    sslmode='verify-ca',
                                    sslrootcert= "gcp postgres/server-ca.pem",
                                    sslcert = "gcp postgres/client-cert.pem",
                                    sslkey = "gcp postgres/client-key.pem")

    cursor = connection.cursor()

except Exception as e:
    print(e)
    print("Conexión fallida por red")


#######################
### Cargue archivos temporales de excel
#######################
categorias_insumos = pd.read_excel("relacion_insumos_principales_categorias.xlsx",engine='openpyxl')
categorias_insumos.dropna(subset=["categorias_por_insumo"],inplace=True)

peso_planta = pd.read_excel("peso_planta.xlsx",dtype={"bloque":str},engine='openpyxl')
peso_planta.sort_values(by=["bloque","edad"],inplace=True)

calendario_aplicaciones = pd.read_excel("calendario_aplicaciones.xlsx")
calendario_aplicaciones =calendario_aplicaciones[calendario_aplicaciones.aplicacion.str.contains('Foliar')]


#####
# Listado de grupos de siembra
####

#Extraer bloques y años de la tabla blocks:
try:
    lotes_historia = pd.read_sql_query(query.lotes_historia ,connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()

## Extraer información grupos de siembra
try:
    grupossiembra = pd.read_sql_query(query.grupossiembra,connection)
    
except Exception as e:

    print("hubo un error", e)
    connection.rollback()

df_grupos_siembra = grupossiembra[["codigo","descripcion"]]

## Extraer información de fórmulas
try:
    df_formulas = pd.read_sql_query(query.df_formulas,connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()


#############
# Guardar en memoria aplicaciones del GS actual Y resumen para no repetir query
#############

aplicaciones_gs_actual = pd.DataFrame(columns=["Seleccione","bloque"])
#resumen_gs_actual es un df que se usa por ahora solo para guardar la fecha de siembra
resumen_gs_actual = pd.DataFrame(columns=["Seleccione","bloque"])



#######################
## MÉTODOS ##############
#####################
########################################

#######################
## devuelve información de estados de los bloques de un lote
#####################

def retorna_info_estados_bloques(lote):
    df_resultado = pd.DataFrame(columns=["Seleccione","lote"])
    try:
        historia_bloques = pd.read_sql_query(query.historia_bloques,con = connection, params=[lote])
  
        return historia_bloques
    except Exception as e:

        print("hubo un error", e)
        connection.rollback()
        return df_resultado

#################
## Traer bloques de un grupo de forza específico
#################

def retorna_bloques_de_gs(gs):

  ## Extraer información tabla bloques:
  try:
      bloques = pd.read_sql_query(query.bloques_por_gs,con=connection,params=[str(gs)])

      lista_dicts_bloques = [{"label":row["descripcion"],"value":row["codigo"]} for _,row in bloques.iterrows()]
      return lista_dicts_bloques
  except Exception as e:

      print("hubo un error", e)
      connection.rollback()
  
def group_by_por_trimestre (df,trimestre):

                
    agg_dict = {
    "abs_menos_de_10" : pd.NamedAgg(column='diff', aggfunc=lambda ts: (ts <10).sum() ),
    "abs_mas_de_20": pd.NamedAgg(column='diff', aggfunc=lambda ts: (ts >20).sum()),
    "abs_conteo": pd.NamedAgg(column='apldate', aggfunc=lambda ts: ts.count()),
}
    resultado = df.groupby(["blocknumber"],dropna=False).agg(**agg_dict).reset_index().round(2)
    
    #Ajustar como proporciones del total ejecutado
    #Cuando salga división por 0: resultado["menos_de_10"].divide(resultado["conteo"], fill_value=0)
    resultado["menos_de_10"] = resultado["abs_menos_de_10"]/resultado["abs_conteo"]
    resultado["mas_de_20"] = resultado["abs_mas_de_20"]/resultado["abs_conteo"]
    resultado["conteo"] = resultado["abs_conteo"].apply(lambda x: 1 if x>6 else x/6 )
    resultado["q"+ str(trimestre)] =resultado.apply(lambda row: 0 if (row ["menos_de_10"]+row["mas_de_20"]>0.7) or (row["conteo"]<0.8) else 1 ,axis=1 )
    
    resultado["tooltip_q"+str(trimestre)] = resultado.apply(lambda row: f"aplicaciones con menos de 10 días de diferencia: {row['abs_menos_de_10']} de {row['abs_conteo']} \n aplicaciones con más de 20 días de diferencia {row['abs_mas_de_20']} de {row['abs_conteo']} \n  Aplicaciones faltantes vs plan: {6-row['abs_conteo']} ",axis=1)
    
    resultado.rename(columns={"abs_menos_de_10":"abs_menos_de_10_q" +str(trimestre),
    "abs_mas_de_20":"abs_mas_de_20_q" +str(trimestre),
    "abs_conteo":"abs_conteo_q" +str(trimestre)
    }, inplace=True)
    resultado.drop(["menos_de_10","mas_de_20","conteo"],axis=1,inplace=True)


    return resultado.rename(columns={"blocknumber":"bloque"}).round(2)



def crear_dfs_auxiliares_trimestrales(df):
    aplicaciones_q1 = df[(df['apldate']<= df['finiciosiembra'] + timedelta(weeks=12)) ]
    aplicaciones_q2 =df[(df['apldate'] > df['finiciosiembra'] + timedelta(weeks=12)) & (df['apldate'] <= df['finiciosiembra'] + timedelta(weeks=24)) ]
    aplicaciones_q3 =  df[(df['apldate'] > df['finiciosiembra'] + timedelta(weeks=24)) & (df['apldate'] <= df['finiciosiembra'] + timedelta(weeks=36)) ]
    aplicaciones_q4 = df[(df['apldate'] > df['finiciosiembra'] + timedelta(weeks=36))]

    df_q1 = group_by_por_trimestre(aplicaciones_q1,1)
    df_q2 = group_by_por_trimestre(aplicaciones_q2,2)
    df_q3 = group_by_por_trimestre(aplicaciones_q3,3)
    df_q4 = group_by_por_trimestre(aplicaciones_q4,4)

    data_frames = [df_q1, df_q2, df_q3,df_q4]

    df_merged = reduce(lambda  left,right: pd.merge(left,right,on=["bloque"],
                                            how='outer'), data_frames)
    return df_merged

def retorna_info_bloques_de_gs(gs):
    df_resultado = pd.DataFrame(columns=["no hay","aplicaciones"])
    try:
        bloques = pd.read_sql_query(query.bloques_detallado_por_gs,
        con = connection,params = [gs])
        
        #Referenciar df en memoria
        global aplicaciones_gs_actual
        global resumen_gs_actual

        if bloques.empty:
            print("no se encontraron bloques")
            aplicaciones_gs_actual = df_resultado
            resumen_gs_actual = df_resultado
            return df_resultado


        cedulas = pd.read_sql_query(query.cedulas,
        con = connection,params =[tuple(set(bloques.blocknumber.to_list()))])
        siembra = pd.read_sql_query(query.info_siembras_por_bloque,
        con = connection,params =[tuple(set(bloques.blocknumber.to_list()))])

        if cedulas.empty:
            print("Hay bloques pero no cédulas de aplicación asociadas a esos bloques")
            aplicaciones_gs_actual = df_resultado
            resumen_gs_actual = df_resultado
            return df_resultado

        formulas = pd.read_sql_query(query.aplicaciones, con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
        
        if formulas.empty:
            print("Hay cédulas pero no cruzan con las fórmulas")
            aplicaciones_gs_actual = df_resultado
            resumen_gs_actual = df_resultado
            return df_resultado

        #Unión de cédulas con bloques afectados por aplicación
        df_union_formulas_cedulas = formulas.merge(cedulas, how="inner",on="codigo")
        df_union_formulas_cedulas.sort_values(by=["blocknumber","apldate"],inplace=True)
        
        #Left join con siembra y blocks para traer información general del bloque
        df_union_formulas_cedulas_siembra = df_union_formulas_cedulas.merge(siembra,how="left",on="blocknumber")
        df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra.merge(bloques,how="left",on="blocknumber")

        #Filtro preforza
        df_union_formulas_cedulas_siembra_blocks.query("apldate<finduccion or finduccion!=finduccion",inplace=True)
        
        if df_union_formulas_cedulas_siembra_blocks.empty:
            print("Hay aplicaciones en algún bloque del GS pero no preforza")
            aplicaciones_gs_actual = df_resultado
            resumen_gs_actual = df_resultado
            return df_resultado

        #Filtro nutrición

        #Cruza las fórmulas preforza con sus insumos
        insumos_por_formulas_seleccionadas = pd.read_sql_query(query.insumos_por_formula,
        con = connection,params =[tuple(set(df_union_formulas_cedulas_siembra_blocks.formula.to_list()))])
        #Crea lista de las aplicaciones del GS que cruzan con la tabla de categorías
        insumos_por_formulas_seleccionadas = insumos_por_formulas_seleccionadas.merge(categorias_insumos,how="inner",on="insumo")
        categoria_por_aplicacion = insumos_por_formulas_seleccionadas[["codigo","descripcion_formula","categorias_por_insumo"]].drop_duplicates()
        categoria_por_aplicacion.rename(columns={"codigo":"formula","categorias_por_insumo":"categoria"},inplace=True)

        ## Tener cuidado acá porque categorias_por_aplicacion tiene aplicaciones 

        
        #Left join de las fórmulas del GS con las categorías correspondientes
        df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra_blocks.merge(categoria_por_aplicacion,how="left",on="formula")
        ####
        ## Filtro únicamente de nutrición
        ###
        df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra_blocks[df_union_formulas_cedulas_siembra_blocks['categoria'].str.contains("Fertilizante")]

        if df_union_formulas_cedulas_siembra_blocks.empty:
            print("Hay aplicaciones preforza pero ninguna de nutrición")
            aplicaciones_gs_actual = df_resultado
            resumen_gs_actual = df_resultado
            return df_resultado
        
        #Días de diferencia
        df_union_formulas_cedulas_siembra_blocks["diff"]=df_union_formulas_cedulas_siembra_blocks.groupby("blocknumber")["apldate"].diff()/np.timedelta64(1, 'D')
        
        #Ajuste para agregar diff a primera aplicación desde siembra
        fill_value = (df_union_formulas_cedulas_siembra_blocks["apldate"]- df_union_formulas_cedulas_siembra_blocks["finiciosiembra"])/np.timedelta64(1, 'D')
        df_union_formulas_cedulas_siembra_blocks["diff"] = df_union_formulas_cedulas_siembra_blocks["diff"].fillna(fill_value)

        #Guardar Query actual en memoria
        aplicaciones_gs_actual = df_union_formulas_cedulas_siembra_blocks 

        agg_dict = {
    "num apls": pd.NamedAgg(column='apldate', aggfunc=lambda ts: ts.count())
}

        df_resultado = df_union_formulas_cedulas_siembra_blocks.groupby(["blocknumber",
        "area","plantcant","finiciosiembra","finduccion"],dropna=False).agg(**agg_dict).reset_index().round(2)
        

        if is_datetime(df_resultado["finiciosiembra"]):
            df_resultado["finiciosiembra"]=df_resultado.finiciosiembra.dt.strftime('%d-%B-%Y')
        if is_datetime(df_resultado["finduccion"]):
            df_resultado["finduccion"]=df_resultado.finduccion.dt.strftime('%d-%B-%Y')

        ##Area a hectareas
        df_resultado["area"]= (df_resultado["area"]/10000).round(2)

        df_resultado.rename(columns={"blocknumber":"bloque","finiciosiembra":"fsiembra",
        "plantcant":"poblacion","area":"area (ha)"},inplace=True)

        
        #Agregar df auxiliar por trimestres

        df_resultados_por_trimestre = crear_dfs_auxiliares_trimestrales(df_union_formulas_cedulas_siembra_blocks)
        df_resultado = df_resultado.merge(df_resultados_por_trimestre, on="bloque",how="left")
        
        resumen_gs_actual = df_resultado
        #Se eliminan estas columnas porque no se desean en df_resultado pero si en resumen_gs_ctual
        columns_to_drop = [x for x in df_resultado.columns if x.startswith('abs')]
        return df_resultado.drop(columns_to_drop,axis=1)
    except Exception as e:

        print("hubo un error", e)
        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
        connection.rollback()
        return df_resultado


def crear_df_trimestral_transpuesto (df,trimestre):
    trim = str(trimestre)
    columnas = [x for x in df.columns if "q"+trim in x]
    df_trim = df[columnas]
    df_trim.columns = [x[4:-3] for x in df_trim.columns]
    df_trim= df_trim.transpose()
    df_trim.columns=["q"+trim]
    return df_trim


def retorna_detalle_calidad_nutricion_pc_preforza(bloque):

    columnas = [x for x in resumen_gs_actual.columns if x.startswith("abs")]
    if not columnas:
        return pd.DataFrame(columns=["No hay ","aplicaciones"])
    
    bloque_seleccionado = resumen_gs_actual.query("bloque==@bloque")[columnas]

    if bloque_seleccionado.empty:
        return pd.DataFrame(columns=["No hay ","aplicaciones asociadas al bloque"])


    df_q1 = crear_df_trimestral_transpuesto(bloque_seleccionado,1)
    df_q2 = crear_df_trimestral_transpuesto(bloque_seleccionado,2)
    df_q3 = crear_df_trimestral_transpuesto(bloque_seleccionado,3)
    df_q4 = crear_df_trimestral_transpuesto(bloque_seleccionado,4)
    
    dfs_a_unir = [df_q2,df_q3,df_q4]

    for data_frame in dfs_a_unir:
        if not data_frame.empty:
            df_q1 = df_q1.merge(data_frame, left_index=True,right_index=True,how="left")

    return df_q1.reset_index().rename(columns={"index":"métrica"})


def retorna_grafica_peso_planta(bloque):
    peso_planta_seleccionado = peso_planta.query("bloque==@bloque")
    
    if peso_planta_seleccionado.empty:

        df_peso_planta = pd.DataFrame(columns=["edad","promedio","fecha"])
    else:
        
        df_peso_planta = peso_planta_seleccionado.round(2)
    
    fig = px.scatter(df_peso_planta, x="fecha", y="promedio",title="Curva peso planta",
    labels={"edad":"edad","promedio":"peso planta promedio"},hover_data=["edad","promedio","fecha"])

    #Modifica tamaño de puntos
    fig.update_traces(marker=dict(size=12,
                              line=dict(width=2,
                                        color='DarkSlateGrey')),
                  selector=dict(mode='markers'))

    fig.update_xaxes(
        dtick=1209600000,
        tickformat="Semana %U-%b\n%Y")

    fig.add_annotation(
    xref="paper",
    yref="y",
    x=1,
    y=500,
    showarrow=False,
    text="aplicaciones",
    bgcolor="black"
)
    fig.add_annotation(
    xref="paper",
    yref="y",
    x=1,
    y=0,
    showarrow=False,
    text="trimestres",
    bgcolor="red"
)

    if bloque!="":
        aplicaciones_bloque_actual = aplicaciones_gs_actual.query("blocknumber==@bloque")[["descripcion_formula","apldate","finiciosiembra"]]
        fsiembra = aplicaciones_bloque_actual.finiciosiembra.max()

        for _,row in aplicaciones_bloque_actual.iterrows():
            fig.add_shape(type='line',
                        yref="y",
                        xref="x",
                        x0=row["apldate"],
                        y0=0,
                        x1=row["apldate"],
                        y1=3000,
                        line=dict(color='black', width=1))

        #Agregar línas de trimestres
        
        trimestres = [fsiembra + pd.DateOffset(weeks=12*x) for x in range (1,4)]

        for fecha in trimestres:
            fig.add_shape(type='line',
                        yref="y",
                        xref="x",
                        x0=fecha,
                        y0=0,
                        x1=fecha,
                        y1=3000,
                        line=dict(color='red', width=1))


    return fig

def retorna_info_aplicaciones_de_gs(bloque):
    
    if bloque =="" or aplicaciones_gs_actual.empty:
      return pd.DataFrame(columns=["Seleccione","bloque"])
    
    aplicaciones_bloque_actual = aplicaciones_gs_actual.query("blocknumber==@bloque")
    
    if aplicaciones_bloque_actual.empty:
        return pd.DataFrame(columns=["No hay","aplicaciones"])
    
    else:
        aplicaciones_bloque_actual["apldate"]=aplicaciones_bloque_actual["apldate"].dt.strftime('%d-%B-%Y')
        #aplicaciones_bloque_actual[["formula","descripcion_formula","apldate","diff","categoria"]]
        
        fecha_siembra_actual =  datetime.strptime(resumen_gs_actual.at[0,"fsiembra"], '%d-%B-%Y')
        #La fecha de siembra actual se usa para construir fechas programadas según paquete tecnológico
        calendario_aplicaciones["fecha_programada"] = calendario_aplicaciones["dias"].apply(lambda x: fecha_siembra_actual + timedelta(days=x))

        resultado = calendario_aplicaciones[["aplicacion","fecha_programada"]].reset_index(drop=True).merge(aplicaciones_bloque_actual[["descripcion_formula","apldate","diff"]].reset_index(drop=True),
        left_index=True, right_index=True,how="outer")

        resultado["fecha_programada"]=resultado["fecha_programada"].dt.strftime('%d-%B-%Y')

        resultado.columns = ["aplicacion programada","fecha programada","aplicacion ejecutada","fecha ejecutada", "diff"]
        return resultado


def retorna_detalle_formula(formula):
    detalle_formula = pd.DataFrame(columns=["Seleccione","Fórmula"])

    if formula =="":
        return detalle_formula

    try:

        formulas = pd.read_sql_query('''select codigo,descripcion from formulas where codigo = %s ''',
        con = connection,params =[formula])

        formulas_det = pd.read_sql_query('''select codigo,insumo,cantha from formulas_det where codigo = %s ''',
        con = connection,params =[formula])

        if formulas_det.empty==False:
            insumos = pd.read_sql_query('''select codigo, descripcion from maestroinsumos where codigo in %s  ''',
            con = connection,params =[tuple(set(formulas_det.insumo.to_list()))])
            
            union_formulas = formulas.merge(formulas_det, how="inner",on="codigo")
            union_formulas.rename(columns={"descripcion":"nombre_formula"},inplace=True)
            union_formulas.drop(["codigo"],axis=1,inplace=True)
            union_formulas_insumos = union_formulas.merge(insumos,how="left",left_on="insumo",right_on="codigo")

            detalle_formula = union_formulas_insumos[["insumo","descripcion","cantha"]].merge(categorias_insumos[["insumo","categorias_por_insumo"]].rename(columns={"categorias_por_insumo":"categoria"}),how="left",on ="insumo")

            return detalle_formula
        else:
            return detalle_formula
        
        

    except Exception as e:
        
        print("hubo un error", e)
        connection.rollback()
        return detalle_formula



