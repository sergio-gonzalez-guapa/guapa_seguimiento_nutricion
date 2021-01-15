
import pandas as pd 
import numpy as np
import locale 
import psycopg2
import sqlalchemy
from sqlalchemy import event
import plotly.express as px

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
categorias_insumos = pd.read_excel("relacion_insumos_principales_categorias.xlsx")
categorias_insumos.dropna(subset=["categorias_por_insumo"],inplace=True)

peso_planta = pd.read_excel("peso_planta.xlsx",dtype={"bloque":str})
peso_planta.sort_values(by=["bloque","edad"],inplace=True)


# ssl_args ={"sslmode":'verify-ca',"sslrootcert": "gcp postgres/server-ca.pem","sslcert": "gcp postgres/client-cert.pem","sslkey":"gcp postgres/client-key.pem"}
# pool = sqlalchemy.create_engine(
#     # Equivalent URL:
#     # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
#     sqlalchemy.engine.url.URL(
#         drivername="postgresql+psycopg2",
#         username="postgres",  # e.g. "my-database-user"
#         password="Guapa.2020*",  # e.g. "my-database-password"
#         host="35.237.147.235",  # e.g. "127.0.0.1"
#         port="5432",  # e.g. 3306
#         database='ppc',  # e.g. "my-database-name"
#     ),connect_args=ssl_args
# )
# #Corrección para ejecución rápida de comandos sql
# @event.listens_for(pool, 'before_cursor_execute')
# def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
#     if executemany:
#         cursor.fast_executemany = True
#         cursor.commit()

# categorias_insumos.to_sql(name="categoria_insumos",con=pool,if_exists='replace',index=False,method='multi')


## Extraer información tabla bloques:
##Falta corregir join de grupossiembra

#####
# Listado de grupos de siembra
####

