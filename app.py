import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash_extensions import Download
from dash.exceptions import PreventUpdate
from dash_extensions.snippets import send_bytes

import pandas as pd
from flask_caching import Cache
import marko
from bs4 import BeautifulSoup

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

#Exportar dashtable a excel
def export_excel_func(n_clicks, table_data, output_file_name):

    if (not n_clicks) or (table_data is None):
      raise PreventUpdate
      
    df = pd.DataFrame.from_dict(table_data)
    #Extraer texto de markdown
    df = df.applymap(lambda x: ''.join(BeautifulSoup(marko.convert(x)).findAll(text=True)) if isinstance(x, str) else x )

    # download_buffer = io.StringIO()
    # df.to_csv(download_buffer, index=False)
    # download_buffer.seek(0)
    # return dict(content=download_buffer.getvalue(), filename="tabla_comparacion.csv")

    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, output_file_name)




#app = dash.Dash(__name__, suppress_callback_exceptions=True,external_stylesheets=[dbc.themes.FLATLY])
app = dash.Dash(__name__, suppress_callback_exceptions=False,external_stylesheets=[dbc.themes.FLATLY])
cache = Cache(app.server,config={

    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1000,
    "CACHE_IGNORE_ERRORS":False,
    "CACHE_THRESHOLD":30

})
server = app.server


#Diccionarios

dicc_etapa = {"preforza":{"PC":"Post Siembra","SC":"Post Deshija"},
"postforza":{"PC":"Post Forza","SC":"Post 2da Forza"},
"semillero":{"PC":"Post Deshija","SC":"Post Poda"}}

###Funciones dash ######
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
        ],
        "export_format":"xlsx"

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

    elif tipo=="export-excel":

        elemento = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id=element_id, color="success", className="mr-1"),
        Download(id=params["download_id"])
    ]
)

    else:
        raise Exception(f"el tipo de elemento {tipo} no está definido")
    
    
    if encerrado:
        elemento = dbc.Card(
            dbc.CardBody(elemento),
            className="mt-3")

    return elemento


