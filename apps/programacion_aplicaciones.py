import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_bytes
from dash.exceptions import PreventUpdate

import db_connection
from app import app,cache, dbc_table_to_pandas, crear_elemento_visual

from .layouts_predefinidos import elementos 

################################
# Consultas ####################
################################
programacion_ppc = """ WITH formulas_por_bloque as (SELECT DISTINCT formula,
block,
fecha,
area,
codformula 
FROM programacionaplicaciones
WHERE EXTRACT(YEAR FROM fecha) =%s
)
, grupos_actuales as (select bloque,
        CASE 
            WHEN finduccion2 is not null THEN grupo_forza2 
            WHEN deshija is not null THEN grupo_2da_cosecha
            WHEN poda is not null THEN grupo_semillero
            WHEN finduccion is not null THEN grupo_forza
            WHEN siembra is not null THEN grupo_siembra
            ELSE 'VALIDAR GRUPO'
        END as grupo

from historia_bloques
WHERE grupo_siembra IS NOT NULL),

    base_cruce as (

    SELECT formula, block, fecha, area, codformula, grupo
    FROM formulas_por_bloque as t1
    LEFT JOIN grupos_actuales as t2
    ON t1.block=t2.bloque)

select fecha,codformula,
 formula, grupo,
  string_agg(block, ', ') as bloques,
   ROUND(SUM(area)::numeric,2) as area

from base_cruce
WHERE EXTRACT(WEEK FROM fecha) =%s
group by codformula,formula,fecha,grupo
ORDER BY fecha,formula
"""
#################
# Layout ########
#################

exportar_a_excel_input = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id="exportar-programacion-excel-btn", color="success", className="mr-1"),
        Download(id="download-programacion")
    ]
)

layout = html.Div([
    crear_elemento_visual(tipo="dbc_select",element_id="select-year-programacion-aplicaciones",params={"label":"Seleccione el año"}),
    crear_elemento_visual(tipo="number-input",element_id="input-week-programacion-aplicaciones",
    params={"label":"Ingrese el número de la semana","min":1,"max":53}),
    exportar_a_excel_input,
    crear_elemento_visual(tipo="dash_table",element_id='programacion-aplicaciones-table')
    ])
##############################
# Funciones  #################
##############################

def query_para_select():
    current_year, semana_actual, _ = datetime.date.today().isocalendar()
    opciones=[
            {"label": str(current_year-1), "value": current_year-1},
            {"label": str(current_year), "value": current_year},
            {"label": str(current_year+1), "value": current_year+1},
        ]
    
    return opciones, current_year, semana_actual

@cache.memoize()
def query_para_tabla(year, week):
    consulta = db_connection.query(programacion_ppc, [year,week])
    consulta["fecha"]= pd.to_datetime(consulta["fecha"]).dt.strftime('%d-%B-%Y')
    #Pegar grupos con bloques
    consulta["grupo"] = consulta["grupo"].fillna('VALIDAR GRUPO')
    consulta["bloques programados"] = consulta["grupo"].str.cat(consulta["bloques"], sep=':')
    consulta = consulta.groupby(["fecha","codformula","formula"],dropna=False)['bloques programados'].apply(""" \n \n  """.join).reset_index()
    #consulta.sort_values(by="fecha",inplace=True)


    return consulta

##############################
# Callbacks  #################
##############################

@app.callback([Output("select-year-programacion-aplicaciones", "options"),
Output("select-year-programacion-aplicaciones", "value"),
Output("input-week-programacion-aplicaciones", "value")],
 [Input('pathname-intermedio','children')])
def actualizar_select_lote(path):
    if path=="programacion-aplicaciones":
        opciones,year,semana = query_para_select()
        return opciones, year,semana
    return None, None, None

@app.callback(Output("programacion-aplicaciones-table", "data"),
Output('programacion-aplicaciones-table', 'columns'),
[Input('select-year-programacion-aplicaciones','value'),
Input("input-week-programacion-aplicaciones", "value")])
def actualizar_select_bloque(year,week):
    df = query_para_tabla(year,week)
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

#Exportar a excel
@app.callback(
Output("download-programacion", "data"),
[Input("exportar-programacion-excel-btn", "n_clicks")],
[State("programacion-aplicaciones-table", "data")])
def download_as_csv(n_clicks, table_data):
    if (not n_clicks) or (table_data is None):
      raise PreventUpdate
      
    df = pd.DataFrame.from_dict(table_data)
    # download_buffer = io.StringIO()
    # df.to_csv(download_buffer, index=False)
    # download_buffer.seek(0)
    # return dict(content=download_buffer.getvalue(), filename="tabla_comparacion.csv")

    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, "programacion_aplicaciones.xlsx")