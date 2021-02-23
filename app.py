import pandas as pd
import sys
import numpy as np
import pickle
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table
import dash_bootstrap_components as dbc
from urllib.request import urlopen
from dash.dependencies import Input, Output, State
import plotly.express as px
import json
import base64
import io
import nutricion_preforza_pc_resumen_gs as nppcgs

from data_processing import df_grupos_siembra,retorna_bloques_de_gs,retorna_info_bloques_de_gs,retorna_info_aplicaciones_de_gs,df_formulas,retorna_detalle_formula, lotes_historia,retorna_info_estados_bloques,retorna_grafica_peso_planta,retorna_detalle_calidad_nutricion_pc_preforza
import upload_file
import insumos_por_formula
import agregar_comentario
import informacion_por_bloque
import nutricion_preforza_pc
import ultimas_aplicaciones_nutricion_preforza_pc
import cargue_peso_planta as cpp


# the style arguments for the sidebar
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',     # this sizes the left hand side of the board to 20%
    'padding': '20px 10px',
    'background-color': 'black'   # this means a light gray
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',   # this was 25%
    'margin-right': '5%',   #this was 5%, by controlling the margins, you control the border
    'padding': '20px 10px'    # this was 20px 10p   The CSS padding properties are used to generate space around an element's content, inside of any defined borders.
                            # i am not sure what this refers to
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': 'white'    # Midnight blue
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'    #Pure (or mostly pure) blue.
}


sidebar = html.Div(
    [
        html.H2("Menu", className="display-4", style={"color":"white"}),
        html.Hr(),
        html.P(
            "Seleccione la acción que desea ejecutar", className="lead",style={"color":"white"}
        ),
        dbc.Nav(
            [
                dbc.NavLink("Información de bloques", href="/page-1", id="page-1-link"),
                dbc.NavLink("Resumen nutrición preforza por grupo de siembra", href="/page-2", id="page-2-link"),
                dbc.NavLink("Aplicaciones nutrición preforza PC", href="/page-3", id="page-3-link"),
                dbc.NavLink("Insumos por fórmula", href="/page-4", id="page-4-link"),
                dbc.NavLink("Ultimas aplicaciones nutrición preforza ", href="/page-5", id="page-5-link"),
                dbc.NavLink("Cargue peso planta", href="/page-6", id="page-6-link")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)


app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],
meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],suppress_callback_exceptions = True)
#Supress callback exceptions para no validar elementos de callbacks dinámicos
server = app.server
app.layout = html.Div([dcc.Location(id="url"),sidebar, content])                   #this is the key of the division!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1

# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 7)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False, False,False, False, False  #AGREGAR UN FALSE MÀS CADA VEZ QUE SE AGREGA PAGINA
    return [pathname == f"/page-{i}" for i in range(1, 7)]

######################################
## URL callback
######################################

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        return informacion_por_bloque.crear_filtro(lotes_historia)
    elif pathname == "/page-2":
        return nppcgs.form
    elif pathname == "/page-3":
        return nutricion_preforza_pc.crear_filtro(df_grupos_siembra)

    elif pathname == "/page-4":
        return insumos_por_formula.crear_filtro(df_formulas)

    elif pathname=="/page-5":
        return ultimas_aplicaciones_nutricion_preforza_pc.crear_filtro()
    # If the user tries to reach a different page, return a 404 message
    elif pathname=="/page-6":
        return cpp.layout
    # If the user tries to reach a different page, return a 404 message
    else:
        return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


###
# Actualizar tabla histórica de estados
###



@app.callback(
    [Output('data-table-info-bloque', 'data'),
    Output('data-table-info-bloque', 'columns')],
    [Input('lote-dropdown', 'value')])
def actualizar_bloques(lote):
    data = retorna_info_estados_bloques(lote)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data.to_dict('records'),_cols

###
# Actualizar nutrición preforza PC
###

#Actualiza dropdown de bloques según gs
@app.callback(
    [Output('div-gs-nutricion-preforza-pc','children'),
    Output('bloque-nutricion-preforza-pc-dropdown', 'options'),
    Output('bloque-nutricion-preforza-pc-dropdown', 'value')],
    [Input('gs-nutricion-preforza-pc-dropdown', 'value')])
def actualizar_gs_y_dropdown_bloques_nutricion_preforza_pc(gs):

    #Hacer consulta para mostrar bloques del GS
    lista_dicts_bloques = retorna_bloques_de_gs(gs)
    return gs,lista_dicts_bloques,""


#Actualizar div bloque
@app.callback(
    Output('div-bloque-nutricion-preforza-pc','children'),
    [Input('bloque-nutricion-preforza-pc-dropdown', 'value')])
def actualizar_year(bloque):
    return bloque


#Actualizar data table agregado según los div de gs y bloque
@app.callback(
    [Output('data-table-nutricion-preforza-pc', 'data'),
    Output('data-table-nutricion-preforza-pc', 'columns')],
    [Input('div-gs-nutricion-preforza-pc', 'children')])
