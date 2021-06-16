import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_bytes
from dash.exceptions import PreventUpdate


import db_connection
from app import app,cache, dbc_table_to_pandas, crear_elemento_visual
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


nombres_tabs_nutricion = ["preforza","semillero","postforza"]

def crear_tabs (lista_nombres,id_objeto):
    lista_tabs = []

    for index,value in enumerate(lista_nombres):
        tab_nueva = dbc.Tab(label=value, tab_id="tab-"+str(index))
        lista_tabs.append(tab_nueva)


    return dbc.Tabs(
            lista_tabs,
            id=id_objeto,
            active_tab="tab-0",
        )

tabs_alertas_nutricion = crear_tabs(nombres_tabs_nutricion,"tabs-alertas-nutricion")

# tabs_alertas_nutricion = crear_elemento_visual(tipo="tabs",element_id="tabs-alertas-nutricion",
# params={"names_list":["preforza","semillero","postforza"]})

exportar_a_excel_input = dbc.FormGroup(
    [
        dbc.Button("Exportar a Excel",id="exportar-alertas-excel-btn", color="success", className="mr-1"),
        Download(id="download-alertas")
    ]
)
form_programacion = dbc.Form([exportar_a_excel_input])

layout = elementos.DashLayout(extra_elements=[form_programacion,tabs_alertas_nutricion])

layout.crear_elemento(tipo="table",element_id="aplicaciones-pendientes-table",  label="Últimas aplicaciones nutrición")
layout.crear_elemento(tipo="table",element_id="bloques-nuevos-table",  label="Bloques recien sembrados sin aplicación")
layout.ordenar_elementos(["aplicaciones-pendientes-table","bloques-nuevos-table"])


# layout = html.Div([
#     form_programacion,
#     tabs_alertas_nutricion,
#     crear_elemento_visual(tipo="dash_table",element_id='aplicaciones-pendientes-table'),
#     crear_elemento_visual(tipo="dash_table",element_id='bloques-nuevos-table')
    
#     ])
##############################
# Funciones  #################
##############################

@cache.memoize()
def generar_alertas_bloques_actuales (etapa):
    if "Post Siembra" in etapa:
        return db_connection.query(consulta_aplicaciones_preforza,[etapa])
    elif "Post Forza" in etapa:
        return db_connection.query(consulta_aplicaciones_posforza,[etapa])
    else: 
        return db_connection.query(consulta_aplicaciones_semillero,[etapa])


@cache.memoize()
def generar_alertas_bloques_nuevos ():
    return db_connection.query(consulta_bloques_nuevos)

###################
##### Callbacks ###
###################

#Actualizar alertas
@app.callback(Output("aplicaciones-pendientes-table", "children"), [Input('pathname-intermedio','children'),Input("tabs-alertas-nutricion", "active_tab")])
def actualizar_select_bloque(path, at):
    if path =='alertas-aplicaciones':
        etapa =  ['Post Siembra','Post Deshija']
        if at =="tab-1":
            etapa = ["Post Poda"]
        if at =="tab-2":
            etapa = ["Post Forza",	"Post Forza"]

        etapa = tuple(set(etapa))

        aplicaciones = generar_alertas_bloques_actuales(etapa)
        
        aplicaciones["fecha"]= pd.to_datetime(aplicaciones["fecha"]).dt.strftime('%d-%B-%Y')
        #Agrega por lote si está en preforza
        variables_agrupadoras = ['fecha','descripcion_formula',"lote", 'grupo','dias_desde_ultima_aplicacion']
        if at in ("tab-0","tab-1"):
            aplicaciones["lote"] = aplicaciones["bloque"].str.slice(start=2, stop=4)
        
        else:
            variables_agrupadoras.remove("lote")

        data = aplicaciones.groupby(variables_agrupadoras,dropna=False)['bloque'].apply(', '.join).reset_index()
        
        data.query("dias_desde_ultima_aplicacion<=100",inplace=True)

        data["bloques_pendientes"] = data["grupo"].str.cat(data["bloque"], sep=':')
        data["bloques_pendientes"] = data["bloques_pendientes"].astype(str)
        data.drop(["bloque","grupo"],axis=1,inplace=True)

        variables_agrupadoras.remove("grupo")
        data = data.groupby(variables_agrupadoras,dropna=False)['bloques_pendientes'].apply('\n---------------------\n'.join).reset_index()
        data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)
        return dbc.Table.from_dataframe(data).children

    return None

@app.callback(Output("bloques-nuevos-table", "children"), [Input('pathname-intermedio','children')])
def actualizar_select_bloque(path):
    if path =='alertas-aplicaciones':
        aplicaciones2 = generar_alertas_bloques_nuevos()
        aplicaciones2["fecha_siembra"]= pd.to_datetime(aplicaciones2["fecha_siembra"]).dt.strftime('%d-%B-%Y')
        data2 = aplicaciones2.groupby(['fecha_siembra','dias_sin_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
        data2.sort_values(by="dias_sin_aplicacion",ascending=False,inplace=True)
        return dbc.Table.from_dataframe(data2).children

    return None


@app.callback(
Output("download-alertas", "data"),
[Input("exportar-alertas-excel-btn", "n_clicks")],
[State("aplicaciones-pendientes-table", "children"),
State("bloques-nuevos-table", "children")])
def download_as_csv(n_clicks, table_data, table_data2):
    if (not n_clicks) or (table_data is None):
      raise PreventUpdate
    
    # import pickle


    # with open('tablita.pickle', 'wb') as handle:
    #     pickle.dump(table_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    df = dbc_table_to_pandas(table_data)
    df2=dbc_table_to_pandas(table_data2)
    # download_buffer = io.StringIO()
    # df.to_csv(download_buffer, index=False)
    # download_buffer.seek(0)
    # return dict(content=download_buffer.getvalue(), filename="tabla_comparacion.csv")

    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        df2.to_excel(xslx_writer, index=False, sheet_name="sheet2")
        xslx_writer.save()

    return send_bytes(to_xlsx, "alertas_aplicaciones.xlsx")