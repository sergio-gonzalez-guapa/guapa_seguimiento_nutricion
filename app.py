import pandas as pd
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

from data_processing import fechas_pendientes, object_file,historia_bloques
import upload_file
import aplicaciones_por_bloque
import agregar_comentario
import informacion_por_bloque


# the style arguments for the sidebar
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',     # this sizes the left hand side of the board to 20%
    'padding': '20px 10px',
    'background-color': '#f8f9fa'   # this means a light gray
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
    'color': '#191970'    # Midnight blue
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'    #Pure (or mostly pure) blue.
}


sidebar = html.Div(
    [
        html.H2("Menu", className="display-4"),
        html.Hr(),
        html.P(
            "Seleccione la acción que desea ejecutar", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Información de bloques", href="/page-1", id="page-2-link"),
                dbc.NavLink("aplicaciones pre-forza pendientes", href="/page-2", id="page-3-link"),
                dbc.NavLink("Aplicaciones ejecutadas por bloque", href="/page-3", id="page-4-link")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)


app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])
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


## URL callback
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        return informacion_por_bloque.crear_filtro(historia_bloques)
    elif pathname == "/page-2":
        return html.Div(dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in fechas_pendientes.columns],
    data=fechas_pendientes.to_dict('records'),editable=True))

    elif pathname == "/page-3":
        return aplicaciones_por_bloque.content
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


@app.callback(
    [Output('data-table-1', 'data'),
    Output('data-table-1', 'columns')],
    [Input('demo-dropdown', 'value')])
def update_table(value):
    data = object_file[value]
    data.drop(["dias"],axis=1, inplace=True)
    data["fechas"]=data.fechas.dt.date
    data["fecha_ejecucion"]=data.fecha_ejecucion.dt.date
    data["ejecucion-plan"]=data["ejecucion-plan"].dt.days
    _cols = [{"name": i, "id": i} for i in data.columns]
    return data.to_dict('records'),_cols



@app.callback(
    [Output('div-lote','children'),
    Output('year-dropdown', 'options'),
    Output('year-dropdown', 'value')],
    [Input('lote-dropdown', 'value')])
def actualizar_lote(lote):

    data = historia_bloques.query("lote==@lote")
    lista_dicts_years = [{"label":"año 20" + str(x),"value":x} for x in data["año"].unique()]
    return lote,lista_dicts_years,""

@app.callback(
    Output('div-year','children'),
    [Input('year-dropdown', 'value')])
def actualizar_year(year):
    return year

@app.callback(
    [Output('data-table-info-bloque', 'data'),
    Output('data-table-info-bloque', 'columns')],
    [Input('div-lote', 'children'),
    Input('div-year', 'children')])
def actualizar_bloques(lote,year):
    data = historia_bloques.query("lote==@lote")
    if year !="":
        data.query("año==@year",inplace=True)
    _cols = [{"name": i, "id": i} for i in data.columns]
    lista_dicts_years = [{"label":"año 20" + str(x),"value":x} for x in data["año"].unique()]
    return data.to_dict('records'),_cols

# @app.callback(
#     [Output('data-table-info-bloque', 'data'),
#     Output('data-table-info-bloque', 'columns')],
#     [Input('year-dropdown', 'value')],
#     [State('lote-dropdown', 'value')]
#     )
# def actualizar_bloques_por_year(year,lote):
#     data = historia_bloques.query("lote==@lote")
#     _cols = [{"name": i, "id": i} for i in data.columns]
#     lista_dicts_years = [{"label":"año 20" + str(x),"value":x} for x in data["año"].unique()]
#     return data.to_dict('records'),_cols

if __name__ == '__main__':
    app.run_server(debug=False,host='0.0.0.0',port=8080)


