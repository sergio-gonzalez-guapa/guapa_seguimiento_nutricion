import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import plotly.express as px

import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

from app import app,cache,crear_elemento_visual
import db_connection
################################
# Consultas ####################
################################

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


calidad_aplicaciones = '''SELECT 
CONCAT('[',bloque,'](', '/',%s,'-detalle-bloque?bloque=',bloque,'#',%s,')' ) as "bloque",
fecha_siembra as "fecha de siembra",
finduccion as "fecha de inducción",
aplicaciones_esperadas - num_aplicaciones_realizadas as "# de aplicaciones pendientes (programadas - realizadas)",
num_aplicaciones_realizadas as "# de aplicaciones realizadas",
aplicaciones_con_retraso as "# de aplicaciones realizadas con retraso",
aplicaciones_muy_proximas as "# de aplicaciones realizadas anticipadamente"
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

aplicaciones_grupo = ''' WITH apls as (SELECT blocknumber,
codigo_cedula as "codigo cédula",
fecha,
descripcion_formula as formula
from aplicaciones
WHERE grupo =%s AND etapa = %s AND categoria = %s
ORDER BY fecha)

select "codigo cédula",
fecha as "fecha aplicación",
formula,
  string_agg(blocknumber, ', ') as bloques

from apls
group by "codigo cédula",formula,fecha
ORDER BY fecha

'''

#################
# Layout ########
#################

layout = html.Div([
    crear_elemento_visual(tipo="dbc_select",element_id="select-grupo",params={"label":"seleccione un grupo"}),
    html.H1("Calidad de aplicaciones"),
    crear_elemento_visual(tipo="dash_table",element_id='detalle-grupo-table'),
    html.H1("Comparativo de muestreos"),
    crear_elemento_visual(tipo="graph",element_id="peso-planta-graph"),
    html.H1("Aplicaciones del grupo"),
    crear_elemento_visual(tipo="dash_table",element_id='aplicaciones-grupo-table')
    ])


##############################
# Funciones  #################
##############################

dicc_etapa = {"preforza":{"GS":"Post Siembra","RC":"Post Deshija"},
"postforza":{"GF":"Post Forza"},
"semillero":{"GS":"Post Deshija"}}

dicc_categoria = {"nutricion":"nutricion",
"proteccion":"proteccion","herbicidas":"herbicida" ,
"induccion":"induccion","induccion":"induccion","protectorsolar":"protectorsolar"}

@cache.memoize()
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

@cache.memoize()
def query_para_tabla(grupo, etapa, categoria):

    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria) or grupo==None:
        print("hay un error en el bloque",grupo, etapa, categoria)
        return None
    
    prefijo = grupo[0:2]
    if prefijo not in ["GF","GS","RC"]:
        print("hay un error en el prefijo")
        return None

    # etapa_query = dicc_etapa[etapa][prefijo]
    categoria_query = dicc_categoria[categoria]
    
    print("parámetros:",etapa,categoria_query,grupo,categoria_query)
    return db_connection.query(calidad_aplicaciones, [etapa,categoria_query,grupo,categoria_query]).fillna("")

@cache.memoize()
def query_para_tabla_aplicaciones(grupo, etapa, categoria):

    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria) or grupo==None:
        print("hay un error en el bloque",grupo, etapa, categoria)
        return None
    
    prefijo = grupo[0:2]
    if prefijo not in ["GF","GS","RC"]:
        print("hay un error en el prefijo")
        return None

    etapa_query = dicc_etapa[etapa][prefijo]
    categoria_query = dicc_categoria[categoria]
    
    resultado = db_connection.query(aplicaciones_grupo, [grupo,etapa_query,categoria_query])
    resultado["fecha aplicación"]=resultado["fecha aplicación"].dt.strftime('%d-%B-%Y')
    return resultado

@cache.memoize()
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


##############################
# Callbacks  #################
##############################

@app.callback(Output("select-grupo", "options"), [Input('pathname-intermedio','children')],[State("url","pathname")])
def actualizar_select_bloque(path,url):
    etapa = url.split("-")[0][1:]
    if path =='detalle-grupo':
        return query_para_select(etapa)

    return None

#Callback para seleccionar estado según search location desde hipervínculo de otro menú
@app.callback(Output("select-grupo", "value"), [Input('url','search')],[State('pathname-intermedio','children')])

def actualizar_valor_select_lote(search, path):
    if "detalle-grupo" in path:
        busqueda = search.split("=")
        if len(busqueda)<2:
            return None
        else:
            return busqueda[1]
    return None

#Actualización de peso planta y detalle grupo
@app.callback([Output("detalle-grupo-table", "data"),Output('detalle-grupo-table', 'columns'),
Output("aplicaciones-grupo-table", "data"),Output('aplicaciones-grupo-table', 'columns'),
Output("peso-planta-graph", "figure")],
 [Input("select-grupo", "value")],
 [State("url","pathname"),State("url","hash")])
def actualizar_tabla(grupo, path, hash):
    if grupo is None:
        raise PreventUpdate
    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    df= query_para_tabla(grupo,etapa,categoria)
    df_data = df.to_dict('records')
    df_cols =  [{"name": i, "id": i,'presentation':'markdown'} for i in df.columns]

    df_aplicaciones = query_para_tabla_aplicaciones(grupo, etapa, categoria)
    df_aplicaciones_data = df_aplicaciones.to_dict('records')
    df_aplicaciones_cols =  [{"name": i, "id": i,'presentation':'markdown'} for i in df_aplicaciones.columns]
    fig = query_para_grafica(grupo,categoria,etapa)
    
    return df_data,df_cols,df_aplicaciones_data,df_aplicaciones_cols,fig




