import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from dash.dependencies import Input, Output,State
from .layouts_predefinidos import elementos 

from app import app,cache
import db_connection


#Inicializo el layout
layout = elementos.DashLayout()
#Agrego los elementos vacíos pero que conforman la estructura
layout.crear_elemento(tipo="select",element_id="select-lote",  label="seleccione un lote")
layout.crear_elemento(tipo="table",element_id="estado-bloques-table",  label="Estado de bloques")

layout.ordenar_elementos(["select-lote","estado-bloques-table"])


lotes_historia = '''
    select label,
    value
    from lotes_detalle
    order by 1'''


historia_bloques = '''SELECT bloque,
    lote,
    grupo_siembra as "grupo de siembra",
    grupo_forza as "grupo de forza",
    grupo_semillero as "grupo semillero",
    grupo_2da_cosecha as "grupo inicio 2da",
    grupo_forza2 as "grupo forza 2da",
    siembra,
    finduccion as "induccion pc",
    fecha_cosecha_pc as "cosecha 1ra",
    poda,
    deshija,
    finduccion2 as "induccion 2da",
    fecha_cosecha_sc as "cosecha 2da",
    semillerosegunda as "semillero 2da",
    barrido
FROM historia_bloques where lote = %s'''


def query_para_select():
    consulta = db_connection.query(lotes_historia)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

def query_para_tabla(lote):
    consulta= db_connection.query(historia_bloques, [lote])
    data = dbc.Table.from_dataframe(consulta).children

    header_agrupador = [html.Th("identificadores",colSpan=7,style={"text-align": "center"}),html.Th("fechas",colSpan=9,style={"text-align": "center"})]
    table_header = [
    html.Thead(header_agrupador),
    html.Thead(html.Tr([ html.Th(col) for col in consulta.columns]))]

    rows = []
    for row in consulta.itertuples(index=False):
        #Aquí debo poner la lógica los anchor para el vínculo que me lleve al grupo correspondiente
        dict_tuple = row._asdict()
        new_row=[]
        for k,v in dict_tuple.items():
            if v ==None:
                new_row.append(html.Td(v))
            elif k in ['_2','_5']:
                new_row.append(html.Td(dcc.Link(v,href=f"/preforza-detalle-grupo?gs={v}") ))
            elif k in ['_3','_6']:
                new_row.append(html.Td(dcc.Link(v,href=f"/postforza-detalle-grupo?gf={v}")))
            elif k=='_4':
                new_row.append(html.Td(dcc.Link(v,href=f"/semillero-detalle-grupo?gse={v}")))
            else:
                new_row.append(html.Td(v))
        
        rows.append(html.Tr(new_row))
        
        
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True)

    return table

@app.callback(Output("select-lote", "options"), [Input('pathname-intermedio','children')])
@cache.memoize()
def actualizar_select_lote(path):
    if path=="estado-bloques":
        return  query_para_select()
    return None

@app.callback(Output("estado-bloques-table", "children"), [Input("select-lote", "value")])
@cache.memoize()
def actualizar_tabla(lote):
    return  query_para_tabla(lote)



