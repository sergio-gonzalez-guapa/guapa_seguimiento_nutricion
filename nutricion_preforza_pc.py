import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc


def crear_filtro(df_grupos_siembra):

    lista_dicts_gs = [{"label":row["descripcion"],"value":row["codigo"]} for index,row in df_grupos_siembra.iterrows()]
 
    content =html.Div([
        dcc.Dropdown(
            id='gs-nutricion-preforza-pc-dropdown',
            options=lista_dicts_gs,
            value="256"
        ),
        html.Div(id='div-gs-nutricion-preforza-pc',hidden=True),
        html.Div(id='div-bloque-nutricion-preforza-pc',hidden=True),
        dash_table.DataTable(
        id='data-table-nutricion-preforza-pc'),
        dcc.Dropdown(
            id='bloque-nutricion-preforza-pc-dropdown',
            placeholder="Seleccione un bloque"
        ),
        dash_table.DataTable(
        id='data-table-nutricion-preforza-pc-por-bloque')])
    return content

