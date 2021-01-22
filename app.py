import pandas as pd
import sys
import numpy as np
import pickle
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table
import dash_bootstrap_components as dbc
from urllib.request import urlopen
from dash.dependencies import Input, Output, State
import plotly.express as px
import json

from data_processing import df_grupos_siembra,retorna_bloques_de_gs,retorna_info_bloques_de_gs,retorna_info_aplicaciones_de_gs,df_formulas,retorna_detalle_formula, lotes_historia,retorna_info_estados_bloques,retorna_grafica_peso_planta
import upload_file
import insumos_por_formula
import agregar_comentario
import informacion_por_bloque
import nutricion_preforza_pc


# the style arguments for the sidebar
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',     # this sizes the left hand side of the board to 20%
    'padding': '20px 10px',
    'background-color': 'black'   # this means a light gray
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',   # this was 25%
    'margin-right': '5%',   #this was 5%, by controlling the margins, you control the border
    'padding': '20px 10px'    # this was 20px 10p   The CSS padding properties are used to generate space around an element's content, inside of any defined borders.
                            # i am not sure what this refers to
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': 'white'    # Midnight blue
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'    #Pure (or mostly pure) blue.
}


sidebar = html.Div(
    [
        html.H2("Menu", className="display-4", style={"color":"white"}),
        html.Hr(),
        html.P(
            "Seleccione la acción que desea ejecutar", className="lead",style={"color":"white"}
        ),
        dbc.Nav(
            [
                dbc.NavLink("Información de bloques", href="/page-1", id="page-1-link"),
                dbc.NavLink("Aplicaciones nutrición preforza PC", href="/page-2", id="page-2-link"),
                dbc.NavLink("Insumos por fórmula", href="/page-3", id="page-3-link")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)


app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],
meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],suppress_callback_exceptions = True)
#Supress callback exceptions para no validar elementos de callbacks dinámicos
server = app.server
app.layout = html.Div([dcc.Location(id="url"),sidebar, content])                   #this is the key of the division!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1

# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 4)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False, False
    return [pathname == f"/page-{i}" for i in range(1, 4)]

######################################
## URL callback
######################################

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        return informacion_por_bloque.crear_filtro(lotes_historia)
    elif pathname == "/page-2":
        return nutricion_preforza_pc.crear_filtro(df_grupos_siembra)

    elif pathname == "/page-3":
        return insumos_por_formula.crear_filtro(df_formulas)
    # If the user tries to reach a different page, return a 404 message
    else:
        return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            upload_file.parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


###
# Actualizar tabla histórica de estados
###



@app.callback(
    [Output('data-table-info-bloque', 'data'),
    Output('data-table-info-bloque', 'columns')],
    [Input('lote-dropdown', 'value')])
def actualizar_bloques(lote):
    data = retorna_info_estados_bloques(lote)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data.to_dict('records'),_cols

###
# Actualizar nutrición preforza PC
###

#Actualiza dropdown de bloques según gs
@app.callback(
    [Output('div-gs-nutricion-preforza-pc','children'),
    Output('bloque-nutricion-preforza-pc-dropdown', 'options'),
    Output('bloque-nutricion-preforza-pc-dropdown', 'value')],
    [Input('gs-nutricion-preforza-pc-dropdown', 'value')])
def actualizar_gs_y_dropdown_bloques_nutricion_preforza_pc(gs):

    #Hacer consulta para mostrar bloques del GS
    lista_dicts_bloques = retorna_bloques_de_gs(gs)
    return gs,lista_dicts_bloques,""


#Actualizar div bloque
@app.callback(
    Output('div-bloque-nutricion-preforza-pc','children'),
    [Input('bloque-nutricion-preforza-pc-dropdown', 'value')])
def actualizar_year(bloque):
    return bloque


#Actualizar data table agregado según los div de gs y bloque
@app.callback(
    [Output('data-table-nutricion-preforza-pc', 'data'),
    Output('data-table-nutricion-preforza-pc', 'columns')],
    [Input('div-gs-nutricion-preforza-pc', 'children')])
def actualizar_bloques_nutricion_preforza_pc(gs):

    data = retorna_info_bloques_de_gs(gs)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data_as_dict,_cols


#Actualizar data table con el resumen de aplicaciones por categoria y bloque seleccionado
#Tener en cuenta para cuando vuelva a poner de nuevo el resumen de todas las aplicaciones
# @app.callback(
#     [Output('dt-resumen-aplicaciones-preforza-por-bloque', 'data'),
#     Output('dt-resumen-aplicaciones-preforza-por-bloque', 'columns')],
#     [Input('div-bloque-nutricion-preforza-pc', 'children')])
# def actualizar_resumen_aplicaciones_preforza(bloque):
    
#     data = retorna_resumen_aplicaciones_por_bloque(bloque)
#     _cols=[{"name": i, "id": i} for i in data.columns]
#     data_as_dict = data.to_dict('records')
#     return data_as_dict,_cols


#Actualizar gráfica de peso planta
@app.callback(
    Output('graph-peso-planta', 'figure'),
    [Input('div-bloque-nutricion-preforza-pc', 'children')])
def actualizar_peso_planta_preforza(bloque):
    
    return retorna_grafica_peso_planta(bloque)


#Actualizar data table con las aplicaciones para el bloque seleccionado
@app.callback(
    [Output('data-table-nutricion-preforza-pc-por-bloque', 'data'),
    Output('data-table-nutricion-preforza-pc-por-bloque', 'columns')],
    [Input('div-bloque-nutricion-preforza-pc', 'children')])
def actualizar_aplicaciones_bloques_nutricion_preforza_pc(bloque):
    
    data = retorna_info_aplicaciones_de_gs(bloque)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data_as_dict,_cols


#####
# Actualiza fórmulas
##### 

#Actualiza dropdown de bloques según gs
@app.callback(
    [Output('data-table-detalle-formulas', 'data'),
    Output('data-table-detalle-formulas', 'columns'),
    Output('data-table-detalle-formulas', 'tooltip_data')],
    [Input('formula-dropdown', 'value')])
def actualizar_insumos_por_formula(formula):

    #Hacer consulta para mostrar bloques del GS
    data = retorna_detalle_formula(formula)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')

    tooltip_data=[
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in data[["descripcion"]].to_dict('records')
    ]
    
    return data_as_dict,_cols,tooltip_data



if __name__ == '__main__':
    if sys.platform.startswith('win'):
        app.run_server(debug=True)
    else:
        app.run_server(debug=False,host='0.0.0.0',port=8080)
    

    ##Do not use run server in production environments!
    #app.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=False)
    
    #Hide the UI with dev_tools_ui=False
    #Turn off the component property validation with dev_tools_props_check=False.


