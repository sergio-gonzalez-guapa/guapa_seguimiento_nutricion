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


consulta = """
WITH pesos as (
    SELECT llave, fecha as fecha_muestreo, AVG(valor) as peso_planta 
    FROM pesoplanta
    group by (llave,fecha)
    order by llave,fecha
),
cruce as (
    SELECT bloque,
    blocknumber,
    desarrollo,
    grupo_siembra,
     fecha_siembra,
    (DATE_PART('day',now()::timestamp - fecha_siembra::timestamp))/30 as edad_actual,
    fecha_muestreo,
    peso_planta,
    row_number() over (partition by bloque ORDER BY fecha_muestreo DESC) As rn
    FROM blocks_desarrollo AS t1
    LEFT JOIN pesos AS t2
    ON t1.bloque = t2.llave

    WHERE finduccion IS NULL AND
    bloque NOT LIKE '%J' AND
    fecha_siembra >= '2018-01-01'::date
    ORDER BY bloque, fecha_muestreo)

SELECT bloque, 
desarrollo,
t1.grupo_siembra as "grupo siembra",
 t2.fecha_siembra as "fecha siembra",
 poblacion,
 area*(1-drenajes)/10000 as "area neta (ha)",
 poblacion/ (area*(1-drenajes)/10000) as densidad,
  edad_actual as "edad actual meses",
 fecha_muestreo::date as "fecha ultimo muestreo",
 peso_planta as "peso promedio ultimo muestreo", 
 rango_semilla as "rango semilla"
FROM cruce as t1
LEFT JOIN blocks_detalle as t2
on t1.blocknumber = t2.blocknumber
WHERE rn=1 AND ((edad_actual >8 AND desarrollo='PC') OR (edad_actual >3 AND desarrollo='SC'))
ORDER BY edad_actual desc
""" 


#Layout

@cache.memoize()
def generar_lista_bloques_forzamiento():
    return db_connection.query(consulta)


exportar_a_excel_input = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id="exportar-forzamiento-excel-btn", color="success", className="mr-1"),
        Download(id="download-forzamiento")
    ]
)
form_programacion = dbc.Form([exportar_a_excel_input])

layout = elementos.DashLayout(extra_elements=[form_programacion])

layout.crear_elemento(tipo="table",element_id="bloques-por-forzar-table",  label="Bloques por forzar")
layout.ordenar_elementos(["bloques-por-forzar-table"])


###################
##### Callbacks ###
###################

#Actualizar alertas
@app.callback(Output("bloques-por-forzar-table", "children"), [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='listado-forzamiento':

        data = generar_lista_bloques_forzamiento().round(2)
        return dbc.Table.from_dataframe(data).children

    return None


@app.callback(
Output("download-forzamiento", "data"),
[Input("exportar-forzamiento-excel-btn", "n_clicks")],
[State("bloques-por-forzar-table", "children")])
def download_as_csv(n_clicks, table_data):
    if (not n_clicks) or (table_data is None):
      raise PreventUpdate

    df = dbc_table_to_pandas(table_data)
    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, "bloques_por_forzar.xlsx")