
import pandas as pd 
import locale 
import psycopg2
import sqlalchemy
from sqlalchemy import event

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
try:
    ejecucion_aplicaciones = pd.read_sql_query(''' 
    SELECT
    formula, 
    apldate,
    observaciones,
    descripcion as id_bloque,
    substring(descripcion from 1 for 2) as lote,
    substring(descripcion from 3 for 2) as bloque,
    cast(substring(descripcion from 5 for 2)as integer) as año,
    finiciosiembra,
    finduccion,
    gruposiembra2
    from (select blocknumber,t2.descripcion,finiciosiembra,finduccion,gruposiembra, t3.descripcion as gruposiembra2 from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo inner join grupossiembra as t3 on t2.gruposiembra = t3.codigo) as t1 inner join   
    
  (SELECT apldate
      ,formula
      ,observaciones
      ,blocknumber
  FROM (select codigo,
  apldate,
  formula,
  observaciones
    from mantenimientocampos
    where formula in (select distinct codigo from formulas_det where insumo in(
      select insumo from categoria_insumos where categorias_por_insumo='Fertilizante'
    ))) as t1
  inner join mantenimientocampos_detalleblocks as t2
  on t1.codigo=t2.codigo
  where blocknumber in (select blocknumber from siembra as t1 inner join blocks as t2 on t1.blocknumber=t2.codigo)) as t2
  on t1.blocknumber = t2.blocknumber
  order by apldate''',connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()



df_nutricion_preforza_pc = ejecucion_aplicaciones.query("apldate<finduccion")
df_nutricion_preforza_pc.drop(["lote","bloque","año","observaciones"],axis=1,inplace=True)
df_nutricion_preforza_pc.drop_duplicates(inplace=True) #Revisar dónde se generan duplicados
locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
df_nutricion_preforza_pc["apldate"] =  df_nutricion_preforza_pc.apldate.dt.strftime('%d-%B-%Y')
df_nutricion_preforza_pc["finiciosiembra"] =  df_nutricion_preforza_pc.finiciosiembra.dt.strftime('%d-%B-%Y')
df_nutricion_preforza_pc["finduccion"] =  df_nutricion_preforza_pc.finduccion.dt.strftime('%d-%B-%Y')
#Conservar para hacer tooltips
# ##Diccionario insumos
# insumos = pd.read_excel("insumos_por_aplicacion.xlsx")
# insumos["agrupacion"] = insumos.groupby("id_formula")["Descripcion"].transform(lambda x: "|||\n".join(x))
# insumos.drop_duplicates(subset=["id_formula"],inplace=True)
# insumos["tooltip"]="Descripción aplicación: " + insumos.descripcion_formula + "\n"+insumos.agrupacion
# diccionario_insumos = insumos.set_index("id_formula")["tooltip"].to_dict()
