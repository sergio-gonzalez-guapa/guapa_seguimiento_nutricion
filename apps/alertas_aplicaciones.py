import pandas as pd

import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_extensions.snippets import send_bytes
from dash.exceptions import PreventUpdate


import db_connection
from app import app,cache, dbc_table_to_pandas, crear_elemento_visual,export_excel_func
from .layouts_predefinidos import elementos 

################################
# Consultas ####################
################################

consulta_aplicaciones_preforza = '''
WITH aplicaciones_ordenadas AS (
    SELECT bloque, etapa,grupo,fecha::date,
    codigo_formula,
    descripcion_formula,
    categoria,
    row_number() over (partition by bloque
                                    order by fecha desc) as rn
    FROM aplicaciones 
    /* Esta es la clave para controlar por estado del cultivo */
    WHERE bloque in (SELECT bloque FROM blocks_desarrollo WHERE finduccion is null ) AND
    categoria = 'nutricion'
    AND etapa in %s
    AND grupo is not NULL
    AND bloque is not NULL
    ORDER BY blocknumber, fecha)

SELECT bloque,
        grupo,
        fecha,
        descripcion_formula,
        DATE_PART('day',now()-fecha)::integer as dias_desde_ultima_aplicacion
FROM aplicaciones_ordenadas 

WHERE rn = 1
'''

consulta_aplicaciones_posforza = '''
WITH aplicaciones_ordenadas AS (
    SELECT bloque, etapa,grupo,fecha::date,
    codigo_formula,
    descripcion_formula,
    categoria,
    row_number() over (partition by bloque
                                    order by fecha desc) as rn
    FROM aplicaciones 
    /* Esta es la clave para controlar por estado del cultivo */
    WHERE bloque not in (SELECT bloque FROM cosecha_resumen) AND
    categoria = 'nutricion'
    AND etapa in %s
    AND grupo is not NULL
    AND bloque is not NULL
    ORDER BY blocknumber, fecha)

SELECT bloque,
        grupo,
        fecha,
        descripcion_formula,
        DATE_PART('day',now()-fecha)::integer as dias_desde_ultima_aplicacion
FROM aplicaciones_ordenadas 

WHERE rn = 1
'''

consulta_aplicaciones_semillero= '''
WITH aplicaciones_ordenadas AS (
    SELECT bloque, etapa,grupo,fecha::date,
    codigo_formula,
    descripcion_formula,
    categoria,
    row_number() over (partition by bloque
                                    order by fecha desc) as rn
    FROM aplicaciones 
    /* Esta es la clave para controlar por estado del cultivo */
    WHERE blocknumber in (SELECT blocknumber FROM siembra WHERE estado in ('3','7')) AND
    categoria = 'nutricion'
    AND etapa in %s
    AND grupo is not NULL
    AND bloque is not NULL
    ORDER BY blocknumber, fecha)

SELECT bloque,
        grupo,
        fecha,
        descripcion_formula,
        DATE_PART('day',now()-fecha)::integer as dias_desde_ultima_aplicacion
FROM aplicaciones_ordenadas 

WHERE rn = 1
'''

consulta_bloques_nuevos = """SELECT bloque,
fecha_siembra,
DATE_PART('day',now()-fecha_siembra)::integer AS dias_sin_aplicacion
FROM blocks_desarrollo 
WHERE finduccion is null 
AND bloque NOT IN (select distinct bloque 
FROM aplicaciones)
"""


#################
# Layout ########
#################


# nombres_tabs_nutricion = ["preforza","semillero","postforza"]

# def crear_tabs (lista_nombres,id_objeto):
#     lista_tabs = []

#     for index,value in enumerate(lista_nombres):
#         tab_nueva = dbc.Tab(label=value, tab_id="tab-"+str(index))
#         lista_tabs.append(tab_nueva)


#     return dbc.Tabs(
#             lista_tabs,
#             id=id_objeto,
#             active_tab="tab-0",
#         )

# tabs_alertas_nutricion = crear_tabs(nombres_tabs_nutricion,"tabs-alertas-nutricion")

tabs_alertas_nutricion = crear_elemento_visual(tipo="tabs",element_id="tabs-alertas-nutricion",
params={"names_list":["preforza","semillero","postforza"]})


