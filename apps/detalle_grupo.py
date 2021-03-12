import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
import db_connection
import plotly.express as px

import numpy as np
from app import app
from .layouts_predefinidos import elementos 

#Inicializo el layout
layout = elementos.DashLayout()
#Agrego los elementos vacíos pero que conforman la estructura
layout.crear_elemento(tipo="select",element_id="select-grupo",  label="seleccione un grupo")
layout.crear_elemento(tipo="table",element_id="detalle-grupo-table",  label="Detalle bloques")
layout.crear_elemento(tipo="graph",element_id="peso-planta-graph",  label="Curva peso planta")
layout.ordenar_elementos(["select-grupo","detalle-grupo-table","peso-planta-graph"])

lista_grupos_siembra = '''select distinct grupo_siembra as label, grupo_siembra as value
 from blocks_desarrollo'''

lista_grupos_forza = '''select distinct grupo_forza as label, grupo_forza as value
 from blocks_desarrollo'''

lista_grupos_semillero = '''select distinct grupo_semillero as label, grupo_forza as value
 from blocks_desarrollo'''

aplicaciones_bloques = '''SELECT blocknumber as bloque,
fecha_aplicacion as fecha,
descripcion_formula as formula,
motivo,
categoria,
etapa
from aplicaciones where blocknumber =%s order by fecha_aplicacion'''

aplicaciones_bloques_por_grupo_siembra = '''SELECT blocknumber as bloque,
fecha_aplicacion as fecha,
descripcion_formula as formula,
motivo,
categoria,
etapa
from aplicaciones where blocknumber in (SELECT
blocknumber from blocks_desarrollo 
WHERE grupo_siembra= %s)  
order by fecha_aplicacion'''

aplicaciones_bloques_por_grupo_forza = '''SELECT blocknumber as bloque,
fecha_aplicacion as fecha,
descripcion_formula as formula,
motivo,
categoria,
etapa
from aplicaciones where blocknumber in (SELECT
blocknumber from blocks_desarrollo 
WHERE grupo_forza= %s)  
order by fecha_aplicacion'''

aplicaciones_bloques_por_grupo_semillero = '''SELECT blocknumber as bloque,
fecha_aplicacion as fecha,
descripcion_formula as formula,
motivo,
categoria,
etapa
from aplicaciones where blocknumber in (SELECT
blocknumber from blocks_desarrollo 
WHERE grupo_semillero= %s)  
order by fecha_aplicacion'''

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
    "semillero":{"GF":"Post Forza"}}

    dicc_categoria = {"nutricion":"FERTILIZANTES",
    "fungicidas":"FUNGICIDAS","herbicidas":"HERBICIDAS" ,
    "hormonas":"HORMONAS Y ACELERANTES"}
    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria) or grupo==None:
        print("hay un error en el bloque",grupo, etapa, categoria)
        return None
    
    prefijo = grupo[0:2]
    if prefijo not in ["GF","GS","RC"]:
        return None

    etapa_query = dicc_etapa[etapa][prefijo]
    categoria_query = dicc_categoria[categoria]
    
    if etapa =="preforza":
        consulta = db_connection.query(aplicaciones_bloques_por_grupo_siembra, [grupo])
    elif etapa=="postforza":
        consulta = db_connection.query(aplicaciones_bloques_por_grupo_forza, [grupo])
    elif etapa=="semillero":
        consulta = db_connection.query(aplicaciones_bloques_por_grupo_semillero, [grupo])
    else:
        consulta=pd.DataFrame()

    if consulta.empty:
        print("consulta vacía")
    data_filtrada = consulta.query("categoria==@categoria_query and etapa ==@etapa_query")
    data_filtrada.to_excel("consulta.xlsx",index=False)
    #data_filtrada.drop(["categoria","etapa"],axis=1,inplace=True)
    if data_filtrada.empty:
        print("consulta con valores pero query vacío")
        return None

    data_filtrada.sort_values(by=["bloque","categoria","fecha"], inplace=True)
    data_filtrada["diff"]=data_filtrada.groupby(["bloque","categoria"])["fecha"].diff()/np.timedelta64(1, 'D')

    agg_dict = {
    "conteo": pd.NamedAgg(column='fecha', aggfunc=lambda ts: ts.count()),
    "# aplicaciones con diferencia menor a 8 días" : pd.NamedAgg(column='diff', aggfunc=lambda ts: (ts <8).sum() ),
    "# aplicaciones con diferencia mayor a 22 días": pd.NamedAgg(column='diff', aggfunc=lambda ts: (ts >22).sum()),
}
    resultado = data_filtrada.groupby(["bloque"],dropna=False).agg(**agg_dict).reset_index().round(2)
    resultado["indicador"] =resultado.apply(lambda row: 0 if (row ["# aplicaciones con diferencia menor a 8 días"]+row["# aplicaciones con diferencia mayor a 22 días"]>0.7*row["conteo"]) or (row["conteo"]<14) else 1 ,axis=1 )

    df_area = db_connection.query(info_blocks, [tuple(set(resultado.bloque.tolist()))])
    
    df_info_blocks = pd.DataFrame(columns=['bloque'])

    if prefijo in ["GS","RC"]:
        df_info_blocks = db_connection.query(info_blocks_desarrollo_gs, [grupo])
        df_info_blocks["inducido"] = df_info_blocks.finduccion.apply(lambda x: "No" if x==None else "Si")

    if prefijo == "GF":
        df_info_blocks = db_connection.query(info_blocks_desarrollo_gf, [grupo])
        df_info_blocks["edad_forza"]=  ((df_info_blocks.finduccion - df_info_blocks.fecha_siembra)/np.timedelta64(1, 'M')).round(2)

    resultado = resultado.merge(df_area, how="left",on="bloque").merge(df_info_blocks, how="left",on="bloque")
    
    #Agregar a resultado valores de bloque como: población, área, etc
    tabla = dbc.Table.from_dataframe(resultado).children
    return tabla

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
def actualizar_select_bloque(path,url):
    etapa = url.split("-")[0][1:]
    if path =='detalle-grupo':
        return query_para_select(etapa)

    return None

@app.callback(Output("select-grupo", "value"), [Input('url','search')],[State('pathname-intermedio','children')])
def actualizar_valor_select_lote(search, path):
    if "detalle-grupo" in path:
        return  search.split("=")[1]
    return None

@app.callback([Output("detalle-grupo-table", "children"),Output("peso-planta-graph", "figure")],
 [Input("select-grupo", "value")],
 [State("url","pathname"),State("url","hash")])
def actualizar_tabla(grupo, path, hash):
    etapa = path.split("-")[0][1:]
    categoria = hash[1:]
    tabla= query_para_tabla(grupo,etapa,categoria)
    
    fig = query_para_grafica(grupo,categoria,etapa)
    return tabla,fig




