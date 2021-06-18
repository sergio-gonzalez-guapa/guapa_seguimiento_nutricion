import pandas as pd
import datetime
import io
from dateutil.relativedelta import relativedelta
import plotly.express as px
import marko
from bs4 import BeautifulSoup

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import Download
from dash_extensions.snippets import send_bytes

import db_connection
from app import app,cache, dbc_table_to_pandas,crear_elemento_visual
from .layouts_predefinidos import elementos 


################################
# Consultas ####################
################################

calidad_grupos = """select CONCAT('[',grupo,'](', '/',%s,'-detalle-grupo?grupo=',grupo,'#',%s,')' ) as "grupo", 
min(fecha_siembra) as "fecha inicio siembra",
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) as numero_bloques,
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) - SUM(CASE WHEN finduccion IS NOT NULL THEN 1 ELSE 0 END) as bloques_por_forzar,
max(aplicaciones_con_retraso) as max_aplicaciones_tardias,
max(aplicaciones_muy_proximas) as max_aplicaciones_adelantadas,
max(aplicaciones_esperadas - num_aplicaciones_realizadas) as max_aplicaciones_pendientes

from calidad_aplicaciones 
WHERE etapa2 =%s and categoria=%s
group by(grupo)
order by 2"""

calidad_aplicaciones_mensual = """ 
    SELECT mes,
            clasificacion,
            total
        FROM  calidad_aplicaciones_mensual
        WHERE etapa = %s and categoria = %s
        """

#################
# Layout ########
#################

dicc_etapa = {"preforza":"Post Siembra",
"postforza":"Post Forza",
"semillero":"Post Deshija"}

dicc_categoria = {"nutricion":"nutricion",
"fungicidas":"proteccion","herbicidas":"herbicida" ,
"hormonas":"hormonas"}

current_year = datetime.date.today().year
year_input = crear_elemento_visual(tipo="slider",element_id="comparar-grupos-year-slider",
params={"label":"Año de siembra","min":2014,"max":2021,"value":[2014, current_year],
"marks":{ i:str(i) for i in range(2014,current_year+1)}, "sublabel":"Seleccione un rango de años"})

month_input = crear_elemento_visual(tipo="slider",element_id="comparar-grupos-month-slider",
params={"label":"Mes de siembra","min":1,"max":12,"value":[1,12],
"marks":{ i:str(i) for i in range(1,13)}, "sublabel":"Seleccione un rango de mes"})

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


aplicaciones_tardias_input = crear_elemento_visual(tipo="vertical-slider",element_id="comparar-grupos-tardias-slider",
params={"label":"máximo número de aplicaciones tardías","min":0,"max":5,"value":[0,5],
"marks":{ i:label_aplicaciones(i) for i in range(0,6)}})

aplicaciones_adelantadas_input = crear_elemento_visual(tipo="vertical-slider",element_id="comparar-grupos-adelantadas-slider",
params={"label":"máximo número de aplicaciones adelantadas","min":0,"max":5,"value":[0,5],
"marks":{ i:label_aplicaciones(i) for i in range(0,6)}})

aplicaciones_pendientes_input = crear_elemento_visual(tipo="vertical-slider",element_id="comparar-grupos-pendientes-slider",
params={"label":"máximo número de aplicaciones pendientes","min":-1,"max":5,"value":[-1,5],
"marks":{ i:label_aplicaciones(i) for i in range(-1,6)}})


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

form_sliders = dbc.Form([year_input, month_input])

form_checboxes =dbc.Row(
    [
        dbc.Col(checklist_estado_forza),
        dbc.Col(aplicaciones_tardias_input),
        dbc.Col(aplicaciones_adelantadas_input),
        dbc.Col(aplicaciones_pendientes_input)
    ],
    form=True
)

form_boton = dbc.Form([boton_aplicar_filtros])
#Inicializo el layout

