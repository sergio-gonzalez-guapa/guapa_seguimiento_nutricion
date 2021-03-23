import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from dash.dependencies import Input, Output, State
import db_connection
import plotly.express as px

import numpy as np
from app import app,cache
from .layouts_predefinidos import elementos 

#Inicializo el layout
layout = elementos.DashLayout()
#Agrego los elementos vacíos pero que conforman la estructura
layout.crear_elemento(tipo="select",element_id="select-grupo",  label="seleccione un grupo")
layout.crear_elemento(tipo="table",element_id="detalle-grupo-table",  label="Detalle bloques")
layout.crear_elemento(tipo="graph",element_id="peso-planta-graph",  label="Curva peso planta")
layout.ordenar_elementos(["select-grupo","detalle-grupo-table","peso-planta-graph"])

lista_grupos_siembra = '''WITH grupos_de_siembra AS (
    SELECT DISTINCT descripcion,
    fecha
    FROM grupossiembra
    UNION
    SELECT DISTINCT  descripcion,
    fecha
    FROM grupos2dacosecha)

SELECT DISTINCT descripcion AS label,
descripcion AS value,
fecha
FROM grupos_de_siembra
ORDER BY fecha'''

lista_grupos_forza = '''WITH grupos_de_forza AS (
    SELECT DISTINCT descripcion,
    fecha
    FROM gruposforza
    UNION
    SELECT DISTINCT  descripcion,
    fecha
    FROM gruposforza2)

SELECT DISTINCT descripcion AS label,
descripcion AS value,
fecha
FROM grupos_de_forza
ORDER BY fecha'''

lista_grupos_semillero = '''SELECT DISTINCT descripcion AS label,
descripcion AS value,
fecha
FROM grupossemillero
ORDER BY fecha'''

calidad_aplicaciones = '''SELECT  bloque,
etapa,
categoria,
grupo,
finduccion,
aplicaciones_esperadas - num_aplicaciones_realizadas as "aplicaciones pendientes",
aplicaciones_con_retraso,
aplicaciones_muy_proximas
FROM calidad_aplicaciones
WHERE grupo=%s and categoria = %s'''

peso_forza_grupo_siembra = '''
SELECT *
FROM pesoplanta 
WHERE llave IN (
    SELECT concat(desarrollo,descripcion) as llave 
    from blocks_desarrollo
    where grupo_siembra =%s 
)
'''

info_blocks = '''
SELECT descripcion as bloque,
(area*(1-drenajes))/10000 as area_neta,
poblacion,
rango_semilla
FROM blocks_detalle 
where descripcion in %s
'''

info_blocks_desarrollo_gs = '''
SELECT descripcion as bloque,
desarrollo,
fecha_siembra,
finduccion
FROM blocks_desarrollo 
where grupo_siembra = %s
'''
info_blocks_desarrollo_gf = '''
SELECT descripcion as bloque,
desarrollo,
fecha_siembra,
finduccion
FROM blocks_desarrollo 
where grupo_forza = %s
'''


def query_para_select(etapa):
    consulta=None
    print(etapa)
    if etapa =="preforza":
        consulta = db_connection.query(lista_grupos_siembra)
    elif etapa=="postforza":
        consulta = db_connection.query(lista_grupos_forza)
    elif etapa=="semillero":
        consulta = db_connection.query(lista_grupos_semillero)
    else:
        consulta=pd.DataFrame()

    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

def query_para_tabla(grupo, etapa, categoria):
    dicc_etapa = {"preforza":{"GS":"Post Siembra","RC":"Post Deshija"},
    "postforza":{"GF":"Post Forza"},
    "semillero":{"GS":"Post Deshija"}}

    dicc_categoria = {"nutricion":"fertilizante",
    "fungicidas":"fungicida","herbicidas":"herbicida" ,
    "hormonas":"hormonas"}
    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria) or grupo==None:
        print("hay un error en el bloque",grupo, etapa, categoria)
        return None
    
    prefijo = grupo[0:2]
    if prefijo not in ["GF","GS","RC"]:
        return None

    etapa_query = dicc_etapa[etapa][prefijo]
    categoria_query = dicc_categoria[categoria]
    
    consulta = db_connection.query(calidad_aplicaciones, [grupo,categoria_query])

    table_header = [html.Thead(html.Tr([ html.Th(col) for col in consulta.columns]))]

    rows = []
    for row in consulta.itertuples(index=False):
        #Aquí debo poner la lógica los anchor para el vínculo que me lleve al grupo correspondiente
        dict_tuple = row._asdict()
        new_row=[]
        for k,v in dict_tuple.items():
            if v ==None:
                new_row.append(html.Td(v))
            elif k =="bloque":
                new_row.append(html.Td(dcc.Link(v,href=f"/{etapa}-detalle-bloque?bloque={v}#{categoria}") ))
            else:
                new_row.append(html.Td(v))
        
        rows.append(html.Tr(new_row))
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True)

    return table.children

def query_para_grafica(grupo,categoria,etapa):

    
    #El eje x debe tener como valor meses desde el inicio del grupo de siembra
    #Debo traer la información de los bloques con LLAVE según el GS seleccionado y solo para hash nutrición
    if categoria!= 'nutricion' or etapa!="preforza":
        return px.scatter()
    
    consulta = db_connection.query(peso_forza_grupo_siembra,[grupo])
    if consulta.empty:
        print("consulta vacía")
        return px.scatter()

    agg_dict = {
    "promedio" : pd.NamedAgg(column='valor', aggfunc=lambda ts: ts.mean() )
    }
    resultado = consulta.groupby(["llave","fecha"],dropna=False).agg(**agg_dict).reset_index().round(2)

    fig = px.scatter(resultado, x="fecha", y="promedio",color="llave",
    hover_data=["llave"])
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(
        dtick=1209600000,
        tickformat="Semana %U-%b\n%Y")
    return fig




@app.callback(Output("select-grupo", "options"), [Input('pathname-intermedio','children')],[State("url","pathname")])
@cache.memoize()
def actualizar_select_bloque(path,url):
    etapa = url.split("-")[0][1:]
    if path =='detalle-grupo':
        return query_para_select(etapa)

    return None

#Callback para seleccionar estado según search location
@app.callback(Output("select-grupo", "value"), [Input('url','search')],[State('pathname-intermedio','children')])
@cache.memoize()
def actualizar_valor_select_lote(search, path):
    if "detalle-grupo" in path:
        busqueda = search.split("=")
        if len(busqueda)<2:
            return None
        else:
            return busqueda[1]
    return None

@app.callback([Output("detalle-grupo-table", "children"),Output("peso-planta-graph", "figure")],
 [Input("select-grupo", "value")],
 [State("url","pathname"),State("url","hash")])
@cache.memoize()
def actualizar_tabla(grupo, path, hash):
    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    tabla= query_para_tabla(grupo,etapa,categoria)
    
    fig = query_para_grafica(grupo,categoria,etapa)
    return tabla,fig




