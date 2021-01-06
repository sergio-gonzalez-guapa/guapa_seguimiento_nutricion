
import pandas as pd 
import numpy as np
import locale 
import psycopg2
import sqlalchemy
from sqlalchemy import event

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

#Cargue estado bloques
## Extraer información tabla bloques:
try:
    historia_bloques = pd.read_sql_query(''' select
    bloque_corregido as id,
    substring(bloque_corregido from 1 for 2) as lote,
    substring(bloque_corregido from 3 for 2) as bloque,
    cast(substring(bloque_corregido from 5 for 2)as integer) as año,
date(primera) as inicio_PC,
date(produccion_semilla) inicio_SM_PC,
date(segunda) inicio_SC,
date(produccion_semilla2) inicio_SMSC,
date(barrido) as barrido
from (SELECT 
descripcion as bloque_corregido,
blocknumber as bloque,
max (CASE WHEN t1.Estado = '1' THEN FechaEstado ELSE NULL END) as primera,
max (CASE WHEN t1.Estado = '2' THEN FechaEstado ELSE NULL END) as segunda,
max (CASE WHEN t1.Estado = '3' THEN FechaEstado ELSE NULL END) as produccion_semilla,
max (CASE WHEN t1.Estado = '4' THEN FechaEstado ELSE NULL END) as barrido,
/*
max (CASE WHEN t1.Estado = '5' THEN FechaEstado ELSE NULL END) as presiembra,
max (CASE WHEN t1.Estado = '6' THEN FechaEstado ELSE NULL END) as sindefinir,*/
max (CASE WHEN t1.Estado = '7' THEN FechaEstado ELSE NULL END) as produccion_semilla2

  FROM (select t1.codigo,blocknumber, lote,descripcion from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo) as t2 
  left join siembrafechaestados as t1 on
  t1.Codigo=t2.Codigo
  GROUP BY blocknumber,descripcion) as t1
order by lote, año, bloque ''',connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()




# ###Query nutricion PC
# ###################
# ######################
# categorias_insumos = pd.read_excel("relacion_insumos_principales_categorias.xlsx")


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
    try:
        bloques = pd.read_sql_query('''select codigo,descripcion,lote,area,gruposiembra from blocks where gruposiembra = %s''',
        con = connection,params = [gs])
        df_resultado_union_bloque_siembra = pd.DataFrame(columns=["no hay","bloques"])
        if bloques.empty==False:
            cedulas = pd.read_sql_query('''select codigo, blocknumber from MANTENIMIENTOCAMPOS_DETALLEBLOCKs where blocknumber in %s ''',
            con = connection,params =[tuple(set(bloques.codigo.to_list()))])
            siembra = pd.read_sql_query('''select blocknumber,plantcant,finiciosiembra,finduccion from siembra where blocknumber in %s ''',
            con = connection,params =[tuple(set(bloques.codigo.to_list()))])

            if cedulas.empty==False:
                formulas = pd.read_sql_query('''select codigo,formula,apldate from mantenimientocampos where codigo in %s  ''', con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
                
                df_union_formulas_cedulas = formulas.merge(cedulas, how="inner",on="codigo")
                df_union_formulas_cedulas.sort_values(by=["blocknumber","apldate"],inplace=True)
                
                df_union_formulas_cedulas["diff"]=df_union_formulas_cedulas.groupby("blocknumber")["apldate"].diff()/np.timedelta64(1, 'D')

                df_resultado = df_union_formulas_cedulas.groupby("blocknumber")["diff"].agg(num_aplicaciones="count",dias_prom="mean",max_dias="max",min_dias="min").reset_index().round(2)
                df_resultado.rename(columns={"blocknumber":"codigo"},inplace=True)

                df_resultado_union_bloque = bloques.merge(df_resultado,how="left",on="codigo")
                df_resultado_union_bloque_siembra = df_resultado_union_bloque.merge(siembra,how="left",left_on="codigo",right_on="blocknumber")
                df_resultado_union_bloque_siembra.drop(["codigo","blocknumber","gruposiembra"],axis=1,inplace=True)
                ### Ajustes

                df_resultado_union_bloque_siembra["finiciosiembra"]=df_resultado_union_bloque_siembra.finiciosiembra.dt.strftime('%d-%B-%Y')
                df_resultado_union_bloque_siembra["finduccion"]=df_resultado_union_bloque_siembra.finduccion.dt.strftime('%d-%B-%Y')
                df_resultado_union_bloque_siembra.rename(columns={"descripcion":"bloque"},inplace=True)

        return df_resultado_union_bloque_siembra
    except AttributeError as error:
        print("error con el campo:",error)
        return df_resultado_union_bloque_siembra
    except Exception as e:

        print("hubo un error", e)
        connection.rollback()


def retorna_info_aplicaciones_de_gs(bloque):

  ## Extraer información tabla bloques:
  df_resultado_union_bloque_siembra = pd.DataFrame(columns=["Seleccione","bloque"])
  
  if bloque =="":
      return df_resultado_union_bloque_siembra

  try:
    
    cedulas = pd.read_sql_query('''select codigo from MANTENIMIENTOCAMPOS_DETALLEBLOCKs where blocknumber = %s ''',
    con = connection,params =[bloque])

    if cedulas.empty==False:
        formulas = pd.read_sql_query('''select codigo, formula,apldate from mantenimientocampos where codigo in %s  ''', con = connection,params =[tuple(set(cedulas.codigo.to_list()))])
        detalle_formulas = pd.read_sql_query('''
        select formula,t1.descripcion as descripcion_formula, t2.descripcion as etapa from 
        (select codigo as formula, descripcion,etapa from formulas where codigo in %s) as t1
        left join etapasaplicacion as t2 on  t1.etapa=t2.codigo
        
         ''', con = connection,params =[tuple(set(formulas.formula.to_list()))])
        formulas_con_detalle = formulas.merge(detalle_formulas,how="left",on="formula")

        df_union_formulas_cedulas = formulas_con_detalle.merge(cedulas, how="inner",on="codigo")
        df_union_formulas_cedulas.sort_values(by=["apldate"],inplace=True)

        df_union_formulas_cedulas["diff"]=df_union_formulas_cedulas["apldate"].diff()/np.timedelta64(1, 'D')
        df_resultado_union_bloque_siembra = df_union_formulas_cedulas[["formula","descripcion_formula","apldate","diff","etapa"]]
        df_resultado_union_bloque_siembra["apldate"]=df_resultado_union_bloque_siembra.apldate.dt.strftime('%d-%B-%Y')

    return df_resultado_union_bloque_siembra
  except Exception as e:

      print("hubo un error", e)
      connection.rollback()



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
            detalle_formula = union_formulas_insumos[["nombre_formula","insumo","descripcion","cantha"]]
            return detalle_formula
        else:
            return detalle_formula
        
        

    except Exception as e:
        
        print("hubo un error", e)
        connection.rollback()
        return detalle_formula

    
    






# try:
#     ejecucion_aplicaciones = pd.read_sql_query(''' 
#     SELECT
#     formula, 
#     apldate,
#     observaciones,
#     descripcion as id_bloque,
#     substring(descripcion from 1 for 2) as lote,
#     substring(descripcion from 3 for 2) as bloque,
#     cast(substring(descripcion from 5 for 2)as integer) as año,
#     finiciosiembra,
#     finduccion,
#     gruposiembra2
#     from (select blocknumber,t2.descripcion,finiciosiembra,finduccion,gruposiembra, t3.descripcion as gruposiembra2 from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo inner join grupossiembra as t3 on t2.gruposiembra = t3.codigo) as t1 inner join   
    
#   (SELECT apldate
#       ,formula
#       ,observaciones
#       ,blocknumber
#   FROM (select codigo,
#   apldate,
#   formula,
#   observaciones
#     from mantenimientocampos
#     where formula in (select distinct codigo from formulas_det where insumo in(
#       select insumo from categoria_insumos where categorias_por_insumo='Fertilizante'
#     ))) as t1
#   inner join mantenimientocampos_detalleblocks as t2
#   on t1.codigo=t2.codigo
#   where blocknumber in (select blocknumber from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo)) as t2
#   on t1.blocknumber = t2.blocknumber
#   order by apldate''',connection)
# except Exception as e:

#     print("hubo un error", e)
#     connection.rollback()



# df_nutricion_preforza_pc = ejecucion_aplicaciones.query("apldate<finduccion")
# df_nutricion_preforza_pc.drop(["lote","bloque","año","observaciones"],axis=1,inplace=True)
# df_nutricion_preforza_pc.drop_duplicates(inplace=True) #Revisar dónde se generan duplicados
# locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
# df_nutricion_preforza_pc["apldate"] =  df_nutricion_preforza_pc.apldate.dt.strftime('%d-%B-%Y')
# df_nutricion_preforza_pc["finiciosiembra"] =  df_nutricion_preforza_pc.finiciosiembra.dt.strftime('%d-%B-%Y')
# df_nutricion_preforza_pc["finduccion"] =  df_nutricion_preforza_pc.finduccion.dt.strftime('%d-%B-%Y')




#Conservar para hacer tooltips
# ##Diccionario insumos
# insumos = pd.read_excel("insumos_por_aplicacion.xlsx")
# insumos["agrupacion"] = insumos.groupby("id_formula")["Descripcion"].transform(lambda x: "|||\n".join(x))
# insumos.drop_duplicates(subset=["id_formula"],inplace=True)
# insumos["tooltip"]="Descripción aplicación: " + insumos.descripcion_formula + "\n"+insumos.agrupacion
# diccionario_insumos = insumos.set_index("id_formula")["tooltip"].to_dict()
