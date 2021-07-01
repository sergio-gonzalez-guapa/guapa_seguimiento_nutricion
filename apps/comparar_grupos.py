import pandas as pd
import datetime
import io
from dateutil.relativedelta import relativedelta
import plotly.express as px
import plotly.graph_objects as go

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import Download
from dash_extensions.snippets import send_bytes

import db_connection
from app import app,cache, dbc_table_to_pandas,crear_elemento_visual, export_excel_func


################################
# Consultas ####################
################################

calidad_grupos = """select CONCAT('[',grupo,'](', '/',%s,'-detalle-grupo?grupo=',grupo,'#',%s,')' ) as "grupo", 
grupo as "nombre grupo",
min(fecha_siembra) as "fecha inicio siembra",
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) as numero_bloques,
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) - SUM(CASE WHEN finduccion IS NOT NULL THEN 1 ELSE 0 END) as bloques_por_forzar,
max(aplicaciones_con_retraso) as max_aplicaciones_tardias,
max(aplicaciones_muy_proximas) as max_aplicaciones_adelantadas,
max(aplicaciones_pendientes) as max_aplicaciones_pendientes

from calidad_aplicaciones 
WHERE etapa2 =%s and categoria=%s
group by(grupo)
order by 2"""

calidad_aplicaciones_mensual2 = """ 
    SELECT grupo,
            date_trunc('month', fecha) as mes,
            1 as conteo,
            CASE WHEN calidad in (0,1) THEN 'adelantada'
                WHEN calidad =2 THEN 'en el rango'
                WHEN calidad in (3,4) THEN 'tardía'
                ELSE 'validar'
                END AS calidad

        FROM  aplicaciones
        WHERE etapa2 = %s and categoria = %s AND EXTRACT(YEAR FROM fecha) =%s
        """

aplicaciones_pendientes_mensual = """ 
    SELECT grupo,
            date_trunc('month', fecha) as mes,
            1 as conteo,
            'pendiente' AS calidad

        FROM  aplicaciones_pendientes
        WHERE etapa2 = %s and categoria = %s AND EXTRACT(YEAR FROM fecha) =%s
        """
#################
# Layout ########
#################

current_year = datetime.date.today().year

checklist_estado_forza = crear_elemento_visual(tipo="checklist",element_id="estado-forza-grupos-checklist",
params={"label":"Estado de forzamiento","options":[
                    {"label": "Forzado", "value": 1},
                    {"label": "No forzado", "value": 3},
                    {"label": "Parcialmente forzado","value": 5},
                ]})

def label_aplicaciones (i):
    if i==5:
        return "5+"
    elif i==-1:
        return "<0"
    else:
        return str(i)



boton_aplicar_filtros = dbc.FormGroup(
    [
        dbc.Col(
            dbc.Button("Aplicar filtros",id="filtrar-grupos-btn", color="primary", className="mr-1"),
            width=10,
        ),
        html.Br()
    ],
    row=True,
)
form_checboxes =dbc.Row(
    [
        dbc.Col(checklist_estado_forza)
    ],
    form=True
)

form_boton = dbc.Form([boton_aplicar_filtros])
#Inicializo el layout
graficas_calidad = html.Div([
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='crossfilter-xaxis-column',
                options=[{'label': i, 'value': i} for i in list(range(2014,2022))],
                value=2021
            ),
            dcc.RadioItems(
                id='crossfilter-xaxis-type',
                options=[{'label': i, 'value': i} for i in ['absoluto', 'porcentual']],
                value='absoluto',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='crossfilter-yaxis-column',
                options=[{'label': i, 'value': i} for i in list(range(2014,2022))],
                value=2021
            ),
            dcc.RadioItems(
                id='crossfilter-yaxis-type',
                options=[{'label': i, 'value': i} for i in ['tardías', 'adelantadas','pendientes']],
                value="tardías",
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(
            id='calidad-aplicaciones-mensual-graph'
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(id='calidad-aplicaciones-por-grupo-graph')
    ], style={'display': 'inline-block', 'width': '49%'})
])


