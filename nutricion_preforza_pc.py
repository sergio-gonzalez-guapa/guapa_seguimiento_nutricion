import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc

def crear_filtro(df_grupos_siembra):

    lista_dicts_gs = [{"label":row["descripcion"],"value":row["codigo"]} for _,row in df_grupos_siembra.iterrows()]
 
    content =html.Div([
        dcc.Dropdown(
            id='gs-nutricion-preforza-pc-dropdown',
            options=lista_dicts_gs,
            value="256"
        ),
        html.Div(id='div-gs-nutricion-preforza-pc',hidden=True),
        html.Div(id='div-bloque-nutricion-preforza-pc',hidden=True),
        html.H3("Bloques por Grupo de Siembra"),
        dash_table.DataTable(
        id='data-table-nutricion-preforza-pc',
        style_header={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px'
    },
style_cell_conditional=[
        {
            'if': {'column_id': 'dias prom'},
            'width': '50px'
        },
        {
            'if': {'column_id':"num apls"},
            'width': '50px'
        },
        {
            'if': {'column_id':"max dias entre apls"},
            'width': '50px'
        },
        {
            'if': {'column_id':"num diffs mayor a 15"},
            'width': '50px'
        }
    ],),
        dcc.Dropdown(
            id='bloque-nutricion-preforza-pc-dropdown',
            placeholder="Seleccione un bloque"
        ),
        dbc.Row([ dbc.Col([html.H4("Detalle por bloque")])]),
        dbc.Row([dbc.Col([dcc.Graph(id="graph-peso-planta")])]),
        
        html.H4("Detalle de aplicaciones"),
        dash_table.DataTable(
        id='data-table-nutricion-preforza-pc-por-bloque')
        ])
    return content