def actualizar_bloques_nutricion_preforza_pc(gs):


    data = retorna_info_bloques_de_gs(gs)
    cols_after_drop = [c for c in data.columns if c.startswith("tooltip")==False]    
    _cols=[{"name": ["Indicador de calidad por trimestre",i], "id": i} if i.startswith("t") else {"name": ["Información general de bloque",i], "id": i} for i in cols_after_drop]
    data_as_dict = data[cols_after_drop].to_dict('records')

    # tooltip_data=[
    #     {
    #         "q1": {'value': row["tooltip_q1"], 'type': 'markdown'},
    #         "q2": {'value': row["tooltip_q2"], 'type': 'markdown'},
    #         "q3": {'value': row["tooltip_q3"], 'type': 'markdown'},
    #         "q4": {'value': row["tooltip_q4"], 'type': 'markdown'}
    #     } for row in data.to_dict('records')
    # ]

    return data_as_dict,_cols


#Actualizar detalle indicador de calidad nutrición preforza pc
@app.callback(
    [Output('dt-calidad-nutricion-preforza-pc-bloque', 'data'),
    Output('dt-calidad-nutricion-preforza-pc-bloque', 'columns')],
    [Input('div-bloque-nutricion-preforza-pc', 'children')])
def actualizar_detalle_calidad_nutricion_preforza_pc(bloque):
    data = retorna_detalle_calidad_nutricion_pc_preforza(bloque)
    _cols=[{"name": ["# de aplicaciones por trimestre",i], "id": i} if i.startswith("t") else {"name": ["",i], "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')

    return data_as_dict,_cols



#Actualizar gráfica de peso planta
@app.callback(
    Output('graph-peso-planta', 'figure'),
    [Input('div-bloque-nutricion-preforza-pc', 'children')])
def actualizar_peso_planta_preforza(bloque):
    
    return retorna_grafica_peso_planta(bloque)


#Actualizar data table con las aplicaciones para el bloque seleccionado
@app.callback(
    [Output('data-table-nutricion-preforza-pc-por-bloque', 'data'),
    Output('data-table-nutricion-preforza-pc-por-bloque', 'columns')],
    [Input('div-bloque-nutricion-preforza-pc', 'children')])
def actualizar_aplicaciones_bloques_nutricion_preforza_pc(bloque):
    
    data = retorna_info_aplicaciones_de_gs(bloque)
    _cols=[{"name": ["Planeación de aplicaciones",i], "id": i} if "programada" in i else {"name": ["Ejecución de aplicaciones",i], "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data_as_dict,_cols


#####
# Actualiza fórmulas
##### 

#Actualiza dropdown de bloques según gs
@app.callback(
    [Output('data-table-detalle-formulas', 'data'),
    Output('data-table-detalle-formulas', 'columns'),
    Output('data-table-detalle-formulas', 'tooltip_data')],
    [Input('formula-dropdown', 'value')])
def actualizar_insumos_por_formula(formula):

    #Hacer consulta para mostrar bloques del GS
    data = retorna_detalle_formula(formula)
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')

    tooltip_data=[
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in data[["descripcion"]].to_dict('records')
    ]
    
    return data_as_dict,_cols,tooltip_data


### Cargue peso planta
@app.callback([Output('data-table-cargue-peso-planta', 'data'),
    Output('data-table-cargue-peso-planta', 'columns')],
              [Input("upload-cargue-peso-planta", 'filename'),
              Input("upload-cargue-peso-planta", 'contents')])
def update_output(filename,contents):
    
    data = pd.DataFrame(columns=["Seleccione","un archivo"]) 
    if filename is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
            
            columnas_seleccionadas = ["PC o RC",'Fecha del muestreo']
            muestras = [x for x in df.columns if (x.lower().startswith("m")) and x.lower().startswith("mu")==False]
            columnas_seleccionadas.extend(muestras)


            df_peso_forza= df[columnas_seleccionadas].melt(id_vars=["PC o RC", 'Fecha del muestreo'], var_name="muestra",value_name="valor" )
            df_peso_forza.dropna(inplace=True)


            agg_dict = {
                "media" : pd.NamedAgg(column='valor', aggfunc=lambda ts: ts.mean() ),
                "desviación": pd.NamedAgg(column='valor', aggfunc=lambda ts: (ts >20).sum()),
                "conteo": pd.NamedAgg(column='valor', aggfunc=lambda ts: ts.count()),
            }

            df_resultado = df_peso_forza.groupby(["PC o RC",'Fecha del muestreo'],dropna=True).agg(**agg_dict).reset_index().round(0)
            df_resultado.sort_values(by=["PC o RC", "Fecha del muestreo"],inplace=True)
            df_resultado.drop_duplicates(subset="PC o RC",keep="last",inplace=True)
            df_resultado["PC o RC"]=df_resultado["PC o RC"].str.upper()
            data = df_resultado.tail(20)
        
        else:
            data = pd.DataFrame(columns=["El archivo debe","ser de excel"]) 
    
    _cols=[{"name": i, "id": i} for i in data.columns]
    data_as_dict = data.to_dict('records')
    return data.to_dict('records'),_cols


if __name__ == '__main__':
    if sys.platform.startswith('win'):
        app.run_server(debug=True)
    else:
        app.run_server(debug=False,host='0.0.0.0',port=8080)
    

    ##Do not use run server in production environments!
    #app.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=False)
    
    #Hide the UI with dev_tools_ui=False
    #Turn off the component property validation with dev_tools_props_check=False.


