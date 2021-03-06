import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import sys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from app import app
from apps import estado_bloques as eb
from apps import calidad_aplicaciones_compartido as shared
from apps import comparar_grupos as cg
from apps import detalle_grupo as dg
from apps import detalle_bloque as db
from apps import programacion_aplicaciones as pa
from apps import alertas_aplicaciones as aa
from apps import forzamiento
from apps import detalle_formula as df
from apps import noticias_actualizaciones as na
#from apps import cargue_muestreos as cm

from db_connection import crear_nueva_conexion


#diccionarios
dicc_tabs = {"preforza":["nutrición","protección","herbicida"], 
        "postforza":["nutrición","inducción","insecticida","protectorsolar","maduración"],
        "semillero":["nutrición","protección","herbicida"]}

        # El tipo de aplicación por defecto es nutrición
dicc_diccs_hrefs = {"preforza": {"Comparación por grupos": ["/preforza-comparar-grupos#nutricion", "comparar-grupos-link"],
"Detalle grupo": ["/preforza-detalle-grupo#nutricion", "detalle-grupo-link"],
"Detalle bloque": ["/preforza-detalle-bloque#nutricion", "detalle-bloque-link"]},
"postforza": {"Comparación por grupos": ["/postforza-comparar-grupos#nutricion", "comparar-grupos-link"],
"Detalle grupo": ["/postforza-detalle-grupo#nutricion", "detalle-grupo-link"],
"Detalle bloque": ["/postforza-detalle-bloque#nutricion", "detalle-bloque-link"]},
"semillero": {"Comparación por grupos": ["/semillero-comparar-grupos#nutricion", "comparar-grupos-link"],
"Detalle grupo": ["/semillero-detalle-grupo#nutricion", "detalle-grupo-link"],
"Detalle bloque": ["/semillero-detalle-bloque#nutricion", "detalle-bloque-link"]}
 }





#Main layout
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Estado de bloques", href="/estado-bloques")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Ver aplicaciones:", header=True),
                dbc.DropdownMenuItem("1. Pre-Forza", href="/preforza-comparar-grupos#nutricion"),
                dbc.DropdownMenuItem("2. Post-Forza", href="/postforza-comparar-grupos#nutricion"),
                dbc.DropdownMenuItem("3. Semillero", href="/semillero-comparar-grupos#nutricion")
            ],
            nav=True,
            in_navbar=True,
            label="Calidad de aplicaciones",
        ),
        dbc.NavItem(dbc.NavLink("Programación de aplicaciones", href="/programacion-aplicaciones")),
        dbc.NavItem(dbc.NavLink("Alerta de aplicaciones", href="/alertas-aplicaciones")),
        dbc.NavItem(dbc.NavLink("Bloques por forzar", href="/listado-forzamiento"))
    ],
    brand="Seguimiento de aplicaciones",
    brand_href="/",
    color="primary",
    dark=True,
)


url_bar_and_content_div = html.Div([navbar,
    dcc.Location(id='url', refresh=False),
    html.Div(id='main-content'),
    html.Div(id="pathname-intermedio",hidden=True) #dejar este div invisible
])

# index layout
app.layout = url_bar_and_content_div

#elementos de layout por default
dicc_hrefs = {"Comparación por grupos": ["/preforza-comparar-grupos", "comparar-grupos-link"],
"Detalle grupo": ["/preforza-detalle-grupo", "detalle-grupo-link"],
"Detalle bloque": ["/preforza-detalle-bloque", "detalle-bloque-link"]}

titulo_funcionalidad = "Comparación de grupos de siembra"
lista_nombres_tabs =["Nutrición","Fungicidas","Herbicidas"]



# "complete" layout to supress callback exceptions
app.validation_layout = html.Div([
    url_bar_and_content_div,
    eb.layout,
    db.layout,
    dg.layout,
    aa.layout,
    pa.layout,
    forzamiento.layout,
    shared.crear_layout_validacion(dicc_hrefs,titulo_funcionalidad, lista_nombres_tabs),
    cg.layout,
    df.layout,
    na.layout
    
])

@app.callback([Output('main-content', 'children'),Output('pathname-intermedio','children')],
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return na.layout, 'Home'     

    if pathname == '/estado-bloques':
        return eb.layout, 'estado-bloques'

    if pathname == '/alertas-aplicaciones':
        return aa.layout, 'alertas-aplicaciones'
    
    if pathname == '/programacion-aplicaciones':
        return pa.layout, 'programacion-aplicaciones'

    if pathname == '/listado-forzamiento':
        return forzamiento.layout, 'listado-forzamiento'

    if pathname == '/detalle-formula':
        return df.layout, 'detalle-formula'

    comando = "selección inválida"
    funcionalidad="selección inválida"
    if pathname is None:
        raise PreventUpdate
    pathname.split("-")[0][1:] 
    
    if pathname is not None:
        agrupacion = pathname.split("-")[0][1:] 
        comando = agrupacion if agrupacion in ["preforza","postforza","semillero"] else "selección inválida"
        funcionalidad = "-".join(pathname.split("-")[1:])
    #Comparar grupos
    
    if comando!="selección inválida":

        funciones_validas= ['comparar-grupos','detalle-grupo',"detalle-bloque"]
        if funcionalidad not in funciones_validas:
            return "404", "404"
        
        tipo_grupo = "siembra" if comando == "preforza" else "forza" if comando=="postforza" else "semillero"
        dicc_funcion = {"comparar-grupos":"comparar grupos de "+tipo_grupo,
        "detalle-grupo":"detalle grupo de "+tipo_grupo, "detalle-bloque":"detalle bloque"}

        tabs_categorias_aplicaciones = dicc_tabs[comando] + ["todas"] if funcionalidad=='detalle-bloque' else dicc_tabs[comando]

        resultado = shared.crear_layout(dicc_diccs_hrefs[comando],dicc_funcion[funcionalidad], tabs_categorias_aplicaciones)
        return resultado, funcionalidad
    else:

        return '404',"404"


@app.callback(Output("contenido-funcionalidad", "children"), [Input("url", "hash")],[State('url', 'pathname')])
def switch_tab(hash, path):
    funcionalidad = "-".join(path.split("-")[1:])
    #Tener en cuenta cambio de hash a vacío!
    if funcionalidad =="detalle-grupo":
        return dg.layout
    elif funcionalidad =="detalle-bloque":
        return db.layout
    elif funcionalidad=="comparar-grupos":
        return cg.layout
    else:
        return None

    

if __name__ == '__main__':

    if sys.platform.startswith('win'):
        app.run_server(debug=True)
    else:
        app.run_server(debug=False,host='0.0.0.0',port=8080)