layout = html.Div([
    tabs_alertas_nutricion,
    crear_elemento_visual(tipo="export-excel",element_id='exportar-alertas-aplicaciones-excel-btn',
params={"download_id":"download-alertas-aplicaciones"}),

    crear_elemento_visual(tipo="dash_table",element_id='aplicaciones-pendientes-table'),

    crear_elemento_visual(tipo="export-excel",element_id='exportar-alertas-bloques-excel-btn',
params={"download_id":"download-alertas-bloques"}),

    crear_elemento_visual(tipo="dash_table",element_id='bloques-nuevos-table')
    
    ])

##############################
# Funciones  #################
##############################

@cache.memoize()
def generar_alertas_bloques_actuales (etapa, at):

    consulta= pd.DataFrame()
    if "Post Siembra" in etapa:
        consulta= db_connection.query(consulta_aplicaciones_preforza,[etapa])
    elif "Post Forza" in etapa:
        consulta= db_connection.query(consulta_aplicaciones_posforza,[etapa])
    else: 
        consulta= db_connection.query(consulta_aplicaciones_semillero,[etapa])

    consulta["fecha"]= pd.to_datetime(consulta["fecha"]).dt.strftime('%d-%B-%Y')
    #Agrega por lote si está en preforza
    variables_agrupadoras = ['fecha','descripcion_formula',"lote", 'grupo','dias_desde_ultima_aplicacion']
    if at in ("tab-0","tab-1"):
        consulta["lote"] = consulta["bloque"].str.slice(start=2, stop=4)
    else:
        variables_agrupadoras.remove("lote")

    data = consulta.groupby(variables_agrupadoras,dropna=False)['bloque'].apply(', '.join).reset_index()
    
    data.query("dias_desde_ultima_aplicacion<=100",inplace=True)

    data["bloques_pendientes"] = data["grupo"].str.cat(data["bloque"], sep=':')
    data["bloques_pendientes"] = data["bloques_pendientes"].astype(str)
    data.drop(["bloque","grupo"],axis=1,inplace=True)

    variables_agrupadoras.remove("grupo")
    data = data.groupby(variables_agrupadoras,dropna=False)['bloques_pendientes'].apply('\n---------------------\n'.join).reset_index()
    data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)

    return data

@cache.memoize()
def generar_alertas_bloques_nuevos ():

    aplicaciones = db_connection.query(consulta_bloques_nuevos)
    aplicaciones["fecha_siembra"]= pd.to_datetime(aplicaciones["fecha_siembra"]).dt.strftime('%d-%B-%Y')
    data = aplicaciones.groupby(['fecha_siembra','dias_sin_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
    data.sort_values(by="dias_sin_aplicacion",ascending=False,inplace=True)

    return data

###################
##### Callbacks ###
###################

#Actualizar alertas

@app.callback(Output("aplicaciones-pendientes-table", "data"),
Output('aplicaciones-pendientes-table', 'columns'),
 [Input('pathname-intermedio','children'),
 Input("tabs-alertas-nutricion", "active_tab")])
def actualizar_select_bloque(path, at):
    if path =='alertas-aplicaciones':
        etapa =  ['Post Siembra','Post Deshija']
        if at =="tab-1":
            etapa = ["Post Poda"]
        if at =="tab-2":
            etapa = ["Post Forza",	"Post Forza"]

        etapa = tuple(set(etapa))

        df = generar_alertas_bloques_actuales(etapa,at)
        

        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

    return None


@app.callback(Output("bloques-nuevos-table", "data"),
Output('bloques-nuevos-table', 'columns'), [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='alertas-aplicaciones':
        df = generar_alertas_bloques_nuevos()
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

    return None, None

#Exportación a excel
@app.callback(
Output("download-alertas-aplicaciones", "data"),
[Input("exportar-alertas-aplicaciones-excel-btn", "n_clicks")],
[State("aplicaciones-pendientes-table", "data")])
def download_as_csv(n_clicks, table_data):
    return export_excel_func(n_clicks, table_data, "alertas_aplicaciones.xlsx")

@app.callback(
Output("download-alertas-bloques", "data"),
[Input("exportar-alertas-bloques-excel-btn", "n_clicks")],
[State("bloques-nuevos-table", "data")])
def download_as_csv(n_clicks, table_data):

    return export_excel_func(n_clicks, table_data, "alertas_bloques_nuevos.xlsx")