import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

import db_connection
from app import app,cache, crear_elemento_visual

################################
# Consultas ####################
################################

lista_formulas = '''select codigo as label,
codigo as value
from formulas
order by codigo'''

insumos_por_formula = '''SELECT codigo as codigo_formula, 
t1.insumo, 
t2.nombre_insumo,
categoria, 
cantha,
descripcion
from formulas_det AS t1
LEFT JOIN AGROINSUMOS AS t2
ON TRIM(BOTH FROM t1.insumo)=TRIM(BOTH FROM t2.insumo)
WHERE codigo=%s'''

#################
# Layout ########
#################

layout = html.Div([
    crear_elemento_visual(tipo="dbc_select",element_id="select-formula",params={"label":"seleccione una formula"}),
    html.H3("Insumos de la fórmula seleccionada"),
    crear_elemento_visual(tipo="dash_table",element_id='detalle-formula-table')
    ])


##############################
# Funciones  #################
##############################


def query_para_select():
    consulta = db_connection.query(lista_formulas)
    opciones = [{"label":row["label"],"value":row["value"]} for _,row in consulta.iterrows()]
    return opciones


@cache.memoize()
def query_para_tabla(codigo_formula):
    return db_connection.query(insumos_por_formula, [codigo_formula])

##############################
# Callbacks  #################
##############################

@app.callback(Output("select-formula", "options"), [Input('pathname-intermedio','children')])
def actualizar_select_lote(path):
    if path !='detalle-formula':
        raise PreventUpdate
    
    return  query_para_select()

#Callback para seleccionar la fórmula según search location
@app.callback(Output("select-formula", "value"), [Input('url','search')],[State('pathname-intermedio','children')])
def actualizar_valor_select_bloque(search, path):
    if "detalle-formula" not in path:
        raise PreventUpdate
    else:
        busqueda = search.split("=")
        if len(busqueda)<2:
            return None
        else:
            return busqueda[1].replace("_"," ")


@app.callback(Output("detalle-formula-table", "data"),Output('detalle-formula-table', 'columns'),
 [Input("select-formula", "value")])
def actualizar_tabla(formula):
    if formula is None:
      raise PreventUpdate

    data = query_para_tabla(formula)

    return data.to_dict('records'), [{"name": i, "id": i} for i in data.columns]