layout = html.Div([
    html.H5("", id="comparar-grupos-etapa"),
    html.H5("", id="comparar-grupos-categoria"),
    html.H5("", id="h3-rango-inferior"),
html.H5("", id="h3-rango-superior"),
#form_checboxes,
html.H5("", id="h3-dias-objetivo"),
 #form_boton,
 html.H1("Calidad de aplicaciones"),
 graficas_calidad,
 dcc.Store(id='tabla-calidad-grupos'),
    #crear_elemento_visual(tipo="graph",element_id="calidad-aplicaciones-mensual-graph"),
html.H1("Calidad de aplicaciones por grupos"),
        dbc.Col(
            dbc.Button("Exportar a Excel",id="exportar-comparacion-btn", color="success", className="mr-1"),
            width=10,
        ),
        Download(id="download-comparacion"),
    crear_elemento_visual(tipo="dash_table",element_id='comparar-grupos-table'),
    
    
    ])

##############################
# Funciones  #################
##############################


#@cache.memoize()
def consulta_grafica_por_fecha(etapa,categoria_query,year):
    return  db_connection.query(calidad_aplicaciones_mensual2, [str(etapa),str(categoria_query),year])

@cache.memoize()
def consulta_grafica_pendientes_por_fecha(etapa,categoria_query,year):
    return  db_connection.query(aplicaciones_pendientes_mensual, [etapa,categoria_query,year])

def query_para_grafica(etapa, categoria,escala,year):
    consulta_pendientes = consulta_grafica_pendientes_por_fecha(etapa,categoria,year)
    consulta =consulta_grafica_por_fecha(etapa,categoria,year)
    consulta = consulta.append(consulta_pendientes)
    
    if consulta.empty:
        print("consulta vacía")
        return px.scatter()

    consulta_agrupada = consulta.groupby(["mes","grupo","calidad"])["conteo"].sum().reset_index()
    fig = px.scatter()
    if escala=="porcentual":
        fig = px.histogram(consulta_agrupada, x="mes", y="conteo",color="calidad",
    color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
               },
    category_orders  ={ "calidad": ["adelantada","en el rango","tardía"]} ,
    labels={ # replaces default labels by column name
                "total": "total aplicaciones", "mes": "mes de aplicación"
            },     

    barnorm="percent",
    title = "por fecha de aplicación")

    else: 
        fig = px.bar(consulta_agrupada, x="mes", y="conteo",color="calidad",hover_data=["grupo"],
        color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
        },
        category_orders  ={ "calidad": ["adelantada","en el rango","tardía"]} ,
        title = "por fecha de aplicación")

    return fig

def query_para_grafica_por_grupo(df,indicador):

    if df.empty:
        print("consulta vacía")
        return px.scatter()
    homologacion_indicador = {"tardías":"Número de aplicaciones tardías",
        "adelantadas":"Número de aplicaciones adelantadas",
        "pendientes":"Número de aplicaciones pendientes"}

    fig = px.histogram(df, x="nombre grupo",
    y= homologacion_indicador[indicador],
    histfunc='max',
    title = "por grupo"

               
               )

    return fig

@cache.memoize()
def query_para_tabla(etapa, categoria):

    consulta = db_connection.query(calidad_grupos, [etapa,categoria,etapa,categoria])

    # #Filtrar por estado de forza
    # if estado_forza is not None:
    #     #Posibles valorses que puede tomar la lista: 1,3,5
    #     suma = sum(estado_forza)
    #     if suma==1:
    #         consulta = consulta[consulta.bloques_por_forzar==0]
    #     elif suma==3:
    #         consulta = consulta[consulta.bloques_por_forzar==consulta.numero_bloques]
    #     elif suma==4:
    #         consulta = consulta[ (consulta.bloques_por_forzar==0) | (consulta.bloques_por_forzar==consulta.numero_bloques)]
    #     elif suma==5:
    #         consulta = consulta[ (consulta.bloques_por_forzar>0) & (consulta.bloques_por_forzar<consulta.numero_bloques)]
    #     elif suma==6:
    #         consulta = consulta[ consulta.bloques_por_forzar<consulta.numero_bloques]       
    #     elif suma==8:
    #         consulta = consulta[ consulta.bloques_por_forzar>0]   
    #     else:
    #         consulta = consulta.copy()
    if consulta.empty==False:
        consulta["fecha inicio siembra"]= pd.to_datetime(consulta["fecha inicio siembra"]).dt.date

    return consulta

