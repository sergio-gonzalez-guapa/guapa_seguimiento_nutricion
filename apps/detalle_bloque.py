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

#Todavía puedo mejorar la creación de llaves para mejorar rendimiento
lista_bloques = '''select concat(desarrollo,descripcion) as label,
concat(desarrollo,blocknumber)  as value
 from blocks_desarrollo
 order by fecha_siembra'''


aplicaciones_bloque = '''SELECT blocknumber,
codigo_cedula as "codigo cédula",
fecha,
descripcion_formula as formula,
motivo,
DATE_PART('day',dias_diferencia) as "dias desde la aplicación anterior"
from aplicaciones
WHERE bloque =%s AND etapa2 = %s AND categoria = %s
ORDER BY fecha'''

rangos_calidad_aplicaciones = '''
SELECT * FROM 
rangos_calidad_aplicaciones
WHERE etapa = %s 
AND
categoria=%s

'''

peso_planta_bloque = '''SELECT *
from pesoplanta where llave =%s '''

#################
# Layout ########
#################

layout = html.Div([
    crear_elemento_visual(tipo="dbc_select",element_id="select-bloque",params={"label":"seleccione un bloque"}),
    html.H1("Calidad de aplicaciones"),
    crear_elemento_visual(tipo="graph",element_id="aplicaciones-bloque-graph"),
    html.H1("Muestreo variable de interés"),
    crear_elemento_visual(tipo="graph",element_id="peso-planta-bloque-graph"),
    html.H1("Detalle aplicaciones"),
    crear_elemento_visual(tipo="dash_table",element_id='detalle-bloque-table')
    ])


##############################
# Funciones  #################
##############################


def query_para_select():
    consulta = db_connection.query(lista_bloques)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones


#Señalización por colores de aplicaciones de acuerdo con rangos
@cache.memoize()
def query_para_grafica(tabla_aplicaciones, etapa_query, categoria_query):

    if tabla_aplicaciones.empty:
        return px.scatter()
    
    consulta = db_connection.query(rangos_calidad_aplicaciones,[etapa_query,categoria_query]).to_dict(orient='list')
    rango_inferior = consulta["tolerancia_rango_inferior"][0]
    rango_superior = consulta["tolerancia_rango_superior"][0]

    #Temporalmente se asume que la primera aplicación se hace a tiempo, caso x==None
    #Hago copia para no afectar tabla referenciada en tabla_aplicaciones
    df = tabla_aplicaciones.copy()

    df["calificacion"]= df["dias desde la aplicación anterior"].apply(lambda x: 2 if x is None else 2 if math.isnan(x) else 1 if x<rango_inferior else 2 if x<rango_superior else 3)
    dicc_calificacion = {1:"debajo del rango",
    2:"en el rango",
    3:"encima del rango"}

    df["color"]= df["calificacion"].apply(lambda x: dicc_calificacion[x])

    fig = px.scatter(df, x="fecha", y="calificacion",color="color",
    hover_data=["fecha_str","formula"], color_discrete_map={ # replaces default color mapping by value
                dicc_calificacion[1]: "purple",
                dicc_calificacion[2]: "green",
                dicc_calificacion[3]: "red"

            })
    fig.update_xaxes(
        dtick=1209600000,
        tickformat="Semana %U-%b\n%Y")
    return fig

@cache.memoize()
def query_para_grafica_peso_planta(bloque,categoria,etapa):

    #Por ahora solo retorno peso planta en nutrición
    if categoria!= 'nutricion':
        return px.scatter()

    if etapa!= 'preforza':
        return px.scatter()

    consulta = db_connection.query(peso_planta_bloque,[bloque])

    if consulta.empty:
        return px.scatter()

    fig =px.violin(consulta,x="fecha" ,y="valor",box=True, points='all',title="Peso planta")
    return fig

@cache.memoize()
def query_para_tabla(bloque, etapa, categoria):

    consulta= db_connection.query(aplicaciones_bloque, [bloque,etapa,categoria])
    if consulta.empty==False:
        consulta["fecha_str"]=consulta["fecha"].dt.strftime('%d-%B-%Y')
    
    return consulta

##############################
# Callbacks  #################
##############################

@app.callback(Output("select-bloque", "options"), [Input('pathname-intermedio','children')])
def actualizar_select_lote(path):
    if path !='detalle-bloque':
        raise PreventUpdate
    else :
        return  query_para_select()

#Callback para seleccionar el bloque según search location
@app.callback(Output("select-bloque", "value"), [Input('url','search')],[State('pathname-intermedio','children')])
def actualizar_valor_select_bloque(search, path):
    if "detalle-bloque" not in path:
        raise PreventUpdate
    else:
        busqueda = search.split("=")
        if len(busqueda)<2:
            return None
        else:
            return busqueda[1]


@app.callback([Output("detalle-bloque-table", "data"),Output('detalle-bloque-table', 'columns'),
Output("aplicaciones-bloque-graph", "figure"),
Output("peso-planta-bloque-graph", "figure")],
 [Input("select-bloque", "value")],
 [State("url","pathname"),State("url","hash")])
def actualizar_tabla(bloque, path, hash):
    if bloque is None:
      raise PreventUpdate

    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    etapa_query = dicc_etapa[etapa][bloque[0:2]]

    data = query_para_tabla(bloque,etapa,categoria)
    
    fig_aplicaciones = query_para_grafica(data, etapa_query, categoria)
    fig_peso_planta = query_para_grafica_peso_planta(bloque,categoria,etapa)

    df = data.drop(["fecha"],axis=1)
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],fig_aplicaciones,fig_peso_planta

