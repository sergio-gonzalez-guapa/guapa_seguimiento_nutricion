import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import pandas as pd
from flask_caching import Cache

import locale 
import dash_table
locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

# Exportar a excel
def explorar_celda (celda):
    #Se debe llamar esta función cuando se recorra un th o un td
    if isinstance(celda,str) or isinstance(celda,int) or isinstance(celda,float):
        return celda
    elif celda is None:
        return None
    else:
        return explorar_celda(celda["props"]["children"])

def explorar_fila(fila):
    labels = []
    for celda in fila:
        labels.append(explorar_celda(celda))
    return labels

def dbc_table_to_pandas (tabla):
    dicc_resultado = {}
    for elemento in tabla:
        if elemento["type"] =="Thead":
            dicc_resultado["columnas"] = explorar_fila(elemento["props"]["children"]["props"]["children"])
        if elemento["type"] =="Tbody":
            lista_filas = elemento["props"]["children"]
            datos = []
            for fila in lista_filas:
                datos.append(explorar_fila(fila["props"]["children"]))
            dicc_resultado["labels"] = datos
    
    return pd.DataFrame(dicc_resultado["labels"], columns = dicc_resultado["columnas"]) 


#app = dash.Dash(__name__, suppress_callback_exceptions=True,external_stylesheets=[dbc.themes.FLATLY])
app = dash.Dash(__name__, suppress_callback_exceptions=False,external_stylesheets=[dbc.themes.FLATLY])
cache = Cache(app.server,config={

    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1000,
    "CACHE_IGNORE_ERRORS":False,
    "CACHE_THRESHOLD":30

})
server = app.server

def crear_elemento_visual(tipo,element_id,params=None,encerrado=True):

    elemento=None

    if tipo=="dbc_select":
        label = params["label"]
        
        elemento = dbc.InputGroup(
                [
                    dbc.InputGroupAddon(label, addon_type="prepend"),
                    dbc.Select(id=element_id)
                    
                ]
            )

    elif tipo=="dash_table":

        params_dash_table = {"id":element_id,
        "sort_action":"native",
        "markdown_options":{"link_target": '_self'},
        "fixed_rows":{'headers': True},"fixed_columns":{'headers':True},
        "style_table":{'height': 500, 'overflowX': 'auto','minWidth':"100%"},
        "style_cell":{'height': 'auto',# Esta configuración de style cell junto con overflowx permite tener barra de desplazamiento horizontal para que ninguna celda se alargue verticalmente abruptamente
            'minWidth': '120px', 'width': '120px', 'maxWidth': '120px','whiteSpace': 'pre-line'},
        "style_header":{'backgroundColor': 'white','fontWeight': 'bold',"min-width": 50},
        "filter_action":"native",
        "style_data_conditional":[
            {
                'if': {'row_index': 'odd'},'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]

        }
        
        elemento = dash_table.DataTable(**params_dash_table)

    
    elif tipo=="graph":

        elemento = dcc.Graph(config={
        'displayModeBar': True},id=element_id )

    elif tipo=="slider":

        elemento = dbc.FormGroup(
    [
        dbc.Label(params["label"], html_for=element_id),
        dcc.RangeSlider(
        id=element_id,
        min=params["min"],
        max=params["max"],
        step=1,
        value=params["value"],
        marks=params["marks"]
    ),
        dbc.FormText(
            params["sublabel"],
            color="secondary",
        ),
    ]
)
    elif tipo=="vertical-slider":

        elemento = dbc.FormGroup(
    [
        dbc.Label(params["label"], html_for=element_id),
        dcc.RangeSlider(
        id=element_id,
        min=params["min"],
        max=params["max"],
        step=1,
        value=params["value"],
        marks=params["marks"],
        vertical=True,
        verticalHeight=150
    )
    ]
)
    elif tipo=="checklist":

        elemento = dbc.FormGroup(
    [
        dbc.Label(params["label"], html_for=element_id),
        dbc.Col(
            dbc.Checklist(
                id=element_id,
                options=params["options"],
            ),
            width=8,
        ),
    ],
    row=False,
)
    elif tipo=="number-input":

        elemento = dbc.FormGroup(
    [
        dbc.Label(params["label"], html_for=element_id),
        dbc.Input(id = element_id,type="number", min = params["min"], max=params["max"], step=1),
    ]
)
    elif tipo=="tabs":
        lista_tabs = []
        
        for index,value in enumerate(params["names_list"] ):
            tab_nueva = dbc.Tab(label=value, tab_id="tab-"+str(index))
            lista_tabs.append(tab_nueva)

        elemento = dbc.Tabs(
            lista_tabs,
            id=element_id,
            active_tab="tab-0",
        )

    else:
        raise Exception(f"el tipo de elemento {tipo} no está definido")
    
    
    if encerrado:
        elemento = dbc.Card(
            dbc.CardBody(elemento),
            className="mt-3")

    return elemento


