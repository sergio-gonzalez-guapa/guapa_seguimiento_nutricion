import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import plotly.express as px
import numpy as np
import db_connection
from app import app,cache
from .layouts_predefinidos import elementos 

#Inicializo el layout
layout = elementos.DashLayout()
#Agrego los elementos vacíos pero que conforman la estructura
layout.crear_elemento(tipo="select",element_id="select-bloque",  label="seleccione un bloque")
layout.crear_elemento(tipo="table",element_id="detalle-bloque-table",  label="Aplicaciones")
layout.crear_elemento(tipo="graph",element_id="aplicaciones-bloque-graph",  label="días entre aplicaciones")
layout.crear_elemento(tipo="graph",element_id="peso-planta-bloque-graph",  label="Curva de peso planta")
layout.ordenar_elementos(["select-bloque","aplicaciones-bloque-graph","peso-planta-bloque-graph","detalle-bloque-table"])

#Todavía puedo mejorar la creación de llaves para mejorar rendimiento
lista_bloques = '''select concat(desarrollo,descripcion) as label,
concat(desarrollo,blocknumber)  as value
 from blocks_desarrollo
 order by fecha_siembra'''


aplicaciones_bloque = '''SELECT blocknumber,
fecha,
descripcion_formula as formula,
motivo,
DATE_PART('day',dias_diferencia) as dias_diferencia
from aplicaciones
WHERE bloque =%s AND etapa = %s AND categoria = %s
ORDER BY fecha'''

peso_planta_bloque = '''SELECT *
from pesoplanta where llave =%s '''


def query_para_select():
    consulta = db_connection.query(lista_bloques)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

def query_para_tabla(bloque, etapa, categoria):
    dicc_etapa = {"preforza":{"PC":"Post Siembra","SC":"Post Deshija"},
    "postforza":{"PC":"Post Forza","SC":"Post 2da Forza"},
    "semillero":{"PC":"Post Deshija","SC":"Post Poda"}}
     
    dicc_categoria = {"nutricion":"fertilizante",
    "fungicidas":"fungicida","herbicidas":"herbicida" ,
    "hormonas":"hormonas"}
    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria) or bloque==None:
        return None, pd.DataFrame()
    
    etapa_query = dicc_etapa[etapa][bloque[0:2]]
    categoria_query = dicc_categoria[categoria]
    
    consulta= db_connection.query(aplicaciones_bloque, [bloque,etapa_query,categoria_query])
    if consulta.empty==False:
        consulta["fecha_str"]=consulta["fecha"].dt.strftime('%d-%B-%Y')
    
    tabla = dbc.Table.from_dataframe(consulta.drop(["fecha"],axis=1)).children
    return tabla, consulta

def query_para_grafica(tabla_aplicaciones):
    if tabla_aplicaciones.empty:
        return px.scatter()
    tabla_aplicaciones["calificacion"]= tabla_aplicaciones["dias_diferencia"].apply(lambda x: 1 if x is None else 1 if x<10 else 2 if x<20 else 3)
    tabla_aplicaciones["color"]= tabla_aplicaciones["calificacion"].apply(lambda x: "debajo del rango" if x==1 else "en rango" if x==2 else "encima del rango")

    fig = px.scatter(tabla_aplicaciones, x="fecha", y="calificacion",color="color",
    hover_data=["fecha_str","formula"], color_discrete_map={ # replaces default color mapping by value
                "debajo del rango": "purple",
                "en rango": "green",
                "encima del rango": "red"

            })
    fig.update_xaxes(
        dtick=1209600000,
        tickformat="Semana %U-%b\n%Y")
    return fig

def query_para_grafica_peso_planta(bloque,categoria):

    #Por ahora solo retorno peso planta en nutrición
    if categoria!= 'nutricion':
        return px.scatter()
    
    consulta = db_connection.query(peso_planta_bloque,[bloque])

    if consulta.empty:
        return px.scatter()

    fig =px.violin(consulta,x="fecha" ,y="valor",box=True, points='all')
    return fig




@app.callback(Output("select-bloque", "options"), [Input('pathname-intermedio','children')])
@cache.memoize()
def actualizar_select_lote(path):
    if path =='detalle-bloque':
        return  query_para_select()
    return None

#Callback para seleccionar estado según search location
@app.callback(Output("select-bloque", "value"), [Input('url','search')],[State('pathname-intermedio','children')])
@cache.memoize()
def actualizar_valor_select_bloque(search, path):
    if "detalle-bloque" in path:
        busqueda = search.split("=")
        if len(busqueda)<2:
            return None
        else:
            return busqueda[1]
    return None

@app.callback([Output("detalle-bloque-table", "children"),
Output("aplicaciones-bloque-graph", "figure")],
 [Input("select-bloque", "value")],
 [State("url","pathname"),State("url","hash")])
@cache.memoize()
def actualizar_tabla(bloque, path, hash):
    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    tabla, data = query_para_tabla(bloque,etapa,categoria)
    
    fig = query_para_grafica(data)
    return tabla,fig


@app.callback(Output("peso-planta-bloque-graph", "figure"),
 [Input("select-bloque", "value")],
 [State("url","pathname"),State("url","hash")])
@cache.memoize()
def actualizar_grafica_muestreo(bloque, path, hash):
    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    fig = query_para_grafica_peso_planta(bloque,categoria)
    return fig

