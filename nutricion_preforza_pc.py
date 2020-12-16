import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc


def crear_filtro(df):
    lotes = df.lote.unique()
    lotes.sort()
    lista_dicts_lote = [{"label":"lote " + str(x),"value":x} for x in lotes]
    content =html.Div([
        dcc.Dropdown(
            id='lote-nutricion-preforza-pc-dropdown',
            options=lista_dicts_lote,
            value=1
        ),
        html.Div(id='div-lote-nutricion-preforza-pc',hidden=True),
       # html.Div(
        dash_table.DataTable(
                style_cell={
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0
    },
        id='data-table-nutricion-preforza-pc',
        css=[{
        'selector': '.dash-table-tooltip',
        'rule': 'width: 700px !important; max-width: 700px !important;'
    }]
    )
    #)
    ])
    return content