#Extraer bloques y años de la tabla blocks:
try:
    lotes_historia = pd.read_sql_query("select distinct concat('lote ',substring(descripcion,1,2), ' año 20',substring(descripcion,5,2)) as label, concat(substring(descripcion,1,2),'__',substring(descripcion,5,2)) as value from blocks where codigo in (select blocknumber from siembra) order by 1" ,connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()

## Extraer información grupos de siembra
try:
    grupossiembra = pd.read_sql_query('''select codigo,descripcion,fecha from grupossiembra where fecha >= '2014-03-01'::date order by fecha''',connection)
    
except Exception as e:

    print("hubo un error", e)
    connection.rollback()

df_grupos_siembra = grupossiembra[["codigo","descripcion"]]

## Extraer información de fórmulas
try:
    df_formulas = pd.read_sql_query('''select codigo, descripcion from formulas''',connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()



#######################
## devuelve información de estados de los bloques de un lote
#####################

def retorna_info_estados_bloques(lote):
    df_resultado = pd.DataFrame(columns=["Seleccione","lote"])
    try:
        historia_bloques = pd.read_sql_query(''' select
        bloque,
        t2.descripcion as gruposiembra,
        grupoforza,
        date(primera) as inicio_PC,
        date(produccion_semilla) inicio_SM_PC,
        date(segunda) inicio_SC,
        date(produccion_semilla2) inicio_SM_SC,
        date(barrido) as barrido
        from (
            SELECT descripcion as bloque,
            gruposiembra,
            grupoforza,
            max (CASE WHEN t1.Estado = '1' THEN FechaEstado ELSE NULL END) as primera,
            max (CASE WHEN t1.Estado = '2' THEN FechaEstado ELSE NULL END) as segunda,
            max (CASE WHEN t1.Estado = '3' THEN FechaEstado ELSE NULL END) as produccion_semilla,
            max (CASE WHEN t1.Estado = '4' THEN FechaEstado ELSE NULL END) as barrido,
            /*
            max (CASE WHEN t1.Estado = '5' THEN FechaEstado ELSE NULL END) as presiembra,
            max (CASE WHEN t1.Estado = '6' THEN FechaEstado ELSE NULL END) as sindefinir,*/
            max (CASE WHEN t1.Estado = '7' THEN FechaEstado ELSE NULL END) as produccion_semilla2

            FROM (
                select t1.codigo,descripcion,gruposiembra,grupoforza
                 from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo
                 where descripcion like %s) as t2 

        left join siembrafechaestados as t1 on
        t1.codigo=t2.codigo
        GROUP BY descripcion,gruposiembra, grupoforza
                ) as t1
        left join grupossiembra as t2
        on t1.gruposiembra=t2.codigo
        order by bloque ''',con = connection, params=[lote])
  
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
  consulta = '''select codigo,descripcion from blocks where gruposiembra =%s '''
  try:
      bloques = pd.read_sql_query(consulta,con=connection,params=[str(gs)])

      lista_dicts_bloques = [{"label":row["descripcion"],"value":row["codigo"]} for _,row in bloques.iterrows()]
      return lista_dicts_bloques
  except Exception as e:

      print("hubo un error", e)
      connection.rollback()
  

def retorna_info_bloques_de_gs(gs):
    df_resultado = pd.DataFrame(columns=["no hay","aplicaciones"])
    try:
        bloques = pd.read_sql_query('''select codigo as blocknumber,descripcion,lote,area,gruposiembra from blocks where gruposiembra = %s''',
        con = connection,params = [gs])
        
        if bloques.empty==False:
            cedulas = pd.read_sql_query('''select codigo, blocknumber from MANTENIMIENTOCAMPOS_DETALLEBLOCKs where blocknumber in %s ''',
            con = connection,params =[tuple(set(bloques.blocknumber.to_list()))])
            siembra = pd.read_sql_query('''select blocknumber,plantcant,finiciosiembra,finduccion from siembra where blocknumber in %s ''',
            con = connection,params =[tuple(set(bloques.blocknumber.to_list()))])

            if cedulas.empty==False:
                formulas = pd.read_sql_query('''select codigo,formula,apldate from mantenimientocampos where codigo in %s  ''', con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
                #Unión de mantenimiento con mantenimiento campos
                df_union_formulas_cedulas = formulas.merge(cedulas, how="inner",on="codigo")
                df_union_formulas_cedulas.sort_values(by=["blocknumber","apldate"],inplace=True)
                
                #Left join con siembra y blocks
                df_union_formulas_cedulas_siembra = df_union_formulas_cedulas.merge(siembra,how="left",on="blocknumber")
                df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra.merge(bloques,how="left",on="blocknumber")

                #Filtro preforza
                df_union_formulas_cedulas_siembra_blocks.query("apldate<finduccion",inplace=True)

                #Filtro nutrición

                #Definir categoría de la aplicación
                insumos_por_formulas_seleccionadas = pd.read_sql_query('''select codigo,insumo from formulas_det where codigo in %s ''',
                con = connection,params =[tuple(set(df_union_formulas_cedulas_siembra_blocks.formula.to_list()))])
                insumos_por_formulas_seleccionadas = insumos_por_formulas_seleccionadas.merge(categorias_insumos,how="inner",on="insumo")
                categoria_por_aplicacion = insumos_por_formulas_seleccionadas[["codigo","categorias_por_insumo"]].drop_duplicates()
                categoria_por_aplicacion.rename(columns={"codigo":"formula","categorias_por_insumo":"categoria"},inplace=True)

                df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra_blocks.merge(categoria_por_aplicacion,how="left",on="formula")
                df_union_formulas_cedulas_siembra_blocks = df_union_formulas_cedulas_siembra_blocks[df_union_formulas_cedulas_siembra_blocks['categoria'].str.contains("Fertilizante")]
                #Días de diferencia
                df_union_formulas_cedulas_siembra_blocks["diff"]=df_union_formulas_cedulas_siembra_blocks.groupby("blocknumber")["apldate"].diff()/np.timedelta64(1, 'D')
                df_resultado = df_union_formulas_cedulas_siembra_blocks.groupby(["blocknumber","area","plantcant","finiciosiembra","finduccion"])["diff"].agg(num_aplica=lambda ts: ts.count()+1,dias_prom ="mean",max_dias="max" ,apl_mas_de_15_dias=lambda ts: (ts > 15).sum()).reset_index().round(2)
                #Ajuste de sumarle 1 al número de aplicaciones porque hace el resumen por columna diff que empieza con un valor nulo

                ### Ajustes

                df_resultado["finiciosiembra"]=df_resultado.finiciosiembra.dt.strftime('%d-%B-%Y')
                df_resultado["finduccion"]=df_resultado.finduccion.dt.strftime('%d-%B-%Y')
                df_resultado.rename(columns={"blocknumber":"bloque"},inplace=True)

        return df_resultado
    except Exception as e:

        print("hubo un error", e)
        connection.rollback()
        return df_resultado


def retorna_info_aplicaciones_preforza_por_bloque(bloque):

  ## Extraer información tabla bloques:
  df_resultado_union_bloque_siembra = pd.DataFrame(columns=["Seleccione","bloque"])
  
  if bloque =="":
      return df_resultado_union_bloque_siembra,df_resultado_union_bloque_siembra

  try:
    
    cedulas = pd.read_sql_query('''select codigo from MANTENIMIENTOCAMPOS_DETALLEBLOCKs where blocknumber = %s ''',
    con = connection,params =[bloque])

    if cedulas.empty==False:
        finduccion = pd.read_sql_query('''select finduccion from siembra where blocknumber = %s ''',
        con = connection,params =[bloque]).iat[0,0]

        formulas = pd.read_sql_query('''select codigo, formula,apldate from mantenimientocampos where codigo in %s  ''', con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
        detalle_formulas = pd.read_sql_query('''
        select formula,t1.descripcion as descripcion_formula, t2.descripcion as etapa from 
        (select codigo as formula, descripcion,etapa from formulas where codigo in %s) as t1
        left join etapasaplicacion as t2 on  t1.etapa=t2.codigo
        
         ''', con = connection,params =[tuple(set(formulas.formula.to_list()))])
        formulas_con_detalle = formulas.merge(detalle_formulas,how="left",on="formula")

        df_union_formulas_cedulas = formulas_con_detalle.merge(cedulas, how="inner",on="codigo")
        df_union_formulas_cedulas.sort_values(by=["apldate"],inplace=True)
        df_union_formulas_cedulas.query("apldate<@finduccion",inplace=True)

        #Definir categoría de la aplicación
        if df_union_formulas_cedulas.empty==False:
            insumos_por_formulas_seleccionadas = pd.read_sql_query('''select codigo,insumo from formulas_det where codigo in %s ''',
            con = connection,params =[tuple(set(df_union_formulas_cedulas.formula.to_list()))])
            insumos_por_formulas_seleccionadas = insumos_por_formulas_seleccionadas.merge(categorias_insumos,how="inner",on="insumo")
            categoria_por_aplicacion = insumos_por_formulas_seleccionadas[["codigo","categorias_por_insumo"]].drop_duplicates()
        else:
            return df_resultado_union_bloque_siembra
      
    return df_union_formulas_cedulas,categoria_por_aplicacion
  except Exception as e:

      print("hubo un error", e)
      connection.rollback()
      return df_resultado_union_bloque_siembra,df_resultado_union_bloque_siembra


def retorna_resumen_aplicaciones_por_bloque(bloque):

    ## Extraer información tabla bloques:
    df_formulas, df_categorias = retorna_info_aplicaciones_preforza_por_bloque(bloque)
  
    if df_formulas.empty ==True:
        return df_formulas
    else: 
        df_categorias.rename(columns={"codigo":"formula","categorias_por_insumo":"categoria"},inplace=True)
        
        df_formulas_con_categorias = df_formulas.merge(df_categorias,how="left",on="formula")
        df_formulas_con_categorias = df_formulas_con_categorias[["apldate","categoria"]]
        df_formulas_con_categorias.sort_values(by=["categoria","apldate"],inplace=True)
        df_formulas_con_categorias["diff"]=df_formulas_con_categorias.groupby("categoria")["apldate"].diff()/np.timedelta64(1, 'D')

        df_resultado = df_formulas_con_categorias.groupby(["categoria"])["diff"].agg(num_aplicaciones="count",
        dias_prom="mean",max_dias="max",min_dias="min").reset_index().round(2)
        return df_resultado



def retorna_grafica_peso_planta(bloque):
    peso_planta_seleccionado = peso_planta.query("bloque==@bloque")
    if peso_planta_seleccionado.empty:

        df = pd.DataFrame(columns=["edad","promedio"])
    else:
        df = peso_planta_seleccionado
    
    fig = px.scatter(df, x="edad", y="promedio",title="Curva peso planta",labels={"edad":"edad","promedio":"peso planta promedio"})
    return fig

def retorna_info_aplicaciones_de_gs(bloque):

    ## Extraer información tabla bloques:
    df_formulas, df_categorias = retorna_info_aplicaciones_preforza_por_bloque(bloque)
  
    if df_formulas.empty:
        return df_formulas
    else: 
        df_categorias_agrupadas = df_categorias.groupby("codigo")["categorias_por_insumo"].apply(lambda x: ','.join(x)).reset_index()
        df_categorias_agrupadas.rename(columns={"codigo":"formula","categorias_por_insumo":"categoria"},inplace=True)
        
        df_formulas_con_categorias = df_formulas.merge(df_categorias_agrupadas,how="left",on="formula")
        #Filtro de fertilizante
        df_formulas_con_categorias = df_formulas_con_categorias[df_formulas_con_categorias['categoria'].str.contains("Fertilizante")]
        df_formulas_con_categorias["diff"]=df_formulas_con_categorias["apldate"].diff()/np.timedelta64(1, 'D')
        df_formulas_con_categorias = df_formulas_con_categorias[["formula","descripcion_formula","apldate","diff","categoria"]]
        df_formulas_con_categorias["apldate"]=df_formulas_con_categorias.apldate.dt.strftime('%d-%B-%Y')

        return df_formulas_con_categorias

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



