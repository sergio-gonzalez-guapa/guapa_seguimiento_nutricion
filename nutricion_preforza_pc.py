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
        css=[{
        'selector': '.dash-table-tooltip',
        'rule': 'background-color: white; font-family: monospace; font-size: 15px;  width: max-content; max-width: 200px; top: 100%;left: 50%;margin-left: -60px; white-space: pre-wrap;'
    }],
    tooltip_duration =None,
        style_header={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px'},
        style_cell={'width':'50px'},
            style_data_conditional=[
            {
            'if': {
                'filter_query': '{q1} > 0.7 && {q1} <= 1',
                'column_id': 'q1'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{q1} > 0.5 && {q1} <= 0.7',
                'column_id': 'q1'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{q1} >= 0 && {q1} <= 0.5',
                'column_id': 'q1'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{q2} > 0.7 && {q2} <= 1',
                'column_id': 'q2'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{q2} > 0.5 && {q2} <= 0.7',
                'column_id': 'q2'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{q2} >= 0 && {q2} <= 0.5',
                'column_id': 'q2'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{q3} > 0.7 && {q3} <= 1',
                'column_id': 'q3'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{q3} > 0.5 && {q3} <= 0.7',
                'column_id': 'q3'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{q3} >= 0 && {q3} <= 0.5',
                'column_id': 'q3'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{q4} > 0.7 && {q4} <= 1',
                'column_id': 'q4'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{q4} > 0.5 && {q4} <= 0.7',
                'column_id': 'q4'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{q4} >= 0 && {q4} <= 0.5',
                'column_id': 'q4'
                },
                'backgroundColor': 'red'
            },
            
        ]
    ),
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

