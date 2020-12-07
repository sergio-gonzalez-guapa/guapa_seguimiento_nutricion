import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc

bloques = [10120, 10220, 10320, 10419, 10519, 10619]
lotes = [1,1,1,1,1,1]
grupos = [2,2,2,4,4,4]
areas = [0.39,0.72,0.45,0.26,0.55,0.77]
plantas = [11000,17000,15000,22000,30000,24000]

def crear_filtro(df):
    lista_dicts_lote = [{"label":"lote " + str(x),"value":x} for x in df.lote.unique()]
    default_years = df.query("lote==1")["año"].unique() #Por defecto toma información de lote1
    lista_dicts_years = [{"label":"año 20" + str(x),"value":x} for x in default_years]
    content =html.Div([
        dcc.Dropdown(
            id='lote-dropdown',
            options=lista_dicts_lote,
            value=1
        ),
        dcc.Dropdown(
            id='year-dropdown',
            options=lista_dicts_years
        ),
        html.Div(id='div-lote',hidden=True),
        html.Div(id='div-year',hidden=True),
        html.Div(dash_table.DataTable(id='data-table-info-bloque'))
    ])
    return content