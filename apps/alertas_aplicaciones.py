import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_bytes
from dash.exceptions import PreventUpdate


import db_connection
import plotly.express as px
from datetime import datetime
import numpy as np
from app import app,cache, dbc_table_to_pandas
from .layouts_predefinidos import elementos 



consulta_aplicaciones = '''
WITH aplicaciones_ordenadas AS (
SELECT bloque, etapa,grupo,fecha::date,
codigo_formula,
descripcion_formula,
categoria,
row_number() over (partition by bloque
                                 order by fecha desc) as rn
FROM aplicaciones 
WHERE blocknumber in (SELECT blocknumber FROM blocks_desarrollo WHERE finduccion is null ) AND
categoria = 'fertilizante'
AND etapa in ('Post Siembra','Post Deshija')
AND grupo is not NULL
AND bloque is not NULL
ORDER BY blocknumber, fecha)

SELECT bloque,grupo,fecha,descripcion_formula, DATE_PART('day',now()-fecha)::integer as dias_desde_ultima_aplicacion FROM aplicaciones_ordenadas 
WHERE rn = 1
'''
@cache.memoize()
def generar_alertas_bloques_actuales ():
    return db_connection.query(consulta_aplicaciones)

consulta_bloques_nuevos = """SELECT bloque,
fecha_siembra,
DATE_PART('day',now()-fecha_siembra)::integer AS dias_sin_aplicacion
FROM blocks_desarrollo 
WHERE finduccion is null 
AND bloque NOT IN (select distinct bloque 
FROM aplicaciones)
"""
@cache.memoize()
def generar_alertas_bloques_nuevos ():
    return db_connection.query(consulta_bloques_nuevos)


exportar_a_excel_input = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id="exportar-alertas-excel-btn", color="success", className="mr-1"),
        Download(id="download-alertas")
    ]
)
form_programacion = dbc.Form([exportar_a_excel_input])

layout = elementos.DashLayout(extra_elements=[form_programacion])

layout.crear_elemento(tipo="table",element_id="aplicaciones-pendientes-table",  label="Últimas aplicaciones nutrición preforza")
layout.crear_elemento(tipo="table",element_id="bloques-nuevos-table",  label="Bloques recien sembrados sin aplicación")
layout.ordenar_elementos(["aplicaciones-pendientes-table","bloques-nuevos-table"])

@app.callback(Output("aplicaciones-pendientes-table", "children"), [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='alertas-aplicaciones':
        aplicaciones = generar_alertas_bloques_actuales()
        aplicaciones["fecha"]= pd.to_datetime(aplicaciones["fecha"]).dt.strftime('%d-%B-%Y')
        aplicaciones["lote"] = aplicaciones["bloque"].str.slice(start=2, stop=4)
        data = aplicaciones.groupby(['fecha','descripcion_formula',"lote", 'grupo','dias_desde_ultima_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
        data.query("dias_desde_ultima_aplicacion<=60",inplace=True)
        data["bloques_pendientes"] = data["grupo"].str.cat(data["bloque"], sep=':')
        data["bloques_pendientes"] = data["bloques_pendientes"].astype(str)
        data.drop(["bloque","grupo"],axis=1,inplace=True)
        data = data.groupby(['fecha','descripcion_formula',"lote",'dias_desde_ultima_aplicacion'],dropna=False)['bloques_pendientes'].apply('\n---------------------\n'.join).reset_index()
        data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)
        return dbc.Table.from_dataframe(data).children

    return None

@app.callback(Output("bloques-nuevos-table", "children"), [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='alertas-aplicaciones':
        aplicaciones2 = generar_alertas_bloques_nuevos()
        aplicaciones2["fecha_siembra"]= pd.to_datetime(aplicaciones2["fecha_siembra"]).dt.strftime('%d-%B-%Y')
        data2 = aplicaciones2.groupby(['fecha_siembra','dias_sin_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
        data2.sort_values(by="dias_sin_aplicacion",ascending=False,inplace=True)
        return dbc.Table.from_dataframe(data2).children

    return None


@app.callback(
Output("download-alertas", "data"),
[Input("exportar-alertas-excel-btn", "n_clicks")],
[State("aplicaciones-pendientes-table", "children"),
State("bloques-nuevos-table", "children")])
def download_as_csv(n_clicks, table_data, table_data2):
    if (not n_clicks) or (table_data is None):
      raise PreventUpdate
    
    # import pickle


    # with open('tablita.pickle', 'wb') as handle:
    #     pickle.dump(table_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    df = dbc_table_to_pandas(table_data)
    df2=dbc_table_to_pandas(table_data2)
    # download_buffer = io.StringIO()
    # df.to_csv(download_buffer, index=False)
    # download_buffer.seek(0)
    # return dict(content=download_buffer.getvalue(), filename="tabla_comparacion.csv")

    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        df2.to_excel(xslx_writer, index=False, sheet_name="sheet2")
        xslx_writer.save()

    return send_bytes(to_xlsx, "alertas_aplicaciones.xlsx")