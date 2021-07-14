from dash_bootstrap_components._components.Button import Button
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
CONCAT('[',codigo_formula,'](', '/detalle-formula?codigo=',REPLACE(codigo_formula,' ','_'),')' ) as "código fórmula",
descripcion_formula as formula,
motivo,
dias_diferencia as "dias desde la aplicación anterior",
CASE 
    WHEN    calidad in (0,1) THEN 'adelantada'
    WHEN    calidad in (3,4) THEN 'tardía'
    ELSE 'en el rango'
    END AS color,
CASE 
    WHEN    calidad in (0,1) THEN 1
    WHEN    calidad in (3,4) THEN 3
    ELSE 2
    END AS calificacion

from aplicaciones 
WHERE bloque =%s AND etapa2 = %s AND categoria = %s
ORDER BY fecha'''

aplicaciones_bloque_todas = '''SELECT distinct blocknumber,
codigo_cedula as "codigo cédula",
fecha,
descripcion_formula as formula,
motivo,
 'sin calificar' as color,
0 as calificacion

from aplicaciones 
WHERE bloque =%s AND etapa2 = %s
ORDER BY fecha'''

aplicaciones_pendientes_bloque = '''SELECT bloque,
fecha,
categoria,
etapa,
etapa2,
-1 as calificacion,
'pendiente' as color,
'pendiente' as formula
from aplicaciones_pendientes
WHERE bloque =%s AND etapa2 = %s AND categoria = %s
ORDER BY fecha'''

peso_planta_bloque = '''SELECT *
from pesoplanta where llave =%s '''

fechas_bloque = """
select fecha_siembra,
 finduccion,
 mediana_fecha_cosecha 
 from blocks_desarrollo
 WHERE bloque=%s

"""

grupo_siembra_bloque = """
SELECT grupo_siembra as grupo
FROM blocks_desarrollo
WHERE bloque = %s"""

grupo_forza_bloque = """
SELECT grupo_forza as grupo
FROM blocks_desarrollo
WHERE bloque = %s"""

grupo_semillero_bloque = """
SELECT grupo_semillero as grupo
FROM blocks_desarrollo
WHERE bloque = %s"""

#################
# Layout ########
#################

layout = html.Div([
    crear_elemento_visual(tipo="dcc_select",element_id="select-bloque",params={"label":"seleccione un bloque"}),
    html.Br(),
    html.A(Button("Volver al grupo",color="primary", className="mr-1"),id="ir-a-grupo-link"),
    html.H1("Calidad de aplicaciones"),
    crear_elemento_visual(tipo="graph",element_id="aplicaciones-bloque-graph"),
    html.H1("Muestreo variable de interés"),
    crear_elemento_visual(tipo="graph",element_id="peso-planta-bloque-graph"),
    html.H1("Detalle aplicaciones"),
    crear_elemento_visual(tipo="dash_table",element_id='aplicaciones-bloque-table')
    ])


##############################
# Funciones  #################
##############################


def query_para_select():
    consulta = db_connection.query(lista_bloques)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

def query_para_link(bloque,etapa):
    grupo = ""
    ruta = etapa
    if etapa =="preforza":
        grupo =  db_connection.query(grupo_siembra_bloque, [bloque])["grupo"][0]
    
    elif etapa =="postforza":
        grupo = db_connection.query(grupo_forza_bloque, [bloque])["grupo"][0]

    elif etapa =="semillero":
        grupo = db_connection.query(grupo_semillero_bloque, [bloque])["grupo"][0]
    
    else:
        grupo="desconocido"

    ruta = f"http://127.0.0.1:8050/{ruta}-detalle-grupo?grupo={grupo}#nutricion" 

    return ruta

#Señalización por colores de aplicaciones de acuerdo con rangos
@cache.memoize()
def query_para_grafica(bloque,etapa,categoria,tabla_aplicaciones):

    if tabla_aplicaciones.empty:
        return px.scatter()
    
    #Hago copia para no afectar tabla referenciada en tabla_aplicaciones
    df = tabla_aplicaciones.copy()
    apls_pendientes= db_connection.query(aplicaciones_pendientes_bloque, [bloque,etapa,categoria])

    if apls_pendientes.empty==False:
        apls_pendientes["fecha_str"]=apls_pendientes["fecha"].dt.strftime('%d-%B-%Y')

    df = df.append(apls_pendientes)
    fig = px.scatter(df, x="fecha", y="calificacion",color="color",
    hover_data=["fecha_str","formula"], color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
                

            })


    consulta= db_connection.query(fechas_bloque, [bloque])
    fecha_siembra = consulta.iloc[0]["fecha_siembra"]
    finduccion = consulta.iloc[0]["finduccion"]
    fecha_cosecha = consulta.iloc[0]["mediana_fecha_cosecha"]

    #Aplicaciones pendientes

    

    if etapa=='preforza':

        if fecha_siembra is not None:
            fig.add_vline(x=fecha_siembra, line_width=3, line_dash="dash", line_color="black")

            fig.add_annotation(x=fecha_siembra, y=2.75,
            text="siembra: " +fecha_siembra.strftime('%d-%B-%Y'),
            showarrow=False)

        if finduccion is not None:
            fig.add_vline(x=finduccion, line_width=3, line_dash="dash", line_color="black")

            fig.add_annotation(x=finduccion, y=2.75,
            text="inducción: " +finduccion.strftime('%d-%B-%Y'),
            showarrow=False)

    if etapa=='postforza':

        if finduccion is not None:
            fig.add_vline(x=finduccion, line_width=3, line_dash="dash", line_color="black")

            fig.add_annotation(x=finduccion, y=2.75,
            text="inducción: " +finduccion.strftime('%d-%B-%Y'),
            showarrow=False)

        if fecha_cosecha is not None:

            fig.add_vline(x=fecha_cosecha, line_width=3, line_dash="dash", line_color="black")
            fig.add_annotation(x=fecha_cosecha, y=2.75,
            text="cosecha: " +fecha_cosecha.strftime('%d-%B-%Y'),
            showarrow=False)

    
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

    #fig =px.violin(consulta,x="fecha" ,y="valor",box=True, points='all',title="Peso planta")
    fig = go.Figure(data=go.Violin(y=consulta['valor'], box_visible=True, line_color='black',
                               meanline_visible=True, fillcolor='lightseagreen', opacity=0.6,
                               points='all',
                               x=consulta['fecha']))
    fig.update_layout(title="peso planta",yaxis_zeroline=False,xaxis_title="Fecha", yaxis_title="peso (gramos)")
    return fig

@cache.memoize()
def query_para_tabla(bloque, etapa, categoria):

    consulta = pd.DataFrame()
    if categoria=='todas':
        consulta= db_connection.query(aplicaciones_bloque_todas, [bloque,etapa])
    
    else:
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


@app.callback([Output("ir-a-grupo-link", "href"),
Output("aplicaciones-bloque-table", "data"),
Output('aplicaciones-bloque-table', 'columns'),
Output("aplicaciones-bloque-graph", "figure"),
Output("peso-planta-bloque-graph", "figure")],
 [Input("select-bloque", "value")],
 [State("url","pathname"),State("url","hash")])
def actualizar_tabla(bloque, path, hash):
    if bloque is None:
      raise PreventUpdate

    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    
    href_grupo= query_para_link(bloque,etapa)
    
    data = query_para_tabla(bloque,etapa,categoria)
    
    fig_aplicaciones = query_para_grafica(bloque,etapa,categoria,data)
    fig_peso_planta = query_para_grafica_peso_planta(bloque,categoria,etapa)

    df = data.drop(["blocknumber","fecha","color","calificacion"],axis=1).rename(columns={"fecha_str":"fecha ejecución"})

    data_final = df.to_dict('records')
    cols_final = [{"name": i, "id": i,'presentation':'markdown'} for i in df.columns]
    return href_grupo,data_final,cols_final ,fig_aplicaciones,fig_peso_planta

