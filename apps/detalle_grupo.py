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

lista_grupos = '''WITH grupos_de_siembra AS (
    SELECT DISTINCT descripcion,
    'preforza' as etapa,
    fecha
    FROM grupossiembra
    UNION
    SELECT DISTINCT  descripcion,
    'preforza' as etapa,
    fecha
    FROM grupos2dacosecha),

    grupos_de_forza AS (
    SELECT DISTINCT descripcion,
    'postforza' as etapa,
    fecha
    FROM gruposforza
    UNION
    SELECT DISTINCT  descripcion,
    'postforza' as etapa,
    fecha
    FROM gruposforza2),

    grupos_de_semilero AS ( SELECT DISTINCT descripcion AS label,
    descripcion AS value,
    'semillero' as etapa,
    fecha
    FROM grupossemillero
    ORDER BY fecha)
    
SELECT *
  FROM (SELECT DISTINCT descripcion AS label,
descripcion AS value,
etapa,
fecha
FROM grupos_de_siembra
UNION 
SELECT DISTINCT descripcion AS label,
descripcion AS value,
etapa,
fecha
FROM grupos_de_forza
UNION
SELECT DISTINCT label,
value,
etapa,
fecha
FROM grupos_de_semilero
       ) AS U
 WHERE U.etapa = %s

ORDER BY fecha'''

calidad_aplicaciones = '''SELECT 
CONCAT('[',bloque,'](', '/',%s,'-detalle-bloque?bloque=',bloque,'#',%s,')' ) as "bloque",
fecha_siembra as "fecha de siembra",
finduccion as "fecha de inducción",
aplicaciones_pendientes as "# de aplicaciones pendientes",
num_aplicaciones_realizadas as "# de aplicaciones realizadas",
aplicaciones_con_retraso as "# de aplicaciones realizadas tardías",
aplicaciones_muy_proximas as "# de aplicaciones realizadas adelantadas"
FROM calidad_aplicaciones
WHERE grupo=%s and categoria = %s'''

peso_forza_grupo_siembra = '''
SELECT llave,
fecha,
ROUND(AVG(valor),2) as promedio
FROM pesoplanta 
WHERE llave IN (
    SELECT concat(desarrollo,descripcion) as llave 
    from blocks_desarrollo
    where grupo_siembra =%s 
)
group by llave,fecha
'''

aplicaciones_grupo = ''' WITH apls as (SELECT blocknumber,
codigo_cedula as "codigo cédula",
fecha,
descripcion_formula as formula
from aplicaciones
WHERE grupo =%s AND etapa2 = %s AND categoria = %s
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

@cache.memoize()
def query_para_select(etapa):
    consulta = db_connection.query(lista_grupos,[etapa])
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

@cache.memoize()
def query_para_tabla(grupo, etapa, categoria):
    return db_connection.query(calidad_aplicaciones, [etapa,categoria,grupo,categoria]).fillna("")

@cache.memoize()
def query_para_tabla_aplicaciones(grupo, etapa, categoria):

    resultado = db_connection.query(aplicaciones_grupo, [grupo,etapa,categoria])
    if resultado.empty==False:
        resultado["fecha aplicación"]=resultado["fecha aplicación"].dt.strftime('%d-%B-%Y')
    return resultado

@cache.memoize()
def query_para_grafica(grupo,categoria,etapa):
    
    #El eje x debe tener como valor meses desde el inicio del grupo de siembra

    if categoria!= 'nutricion':
        return px.scatter()
    if etapa!="preforza":
        return px.scatter()
    
    consulta = db_connection.query(peso_forza_grupo_siembra,[grupo])

    #Crear gráfica
    fig = px.scatter(consulta, x="fecha", y="promedio",color="llave",hover_data=["llave"],title="Peso planta")

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
    if path !='detalle-grupo':
        raise PreventUpdate
    else:
        etapa = url.split("-")[0][1:]
        return query_para_select(etapa)

#Callback para seleccionar estado según search location desde hipervínculo de otro menú
@app.callback(Output("select-grupo", "value"), [Input('url','search')],[State('pathname-intermedio','children')])

def actualizar_valor_select_lote(search, path):
    if "detalle-grupo" not in path:
        raise PreventUpdate

    busqueda = search.split("=")
    if len(busqueda)<2:
        return None
    else:
        return busqueda[1]

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




