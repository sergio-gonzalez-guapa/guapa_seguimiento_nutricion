import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

def metodo_principal(lista_bloques, lista_aplicaciones):


    lista_opciones_bloques = []
    for bloque in lista_bloques:
        dicc_temp = {"label":bloque,"value":bloque}
        lista_opciones_bloques.append(dicc_temp)

    lista_opciones_aplicaciones = []
    for aplicacion in lista_aplicaciones:
        dicc_temp = {"label":aplicacion,"value":aplicacion}
        lista_opciones_aplicaciones.append(dicc_temp)

    return html.Div(
        [
            html.Label(["Seleccione el bloque", dcc.Dropdown(id="my-dynamic-dropdown",options=lista_opciones_bloques)]),
            html.Br(),
            html.Label(["Seleccione la aplicación",dcc.Dropdown(id="my-multi-dynamic-dropdown",options=lista_opciones_aplicaciones),
                ]
            ),
            html.Br(),
            dcc.Input(id="input1", type="text", placeholder="Comentario"),
            html.Br(),
            dbc.Button("Enviar", color="primary", className="mr-1"),
        ]
    )