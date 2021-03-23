import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
import db_connection
import plotly.express as px
from datetime import datetime
import numpy as np
from app import app
from .layouts_predefinidos import elementos 


aplicaciones = db_connection.query('''
WITH aplicaciones_ordenadas AS (
SELECT bloque, etapa,grupo,fecha,codigo_formula,descripcion_formula,categoria,
row_number() over (partition by bloque
                                 order by fecha desc) as rn
FROM aplicaciones 
WHERE blocknumber in (SELECT blocknumber FROM blocks_desarrollo WHERE finduccion is null ) AND
categoria = 'fertilizante'
AND etapa ='Post Siembra'
AND grupo is not NULL
AND bloque is not NULL
ORDER BY blocknumber, fecha)

SELECT bloque,grupo,fecha,descripcion_formula, DATE_PART('day',now()-fecha)::integer as dias_desde_ultima_aplicacion FROM aplicaciones_ordenadas 
WHERE rn = 1
''')

aplicaciones["fecha"]= aplicaciones["fecha"].dt.strftime('%d-%B-%Y')

data = aplicaciones.groupby(['fecha','descripcion_formula','grupo','dias_desde_ultima_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()

data.query("dias_desde_ultima_aplicacion<=60",inplace=True)
data["bloques_pendientes"] = data["grupo"].str.cat(data["bloque"], sep=':')
data["bloques_pendientes"] = data["bloques_pendientes"].astype(str)
data.drop(["bloque","grupo"],axis=1,inplace=True)
data = data.groupby(['fecha','descripcion_formula','dias_desde_ultima_aplicacion'],dropna=False)['bloques_pendientes'].apply('. || '.join).reset_index()
data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)


layout = elementos.DashLayout()

layout.crear_elemento(tipo="table",element_id="aplicaciones-pendientes-table",  label="Detalle bloques", content=dbc.Table.from_dataframe(data).children)
layout.ordenar_elementos(["aplicaciones-pendientes-table"])