layout = html.Div([
    form_sliders,form_checboxes,html.H5("", id="h3-dias-objetivo"),
html.H5("", id="h3-rango-inferior"),
html.H5("", id="h3-rango-superior"),
 form_boton,
 html.H1("Calidad de aplicaciones por mes"),
    crear_elemento_visual(tipo="graph",element_id="calidad-aplicaciones-mensual-graph"),
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
def query_para_grafica(etapa, categoria):

    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria):
        print("hay un error en etapa o categoria", etapa, categoria)
        return px.scatter()

    categoria_query = dicc_categoria[categoria]
    consulta = db_connection.query(calidad_aplicaciones_mensual, [dicc_etapa[etapa],categoria_query])

    if consulta.empty:
        print("consulta vacía")
        return px.scatter()


    fig = px.histogram(consulta, x="mes", y="total",color="clasificacion", histfunc='sum')

    return fig

@cache.memoize()
def query_para_tabla(etapa, categoria,years,months,estado_forza,tardias,adelantadas,pendientes):

    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria):
        print("hay un error en etapa o categoria", etapa, categoria)
        return None
    
    categoria_query = dicc_categoria[categoria]
    
    consulta = db_connection.query(calidad_grupos, [etapa,categoria_query,etapa,categoria_query])

    #Filtrar por estado de forza
    if estado_forza is not None:
        #Posibles valorses que puede tomar la lista: 1,3,5
        suma = sum(estado_forza)
        if suma==1:
            consulta = consulta[consulta.bloques_por_forzar==0]
        elif suma==3:
            consulta = consulta[consulta.bloques_por_forzar==consulta.numero_bloques]
        elif suma==4:
            consulta = consulta[ (consulta.bloques_por_forzar==0) | (consulta.bloques_por_forzar==consulta.numero_bloques)]
        elif suma==5:
            consulta = consulta[ (consulta.bloques_por_forzar>0) & (consulta.bloques_por_forzar<consulta.numero_bloques)]
        elif suma==6:
            consulta = consulta[ consulta.bloques_por_forzar<consulta.numero_bloques]       
        elif suma==8:
            consulta = consulta[ consulta.bloques_por_forzar>0]   
        else:
            consulta = consulta.copy()
    
    consulta["fecha inicio siembra"]= pd.to_datetime(consulta["fecha inicio siembra"]).dt.date

    consulta = consulta[(consulta['fecha inicio siembra']>=datetime.date(years[0],months[0],1)) & (consulta['fecha inicio siembra']<datetime.date(years[1],months[1],1) + relativedelta(months=1))]

    #Filtros por calidad

    lim_sup_tardias = tardias[1]
    lim_sup_adelantadas = adelantadas[1]
    lim_inf_pendientes = pendientes[0]
    lim_sup_pendientes = pendientes[1]

    if lim_sup_tardias ==5:
        consulta = consulta[consulta['max_aplicaciones_tardias']>=tardias[0]]
    else: 
        consulta = consulta[(consulta['max_aplicaciones_tardias']>=tardias[0])&(consulta['max_aplicaciones_tardias']<=tardias[1])]

    if lim_sup_adelantadas ==5:
        consulta = consulta[consulta['max_aplicaciones_adelantadas']>=tardias[0]]
    else: 
        consulta = consulta[(consulta['max_aplicaciones_adelantadas']>=tardias[0])&(consulta['max_aplicaciones_adelantadas']<=tardias[1])]

    if lim_inf_pendientes ==-1 and lim_sup_pendientes==5:
        consulta = consulta.copy()
    elif lim_inf_pendientes ==-1:
        consulta = consulta[consulta['max_aplicaciones_pendientes']<=pendientes[1]]
    elif lim_sup_pendientes ==-5:
        consulta = consulta[consulta['max_aplicaciones_pendientes']>=pendientes[0]]
    else:
        consulta = consulta[(consulta['max_aplicaciones_pendientes']>=pendientes[0])&(consulta['max_aplicaciones_pendientes']<=pendientes[1])]

    table_header = [html.Thead(html.Tr([ html.Th(col) for col in consulta.columns]))]

    rows = []
    for row in consulta.itertuples(index=False):
        #Aquí debo poner la lógica los anchor para el vínculo que me lleve al grupo correspondiente
        dict_tuple = row._asdict()
        new_row=[]
        for k,v in dict_tuple.items():
            if v ==None:
                new_row.append(html.Td(v))
            elif k =="grupo":
                new_row.append(html.Td(dcc.Link(v,href=f"/{etapa}-detalle-grupo?grupo={v}#{categoria}") ))
            else:
                new_row.append(html.Td(v))
        
        rows.append(html.Tr(new_row))
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True)

    return consulta

