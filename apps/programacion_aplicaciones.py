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
SELECT * 
FROM APLICACIONES 
WHERE blocknumber in (SELECT BLOCKNUMBER FROM BLOCKS_desarrollo WHERE FINDUCCION is null ) AND
categoria = 'FERTILIZANTES'
ORDER BY blocknumber, fecha_aplicacion
''')

bloques = db_connection.query('''
SELECT blocknumber, 
grupo_siembra
FROM blocks_detalle 
WHERE grupo_forza is null and grupo_siembra is not null
''')

aplicaciones_filtradas = aplicaciones.drop_duplicates(subset="blocknumber",keep='last').copy()
aplicaciones_filtradas = aplicaciones_filtradas.merge(bloques, how="left",on="blocknumber")
aplicaciones_filtradas["hoy"] = datetime.today()
aplicaciones_filtradas["dias_desde_ultima_aplicacion"]=(aplicaciones_filtradas["hoy"]-aplicaciones_filtradas["fecha_aplicacion"]).dt.days
aplicaciones_filtradas["fecha_aplicacion"]= aplicaciones_filtradas["fecha_aplicacion"].dt.strftime('%d-%B-%Y')
aplicaciones_filtradas.drop(["codigo_formula","etapa","motivo","hoy","categoria"],axis=1,inplace=True)

data = aplicaciones_filtradas.groupby(['fecha_aplicacion','descripcion_formula','grupo_siembra','dias_desde_ultima_aplicacion'],dropna=False)['blocknumber'].apply(', '.join).reset_index()

data.query("dias_desde_ultima_aplicacion<=60",inplace=True)
data["bloques_pendientes"] = data["grupo_siembra"].str.cat(data["blocknumber"], sep=':')
data["bloques_pendientes"] = data["bloques_pendientes"].astype(str)
data.drop(["blocknumber","grupo_siembra"],axis=1,inplace=True)
data = data.groupby(['fecha_aplicacion','descripcion_formula','dias_desde_ultima_aplicacion'],dropna=False)['bloques_pendientes'].apply('. || '.join).reset_index()
data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)


layout = elementos.DashLayout()

layout.crear_elemento(tipo="table",element_id="aplicaciones-pendientes-table",  label="Detalle bloques", content=dbc.Table.from_dataframe(data).children)
layout.ordenar_elementos(["aplicaciones-pendientes-table"])




