import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc


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