import dash
import dash_bootstrap_components as dbc
import pandas as pd
from flask_caching import Cache

import locale 

locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

#app = dash.Dash(__name__, suppress_callback_exceptions=True,external_stylesheets=[dbc.themes.FLATLY])
app = dash.Dash(__name__, suppress_callback_exceptions=False,external_stylesheets=[dbc.themes.FLATLY])
cache = Cache(app.server,config={

    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1000,
    "CACHE_IGNORE_ERRORS":True,
    "CACHE_THRESHOLD":30

})
server = app.server
