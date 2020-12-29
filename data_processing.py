
import pickle
import pandas as pd 
import locale 
import psycopg2

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
    historia_bloques = pd.read_sql_query(''' select bloque as id,
date(primera) as inicio_PC,
date(produccion_semilla) inicio_SM_PC,
date(segunda) inicio_SC,
date(produccion_semilla2) inicio_SMSC,
date(barrido) as barrido
from (SELECT 
blocknumber as bloque,
max (CASE WHEN t1.Estado = '1' THEN FechaEstado ELSE NULL END) as primera,
max (CASE WHEN t1.Estado = '2' THEN FechaEstado ELSE NULL END) as segunda,
max (CASE WHEN t1.Estado = '3' THEN FechaEstado ELSE NULL END) as produccion_semilla,
max (CASE WHEN t1.Estado = '4' THEN FechaEstado ELSE NULL END) as barrido,
/*
max (CASE WHEN t1.Estado = '5' THEN FechaEstado ELSE NULL END) as presiembra,
max (CASE WHEN t1.Estado = '6' THEN FechaEstado ELSE NULL END) as sindefinir,*/
max (CASE WHEN t1.Estado = '7' THEN FechaEstado ELSE NULL END) as produccion_semilla2

  FROM siembrafechaestados as t1
  inner join siembra as t2 on
  t1.Codigo=t2.Codigo
  GROUP BY blocknumber) as t1
order by primera ''',connection)
except Exception as e:

    print("hubo un error", e)
    connection.rollback()



historia_bloques["lote"]=historia_bloques.id.str.slice(start=0,stop=2)
historia_bloques["bloque"]=historia_bloques.id.str.slice(start=2,stop=4)
historia_bloques["año"]=historia_bloques.id.str.slice(start=4,stop=6)
historia_bloques.query("año!=''",inplace=True)
historia_bloques["año"]=historia_bloques["año"].astype(int)
historia_bloques.sort_values(by=["lote","año","bloque"],inplace=True)

df_nutricion_preforza_pc = pd.read_excel("aplicaciones_fertilizantes_preforza_pc_por_lote.xlsx",parse_dates=["fecha"])
locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
df_nutricion_preforza_pc["fecha"] =  df_nutricion_preforza_pc.fecha.dt.strftime('%d-%B-%Y')

##Diccionario insumos
insumos = pd.read_excel("insumos_por_aplicacion.xlsx")
insumos["agrupacion"] = insumos.groupby("id_formula")["Descripcion"].transform(lambda x: "|||\n".join(x))
insumos.drop_duplicates(subset=["id_formula"],inplace=True)
insumos["tooltip"]="Descripción aplicación: " + insumos.descripcion_formula + "\n"+insumos.agrupacion
diccionario_insumos = insumos.set_index("id_formula")["tooltip"].to_dict()
