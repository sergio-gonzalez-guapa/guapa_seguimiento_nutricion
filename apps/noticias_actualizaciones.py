import pandas as pd
import plotly.express as px
pd.options.mode.chained_assignment = None  # default='warn'
import plotly.graph_objs as go
import math

import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

import db_connection
from app import app,cache, crear_elemento_visual, dicc_etapa

################################
# Consultas ####################
################################

#################
# Layout ########
#################

layout = html.Div([
    html.H3("Últimas actualizaciones"),
    html.H5("7 de julio de 2021"),
    html.Div(
   [html.Div('''En la sección de calidad de aplicaciones / comparación por grupos
   ahora es posible visualizar tanto la calidad de las aplicaciones realizadas, 
   como la estimación de aplicaciones pendientes según el tipo de aplicación
   
   '''),
   html.Div(html.Img(src=app.get_asset_url('news_20210707.PNG'), style= {"max-width":"800px","max-height":"800px",
   "width":"auto","height":"auto"}  ))]
)
    ])


##############################
# Funciones  #################
##############################


##############################
# Callbacks  #################
##############################
