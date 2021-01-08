import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc


def crear_filtro(df):
    lista_dicts = [{"label":row["label"],"value":row["value"]} for index,row in df.iterrows()]
    content =html.Div([
        dcc.Dropdown(
            id='lote-dropdown',
            options=lista_dicts,
            value='01__17'
        ),
        html.H3("Información general de bloque")
        ,
        html.Div(dash_table.DataTable(id='data-table-info-bloque'))
    ])
    return content