##############################
# Callbacks  #################
##############################


@app.callback([Output("comparar-grupos-table", "data"),Output('comparar-grupos-table', 'columns'),
Output("h3-dias-objetivo", "children"),
Output("h3-rango-inferior", "children"),Output("h3-rango-superior", "children"),
Output("calidad-aplicaciones-mensual-graph", "figure")],
[Input('pathname-intermedio','children'),
Input("filtrar-grupos-btn", "n_clicks")],[State("url","pathname"),
State("url","hash"), State('comparar-grupos-year-slider',"value"),
State('comparar-grupos-month-slider',"value"),State('estado-forza-grupos-checklist','value'),
State('comparar-grupos-tardias-slider',"value"),State('comparar-grupos-adelantadas-slider',"value"),
State('comparar-grupos-pendientes-slider',"value")])

def actualizar_select_bloque(path,n,url,hash,years,months,estado_forza,tardias,adelantadas,pendientes):

    if path =='comparar-grupos':


        dicc_homologacion = {"preforza":"Post Siembra",
        "postforza":"Post Forza",
        "semillero":"Post Poda",
        "nutricion":"nutricion",
        "herbicidas":"herbicida",
        "proteccion":"proteccion",
        "insecticidas":"insecticida"}

        
        etapa = url.split("-")[0][1:]
        categoria = hash[1:]
        #Gráfica
        histograma = query_para_grafica(etapa,categoria)
        #Tabla
        nueva_consulta = db_connection.query("""SELECT dias_entre_aplicaciones, tolerancia_rango_inferior, tolerancia_rango_superior FROM rangos_calidad_aplicaciones
    WHERE etapa=%s and categoria = %s""",[dicc_homologacion[etapa],dicc_homologacion[categoria] ])

        df = query_para_tabla(etapa,categoria,years,months,estado_forza,tardias,adelantadas,pendientes)
        dias_objetivo = f"* días entre aplicaciones: {nueva_consulta.iat[0,0]}"
        limite_inferior = f"* límite inferior de tolerancia : {nueva_consulta.iat[0,1]}"
        limite_superior = f"* límite superior de tolerancia : {nueva_consulta.iat[0,2]}"
        
        return df.to_dict('records'), [{"name": i, "id": i,'presentation':'markdown'} for i in df.columns],dias_objetivo ,limite_inferior , limite_superior,histograma
    return None,None, "","","", px.scatter()

@app.callback(
Output("download-comparacion", "data"),
[Input("exportar-comparacion-btn", "n_clicks")],
[State("comparar-grupos-table", "data")])
def download_as_csv(n_clicks, table_data):

    if (not n_clicks) or (table_data is None):
      raise PreventUpdate

    df = pd.DataFrame.from_dict(table_data)
    df["grupo"] = df["grupo"].apply(lambda x: ''.join(BeautifulSoup(marko.convert(x)).findAll(text=True)))
    df["fecha inicio siembra"] = df["fecha inicio siembra"].apply(lambda x: ''.join(BeautifulSoup(marko.convert(x)).findAll(text=True)))
    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, "comparacion_grupos.xlsx")