import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output

from app import app,cache,crear_elemento_visual
import db_connection

################################
# Consultas ####################
################################

lotes_historia = '''
    select label,
    value
    from lotes_detalle
    order by 1'''

historia_bloques = '''SELECT bloque,
    CONCAT('[',grupo_siembra,'](', '/preforza-detalle-grupo?gs=',grupo_siembra,')' ) as "grupo de siembra",
    CONCAT('[',grupo_forza,'](', '/postforza-detalle-grupo?gf=',grupo_forza,')' ) as "grupo de forza",
    CONCAT('[',grupo_semillero,'](', '/semillero-detalle-grupo?gse=',grupo_semillero,')' ) as "grupo semillero",
    CONCAT('[',grupo_2da_cosecha,'](', '/preforza-detalle-grupo?gs=',grupo_2da_cosecha,')' ) as "grupo inicio 2da",
    CONCAT('[',grupo_forza2,'](', '/postforza-detalle-grupo?gf=',grupo_forza2,')' ) as "grupo forza 2da",
    CONCAT('[',siembra,'](', '/preforza-detalle-bloque?bloque=PC',bloque,')' ) as siembra,
    CONCAT('[',finduccion,'](', '/postforza-detalle-bloque?bloque=PC',bloque,')' ) as "induccion pc",
    fecha_cosecha_pc as "cosecha 1ra",
    poda,
    CONCAT('[',deshija,'](', '/preforza-detalle-bloque?bloque=SC',bloque,')' ) as deshija,
    CONCAT('[',finduccion2,'](', '/postforza-detalle-bloque?bloque=SC',bloque,')' ) as "induccion 2da",
    fecha_cosecha_sc as "cosecha 2da",
    semillerosegunda as "semillero 2da",
    barrido
FROM historia_bloques where lote = %s'''

#################
# Layout ########
#################


layout = html.Div([
    
    crear_elemento_visual(tipo="dbc_select",element_id="select-lote",params={"label":"Seleccione un lote"}),
    html.H1("Estado de bloques"),
    crear_elemento_visual(tipo="dash_table",element_id='estado-bloques-table')
    ])

##############################
# Funciones  #################
##############################

@cache.memoize()
def query_para_select():
    consulta = db_connection.query(lotes_historia)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones

@cache.memoize()
def query_para_tabla(lote):
    return db_connection.query(historia_bloques, [lote]).fillna("")

##############################
# Callbacks  #################
##############################
@app.callback(Output("select-lote", "options"), [Input('pathname-intermedio','children')])
def actualizar_select_lote(path):
    if path=="estado-bloques":
        return  query_para_select()
    return None

@app.callback(Output("estado-bloques-table", "data"),Output('estado-bloques-table', 'columns'), [Input("select-lote", "value")])
def actualizar_tabla(lote):
    if lote is None:
        raise PreventUpdate

    df = query_para_tabla(lote)
    return df.to_dict('records'), [{"name": i, "id": i,'presentation':'markdown'} for i in df.columns]
    



