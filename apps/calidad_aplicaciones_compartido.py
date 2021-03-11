import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State

from app import app
from unidecode import unidecode

margen_sidebar = "160px"
##Sidebar

SIDEBAR_STYLE = {
    "height":"100%",
    "width": margen_sidebar,
    "position": "fixed",
    "background-color": "#18bc9c",
    "padding": "1rem 1rem"
}

CONTENT_STYLE = {
    "margin-left": margen_sidebar,
    "padding": "2rem 1rem"
}


def crear_sidebar(dicc_hrefs):
    #Crear navlinks de acuerdo con diccionario:
    lista_navlinks = []
    for k,v in dicc_hrefs.items():
        nuevo_link = dbc.NavLink(k,href=v[0],id=v[1],className="text-primary list-group-item")
        lista_navlinks.append(nuevo_link)

    sidebar = html.Div(
        [
            html.H2(" ", className="sidebar-header", style={"color":"white"}),
            html.Hr(),
            html.P(
                "Seleccione la acción que desea ejecutar", className="lead",style={"color":"white"}
            ),
            dbc.Nav(
                lista_navlinks,
                vertical="sm",
                pills=True,
                className = "list-group list-group-flush",
                fill=True
            ),
        ],
        style=SIDEBAR_STYLE
    )
    return sidebar

def definir_titulo (titulo):
    return html.H3(titulo,id="titulo-funcionalidad")

def crear_tabs (lista_nombres):
    lista_tabs = []

    for index,value in enumerate(lista_nombres):
        tab_nueva = dbc.Tab(label=value, tab_id="tab-"+str(index))
        lista_tabs.append(tab_nueva)


    return dbc.Tabs(
            lista_tabs,
            id="tipo-aplicacion-tabs",
            active_tab="tab-0",
        )

def crear_layout(dicc_hrefs,titulo_funcionalidad, lista_nombres_tabs):
    sidebar = crear_sidebar(dicc_hrefs)
    titulo = definir_titulo (titulo_funcionalidad)
    tabs = crear_tabs (lista_nombres_tabs)
    contenido_funcionalidad = html.Div( id="contenido-funcionalidad")

    return html.Div([sidebar,html.Div([titulo,tabs,contenido_funcionalidad],style=CONTENT_STYLE)]) 

def crear_layout_validacion(dicc_hrefs,titulo_funcionalidad, lista_nombres_tabs):
    return crear_layout(dicc_hrefs,titulo_funcionalidad, lista_nombres_tabs)


label_seleccion = "Seleccione un grupo"
opciones = [
                        {"label": "Option 1", "value": 1},
                        {"label": "Option 2", "value": 2},
                    ]

id_select = "select-grupo"
label_tabla = "Bloques por grupo"
#parametrizar opciones del select
#Parametrizar tabla y creación de links
label_grafica = "Curvas peso planta"

def encerrar_en_tarjeta(children):
    return dbc.Card(
        dbc.CardBody(children),
        className="mt-3")


def crear_layout_select (label_seleccion,opciones,id_select):
    select = dbc.InputGroup(
            [
                dbc.InputGroupAddon(label_seleccion, addon_type="prepend"),
                dbc.Select(
                    options=opciones,
                id=id_select)
                
            ]
        )

    return encerrar_en_tarjeta(select)

def crear_layout_tabla (label_tabla, ):

    table_header = [
        html.Thead(html.Tr([html.Th("First Name"), html.Th("Last Name")]))
    ]

    row1 = html.Tr([html.Td("Arthur"), html.Td("Dent")])
    row2 = html.Tr([html.Td("Ford"), html.Td("Prefect")])
    row3 = html.Tr([html.Td("Zaphod"), html.Td("Beeblebrox")])
    row4 = html.Tr([html.Td("Trillian"), html.Td("Astra")])

    table_body = [html.Tbody([row1, row2, row3, row4])]

    table = dbc.Table(table_header + table_body, bordered=True)

    return encerrar_en_tarjeta([ html.H3(label_tabla),table])


def crear_layout_grafica(label_grafica):
    grafica = dcc.Graph(config={
            'displayModeBar': False
        } )
    return encerrar_en_tarjeta([html.H3(label_grafica),grafica])


@app.callback(Output("url", "hash"), [Input("tipo-aplicacion-tabs", "active_tab")], [State("tipo-aplicacion-tabs","children")])
def switch_tab(at, tabs):
    posicion_tab = int(at.split("-")[1])
    return "#"+unidecode(tabs[posicion_tab]["props"]["label"])