##############################
# Callbacks  #################
##############################



@app.callback([Output("comparar-grupos-table", "data"),Output('comparar-grupos-table', 'columns'),
Output("h3-dias-objetivo", "children"),
Output("h3-rango-inferior", "children"),
Output("h3-rango-superior", "children"),
Output("comparar-grupos-etapa", "children"),
Output("comparar-grupos-categoria", "children"),
Output('tabla-calidad-grupos','data')],
[Input('pathname-intermedio','children')
],
[State("url","pathname"),
State("url","hash")
])

def actualizar_tabla_calidad_grupos(path,url,hash_url):

    if path !="comparar-grupos":
        raise PreventUpdate
    else:
        etapa = url.split("-")[0][1:]
        categoria = hash_url[1:]
        #Gráfica
        
        #Tabla
        nueva_consulta = db_connection.query("""SELECT dias_entre_aplicaciones, tolerancia_rango_inferior, tolerancia_rango_superior FROM rangos_calidad_aplicaciones
    WHERE etapa2=%s and categoria = %s""",[etapa,categoria])

        
        dias_objetivo = f"días entre aplicaciones: {nueva_consulta.iat[0,0]}"
        limite_inferior = f"límite inferior de tolerancia : {nueva_consulta.iat[0,1]}"
        limite_superior = f"límite superior de tolerancia : {nueva_consulta.iat[0,2]}"
        
        df = query_para_tabla(etapa,categoria)
        df_as_json = df.to_json(date_format='iso', orient='split')

        return df.to_dict('records'), [{"name": i, "id": i,'presentation':'markdown'} for i in df.columns],dias_objetivo ,limite_inferior , limite_superior,etapa,categoria, df_as_json


@app.callback(Output("calidad-aplicaciones-mensual-graph", "figure"),
[Input("crossfilter-xaxis-type", "value"),
Input('crossfilter-xaxis-column', "value"),
Input("comparar-grupos-etapa", "children"),
Input("comparar-grupos-categoria", "children")])
def calidad_aplicaciones_mensual(escala,year,etapa,categoria):
    if etapa is None or categoria is None:
        raise PreventUpdate
        
    histograma = query_para_grafica(etapa,categoria,escala,year)
    return histograma



@app.callback(Output("calidad-aplicaciones-por-grupo-graph", "figure"),
[Input('tabla-calidad-grupos','data'),
Input("crossfilter-yaxis-type", "value"),
Input('crossfilter-yaxis-column', "value")])
def calidad_aplicaciones_por_grupo(data,indicador,year_grupo):
    if data is None:
        raise PreventUpdate

    df = pd.read_json(data, orient='split')

    grupos_consultados = df[(pd.to_datetime(df['fecha inicio siembra']).dt.year == year_grupo)].copy()
    grupos_consultados.rename(columns={"max_aplicaciones_tardias":"Número de aplicaciones tardías",
    "max_aplicaciones_adelantadas":"Número de aplicaciones adelantadas",
    "max_aplicaciones_pendientes":"Número de aplicaciones pendientes"},inplace=True)
    grafica_por_grupo = query_para_grafica_por_grupo(grupos_consultados,indicador)

    return grafica_por_grupo


@app.callback(
Output("download-comparacion", "data"),
[Input("exportar-comparacion-btn", "n_clicks")],
[State("comparar-grupos-table", "data")])
def download_as_csv(n_clicks, table_data):

    return export_excel_func(n_clicks, table_data, "comparacion_grupos.xlsx")