import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_bytes
from dash.exceptions import PreventUpdate
from datetime import date, timedelta

from pycaret.regression import *
import db_connection
import dash_table
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from app import app,cache, dbc_table_to_pandas
from .layouts_predefinidos import elementos 
from preprocesar_base import aplicar_pipeline
from consulta_db_para_estimacion import consulta_modelo_v1

##############
# modelos #####
##############
pc_model = load_model('lr_pc_19Ene2020')
sc_model = load_model('cb_sc_21Ene2020')

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
WHERE rn=1 AND ((edad_actual >10 AND desarrollo='PC') OR (peso_planta >2500 AND desarrollo='PC') OR (edad_actual >3 AND desarrollo='SC'))
ORDER BY edad_actual desc
""" 
@cache.memoize()
def generar_lista_bloques_forzamiento():
    return db_connection.query(consulta)

def query_para_select():
    bloques = generar_lista_bloques_forzamiento()[["bloque","desarrollo"]]
    opciones = [{"label":row["bloque"],"value":row["bloque"]} for _,row in bloques.iterrows()]
    return opciones

@cache.memoize()
def extraer_datos_bloque_para_modelo(bloque):
    bloque_como_lista = [tuple(set([bloque]))]
    consulta_sin_procesar = db_connection.query(consulta_modelo_v1,  bloque_como_lista)
    return consulta_sin_procesar

def aplicar_modelo(df):
    x_pc,x_sc = aplicar_pipeline(df)
    if x_sc.empty:
        return predict_model(pc_model, data=x_pc)
    else:
        return predict_model(sc_model, data=x_sc)

def query_para_grafica(df,bloque):

    # Aplicar modelo de acuerdo con el peso forza
    base = extraer_datos_bloque_para_modelo(bloque)
    base_sensibilidad = base.loc[base.index.repeat(5)].reset_index(drop=True)
    
    #Crear nuevas columnas
    today = date.today()
    dias_dif = [0,7,15,21,29]
    fechas_induccion = [today + timedelta(days=x) for x in dias_dif]
    fechas_cosecha = [x + timedelta(days=140) for x in fechas_induccion]

    base_sensibilidad["finduccion"] = fechas_induccion
    base_sensibilidad["mean_fecha_cosecha"] = fechas_cosecha
    base_sensibilidad['peso_forza'] = df["peso forza proyectado"]/1000

    resultado_sensibilidad = aplicar_modelo(base_sensibilidad)
    #Crear gráfica
    fig = go.Figure()    
    
    fig.add_trace(go.Scatter(x=df["Semanas adicionales"] , 
    y=resultado_sensibilidad["Label"]*resultado_sensibilidad["area"] ,
                        mode='lines+markers',
                        name='lines+markers'))

    fig.update_layout(
    title=f"Proyección de kilos a cosechar bloque {bloque} ",
    xaxis_title="Número de semanas con respecto a la actual",
    yaxis_title="Kilos a cosechar",
    font=dict(
        family="Courier New, monospace",
        size=18,
        color="RebeccaPurple"
    )
)
    return fig
###############
#Layout
##############


bloque_dropdown = dcc.Dropdown(
        id='bloque-peso-forza-dropdown'
    )
peso_forza_graph = dcc.Graph(config={
        'displayModeBar': True},id="peso-forza-graph")


df_pesos = pd.DataFrame(
    {
        "Semanas adicionales": [],
        "peso forza proyectado": [],
    }
)

peso_forza_sensibilidad_table =  dash_table.DataTable(
        id='sensibilidad-peso-forza-table',
        columns=[{"name": "Semanas adicionales", "id": "Semanas adicionales", "editable": False},
        {"name": "peso forza proyectado", "id": "peso forza proyectado", "editable": True},],
        data=df_pesos.to_dict('records')
    )

div_sensibilidad= html.Div([
    bloque_dropdown,
    dbc.Row(            [
                dbc.Col(peso_forza_graph),
                dbc.Col(peso_forza_sensibilidad_table)
                
            ]
        ),
        ]
    )


exportar_a_excel_input = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id="exportar-forzamiento-excel-btn", color="success", className="mr-1"),
        Download(id="download-forzamiento")
    ]
)
form_programacion = dbc.Form([exportar_a_excel_input])

layout = elementos.DashLayout(extra_elements=[div_sensibilidad,form_programacion])

layout.crear_elemento(tipo="table",element_id="bloques-por-forzar-table",  label="Bloques por forzar")
layout.ordenar_elementos(["bloques-por-forzar-table"])


###################
##### Callbacks ###
###################


#Actualizar alertas y dropdown
@app.callback([Output("bloques-por-forzar-table", "children"),Output('bloque-peso-forza-dropdown', "options")], [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='listado-forzamiento':
        data = generar_lista_bloques_forzamiento().round(2)
        opciones = [{"label":row["bloque"],"value":row["bloque"]} for _,row in data[["bloque","desarrollo"]].iterrows()]
        return dbc.Table.from_dataframe(data).children, opciones

    return None

#Actualizar tabla de entrada
@app.callback(Output("sensibilidad-peso-forza-table", "data"), [Input('bloque-peso-forza-dropdown','value')])
def actualizar_select_bloque(bloque):
    if bloque is None:
        raise PreventUpdate

    info_bloque = generar_lista_bloques_forzamiento().query("bloque==@bloque")[["bloque","peso promedio ultimo muestreo"]]
    peso_actual =info_bloque.iat[0,1]
    df_pesos = pd.DataFrame(
    {
        "Semanas adicionales": [0,1,2,3,4],
        "peso forza proyectado": [peso_actual,peso_actual+200,
        peso_actual+400,peso_actual+600,peso_actual+800],
    })

    return df_pesos.to_dict('records')


#Actualizar gráfica con cambios en la tabla

@app.callback(
    Output("peso-forza-graph", 'figure'),
    [Input('sensibilidad-peso-forza-table', 'data'),
    Input('sensibilidad-peso-forza-table', 'columns')],
    [State('bloque-peso-forza-dropdown','value')]
)
def display_output(rows, columns,bloque):
    if bloque is None:
        raise PreventUpdate

    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    df["peso forza proyectado"] = df["peso forza proyectado"].astype(float)
    return query_para_grafica(df,bloque)



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