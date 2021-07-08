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
from app import app,cache, crear_elemento_visual, export_excel_func


################################
# Consultas ####################
################################


#######
# Tengo que cruzar con la fecha del grupo
#########

calidad_grupos = """ WITH calidad_grupos as 
    (select CONCAT('[',grupo,'](', '/',%s,'-detalle-grupo?grupo=',grupo,'#',%s,')' ) as grupo, 
    grupo as "nombre grupo",
    SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) as numero_bloques,
    SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) - SUM(CASE WHEN finduccion IS NOT NULL THEN 1 ELSE 0 END) as bloques_por_forzar,
    max(aplicaciones_con_retraso) as max_aplicaciones_tardias,
    max(aplicaciones_muy_proximas) as max_aplicaciones_adelantadas,
    max(aplicaciones_pendientes) as max_aplicaciones_pendientes

    from calidad_aplicaciones 
    WHERE etapa2 =%s and categoria=%s
    group by(grupo) ),

    fechas_grupos AS (select descripcion, fecha from grupossiembra 
    UNION 
    select descripcion, max(fecha) as fecha from grupossemillero group by descripcion
    UNION
    select descripcion, max(fecha) as fecha from gruposforza2 group by descripcion
    UNION
    select descripcion, max(fecha) as fecha from gruposforza group by descripcion
    UNION
    select descripcion, max(fecha) as fecha from grupos2dacosecha group by descripcion)

SELECT grupo,
    "nombre grupo",
    fecha as "fecha inicio grupo",
    numero_bloques,
    bloques_por_forzar,
    max_aplicaciones_tardias,
    max_aplicaciones_adelantadas,
    max_aplicaciones_pendientes
    from calidad_grupos as t1
    LEFT JOIN fechas_grupos as t2
    on t1."nombre grupo" = t2.descripcion
    ORDER BY fecha

"""

calidad_aplicaciones_mensual2 = """ 
    SELECT grupo,
        area/10000 as area_aplicacion,
        lote,
        date_trunc('month', fecha) as mes,
        1 as conteo,
        CASE WHEN calidad in (0,1) THEN 'adelantada'
            WHEN calidad =2 THEN 'en el rango'
            WHEN calidad in (3,4) THEN 'tardía'
            ELSE 'validar'
            END AS calidad

        FROM  aplicaciones as t1
        left join blocks as t2
        on t1.blocknumber=t2.codigo
        WHERE etapa2 = %s and categoria = %s AND EXTRACT(YEAR FROM fecha) =%s
        """

aplicaciones_pendientes_mensual = """ 
    SELECT grupo,
            area/10000 as area_aplicacion,
            lote,
            date_trunc('month', fecha) as mes,
            1 as conteo,
            'pendiente' AS calidad

        FROM  aplicaciones_pendientes as t1
        left join blocks as t2
        on t1.blocknumber=t2.codigo
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
                options=[{'label': i, 'value': i} for i in ['absoluto', 'porcentual','loteyarea']],
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


@cache.memoize()
def consulta_grafica_por_fecha(etapa,categoria_query,year):
    return  db_connection.query(calidad_aplicaciones_mensual2, [str(etapa),str(categoria_query),year])


@cache.memoize()
def consulta_grafica_pendientes_por_fecha(etapa,categoria_query,year):
    return  db_connection.query(aplicaciones_pendientes_mensual, [etapa,categoria_query,year])

def query_para_grafica(etapa, categoria,escala,year):
    consulta_pendientes = consulta_grafica_pendientes_por_fecha(etapa,categoria,year)
    consulta =consulta_grafica_por_fecha(etapa,categoria,year)
    ejecucion_y_pendientes = consulta.append(consulta_pendientes)
    
    if consulta.empty:
        return px.scatter()

    consulta_agrupada = ejecucion_y_pendientes.groupby(["mes","grupo","calidad"])["conteo"].sum().reset_index()

    # consulta_agrupada = 
    
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

    elif escala=="absoluto": 
        fig = px.bar(consulta_agrupada, x="mes", y="conteo",color="calidad",hover_data=["grupo"],
        color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
        },
        category_orders  ={ "calidad": ["adelantada","en el rango","tardía"]} ,
        title = "por fecha de aplicación")

    else: 
        consulta_agrupada_por_lote = ejecucion_y_pendientes.groupby(["mes","lote","calidad"])["area_aplicacion"].sum().reset_index()
        fig = px.bar(consulta_agrupada_por_lote, x="mes", y="area_aplicacion",color="calidad",hover_data=["lote"],
        color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
        },
        category_orders  ={ "calidad": ["adelantada","en el rango","tardía"]} ,
        title = "por fecha de aplicación")

    return fig

def query_para_grafica_por_grupo(df):

    if df.empty:
        print("consulta vacía")
        return px.scatter()

    df_long = pd.melt(df, id_vars='nombre grupo', value_vars=["tardía",
    'adelantada', 'pendiente'],
    value_name='Número máximo de aplicaciones',
    var_name="calidad")

    
    fig = px.histogram(df_long, x="nombre grupo",y='Número máximo de aplicaciones',
    color= "calidad",
    title = "por grupo",
    color_discrete_map={ # replaces default color mapping by value
                "adelantada":"#E5BE01",
                "en el rango": "green",
                "tardía":"#FF8000",
                "pendiente":"#C81D11"
               },
    category_orders  ={ "calidad": ["adelantada","en el rango","tardía"]},
        labels={ # replaces default labels by column name
                "Número máximo de aplicaciones": "total aplicaciones"
            }
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
        consulta["fecha inicio grupo"]= pd.to_datetime(consulta["fecha inicio grupo"]).dt.date

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
Input('crossfilter-yaxis-column', "value")])
def calidad_aplicaciones_por_grupo(data,year_grupo):
    if data is None:
        raise PreventUpdate

    df = pd.read_json(data, orient='split')

    grupos_consultados = df[(pd.to_datetime(df['fecha inicio grupo']).dt.year == year_grupo)].copy()
    grupos_consultados.rename(columns={"max_aplicaciones_tardias":"tardía",
    "max_aplicaciones_adelantadas":"adelantada",
    "max_aplicaciones_pendientes":"pendiente"},inplace=True)
    grafica_por_grupo = query_para_grafica_por_grupo(grupos_consultados)

    return grafica_por_grupo


@app.callback(
Output("download-comparacion", "data"),
[Input("exportar-comparacion-btn", "n_clicks")],
[State("comparar-grupos-table", "data")])
def download_as_csv(n_clicks, table_data):

    return export_excel_func(n_clicks, table_data, "comparacion_grupos.xlsx")