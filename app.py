import dash
import dash_bootstrap_components as dbc
import pandas as pd
from flask_caching import Cache

import locale 

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
