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
    merge_duplicate_headers=True,
        style_header={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px'},
        style_cell={'width':'50px'},
            style_data_conditional=[
            {
            'if': {
                'filter_query': '{t1} > 0.7 && {t1} <= 1',
                'column_id': 't1'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{t1} > 0.5 && {t1} <= 0.7',
                'column_id': 't1'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{t1} >= 0 && {t1} <= 0.5',
                'column_id': 't1'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{t2} > 0.7 && {t2} <= 1',
                'column_id': 't2'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{t2} > 0.5 && {t2} <= 0.7',
                'column_id': 't2'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{t2} >= 0 && {t2} <= 0.5',
                'column_id': 't2'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{t3} > 0.7 && {t3} <= 1',
                'column_id': 't3'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{t3} > 0.5 && {t3} <= 0.7',
                'column_id': 't3'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{t3} >= 0 && {t3} <= 0.5',
                'column_id': 't3'
                },
                'backgroundColor': 'red'
            },
            {
            'if': {
                'filter_query': '{t4} > 0.7 && {t4} <= 1',
                'column_id': 't4'
                },
                'backgroundColor': 'green'
            },
            {
            'if': {
                'filter_query': '{t4} > 0.5 && {t4} <= 0.7',
                'column_id': 't4'
                },
                'backgroundColor': 'yellow'
            },
            {
            'if': {
                'filter_query': '{t4} >= 0 && {t4} <= 0.5',
                'column_id': 't4'
                },
                'backgroundColor': 'red'
            },
            
        ]
    ),
        dcc.Dropdown(
            id='bloque-nutricion-preforza-pc-dropdown',
            placeholder="Seleccione un bloque"
        ),
        dbc.Row([ dbc.Col([html.H4("Resumen por bloque")])]),
        dbc.Row([
            dbc.Col([ html.H6("Indicador de calidad abierto por métrica y trimestre"),
            dash_table.DataTable(id='dt-calidad-nutricion-preforza-pc-bloque',
            merge_duplicate_headers=True,
            style_cell={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px',
        'maxWidth': 70
    })]), 
            dbc.Col([dcc.Graph(id="graph-peso-planta", config={
        'displayModeBar': False
    } )],width =9)
            
                ]),
        
        html.H4("Detalle de aplicaciones"),
        dash_table.DataTable(
        id='data-table-nutricion-preforza-pc-por-bloque',
        merge_duplicate_headers=True,
        style_header={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '15px'},
        style_cell={'width':'50px'})
        ],
        )
    return content

