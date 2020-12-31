import pandas as pd
import dash_html_components as html
import dash_table
import dash_core_components as dcc


def crear_filtro(df):
    grupossiembra = df.gruposiembra2.unique()
    grupossiembra.sort()
    lista_dicts_gs = [{"label":"grupo " + str(x),"value":x} for x in grupossiembra]

    default_bloques = ['01']
    lista_dicts_bloques = [{"label":x,"value":x} for x in default_bloques]
    # lotes = df.lote.unique()
    # lotes.sort()
    # lista_dicts_lote = [{"label":"lote " + str(x),"value":x} for x in lotes]

    content =html.Div([
        dcc.Dropdown(
            id='gs-nutricion-preforza-pc-dropdown',
            options=lista_dicts_gs,
            value=1
        ),
        dcc.Dropdown(
            id='bloque-nutricion-preforza-pc-dropdown',
            options=lista_dicts_bloques,
            value=1
        ),
        html.Div(id='div-gs-nutricion-preforza-pc',hidden=True),
        html.Div(id='div-bloque-nutricion-preforza-pc',hidden=True),
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

