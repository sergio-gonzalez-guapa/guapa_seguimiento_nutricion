import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State

import datetime
from dateutil.relativedelta import relativedelta
import db_connection
from app import app,cache

from .layouts_predefinidos import elementos 

#Elementos filtro

year_input = dbc.FormGroup([
    dbc.Label("Seleccione el año", html_for="select-year-programacion-aplicaciones"),

    dbc.Select(
        id="select-year-programacion-aplicaciones",
        options=[
            {"label": "2020", "value": 2020},
            {"label": "2021", "value": 2021},
            {"label": "2022", "value": 2022},
        ],
        value=2021
    )
])

#semana actual 
_, semana_actual, _ = datetime.date.today().isocalendar()

week_input = dbc.FormGroup(
    [
        dbc.Label("Ingrese el número de la semana", html_for="input-week-programacion-aplicaciones"),
        dbc.Input(id = "input-week-programacion-aplicaciones",type="number", min=1, max=52, step=1,value=semana_actual),
    ]
)



form_programacion = dbc.Form([year_input, week_input])

#Inicializo el layout
layout = elementos.DashLayout(extra_elements=[form_programacion])
#Agrego elementos
layout.crear_elemento(tipo="table",element_id="programacion-aplicaciones-table",  label="Aplicaciones programadas según PPC")

layout.ordenar_elementos(["programacion-aplicaciones-table"])

#Consultas
programacion_ppc = """ WITH formulas_por_bloque as (SELECT DISTINCT formula,
block,
fecha,
area,
codformula 
FROM programacionaplicaciones
WHERE EXTRACT(YEAR FROM fecha) =%s
), grupos_actuales as (select bloque,
        CASE 
            WHEN finduccion2 is not null THEN grupo_forza2 
            WHEN deshija is not null THEN grupo_2da_cosecha
            WHEN poda is not null THEN grupo_siembra
            WHEN finduccion is not null THEN grupo_forza
            ELSE grupo_siembra
        END as grupo

from historia_bloques
WHERE grupo_siembra IS NOT NULL), base_cruce as (

SELECT formula, block, fecha, area, codformula, grupo

FROM formulas_por_bloque as t1
LEFT JOIN grupos_actuales as t2
ON t1.block=t2.bloque)

select fecha, formula, grupo, string_agg(block, ', ') as bloques, ROUND(SUM(area)::numeric,2) as area

from base_cruce
WHERE EXTRACT(WEEK FROM fecha) =%s
group by formula,fecha,grupo
ORDER BY fecha,formula
"""

def query_para_tabla(year, week):
    consulta = db_connection.query(programacion_ppc, [year,week])
    consulta["fecha"]= pd.to_datetime(consulta["fecha"]).dt.strftime('%d-%B-%Y')
    return dbc.Table.from_dataframe(consulta).children

@app.callback(Output("programacion-aplicaciones-table", "children"), 
[Input('select-year-programacion-aplicaciones','value'),
Input("input-week-programacion-aplicaciones", "value")])
@cache.memoize()
def actualizar_select_bloque(year,week):
    return query_para_tabla(year,week)
