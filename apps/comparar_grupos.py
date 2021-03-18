import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
import db_connection
from app import app,cache

from .layouts_predefinidos import elementos 

#Inicializo el layout
layout = elementos.DashLayout()

#Agrego elementos
layout.crear_elemento(tipo="table",element_id="comparar-grupos-table",  label="Detalle bloques")
layout.ordenar_elementos(["comparar-grupos-table"])

#Consultas
calidad_grupos = """select grupo, 
max(aplicaciones_con_retraso) as max_aplicaciones_tardias,
max(aplicaciones_muy_proximas) as max_aplicaciones_adelantadas,
max(aplicaciones_esperadas - num_aplicaciones_realizadas) as max_aplicaciones_pendientes

from calidad_aplicaciones 
WHERE etapa2 =%s and categoria=%s
group by(grupo)"""

def query_para_tabla(etapa, categoria):
    dicc_etapa = {"preforza":"Post Siembra",
    "postforza":"Post Forza",
    "semillero":"Post Deshija"}

    dicc_categoria = {"nutricion":"fertilizante",
    "fungicidas":"fungicida","herbicidas":"herbicida" ,
    "hormonas":"hormonas"}

    if (etapa not in dicc_etapa) or (categoria not in dicc_categoria):
        print("hay un error en etapa o categoria", etapa, categoria)
        return None
    
    categoria_query = dicc_categoria[categoria]
    
    consulta = db_connection.query(calidad_grupos, [etapa,categoria_query])

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

    return table.children

#Elementos filtro
year_input = dbc.FormGroup(
    [
        dbc.Label("Año", html_for="nutricion-preforza-year"),
        dcc.RangeSlider(
        id='nutricion-preforza-year',
        min=2014,
        max=2021,
        step=1,
        value=[2014, 2021],
        marks={ i:str(i) for i in range(2014,2022)}
    ),
        dbc.FormText(
            "Seleccione un rango de años",
            color="secondary",
        ),
    ]
)

month_input = dbc.FormGroup(
    [
        dbc.Label("Mes", html_for="nutricion-preforza-month"),
        dcc.RangeSlider(
        id='nutricion-preforza-month',
        min=1,
        max=12,
        step=1,
        value=[1, 12],
        marks={
        1: 'enero',
        2: 'febrero',
        3: 'marzo',
        4: 'abril',
        5: 'mayo',
        6: 'junio',
        7: 'julio',
        8: 'agosto',
        9: 'septiembre',
        10: 'octubre',
        11: 'noviembre',
        12: 'diciembre'
    }
    ),
        dbc.FormText(
            "Seleccione un rango de mes", color="primary"
        ),
    ]
)

radios_estado_forza = dbc.FormGroup(
    [
        dbc.Label("Estado de forzamiento", html_for="nutricion-preforza-estado-forza", width=2),
        dbc.Col(
            dbc.Checklist(
                id="nutricion-preforza-estado-forza",
                options=[
                    {"label": "Forzado", "value": 1},
                    {"label": "No forzado", "value": 2},
                    {"label": "Parcialmente forzado","value": 3},
                ],
            ),
            width=8,
        ),
    ],
    row=False,
)

check_calidad_aplicacion = dbc.FormGroup(
    [
        dbc.Label("Calidad de aplicación", html_for="nutricion-preforza-calidad-aplicacion", width=2),
        dbc.Col(
            dbc.Checklist(
                id="nutricion-preforza-calidad-aplicacion",
                options=[
                    {"label": "Alta", "value": 1},
                    {"label": "Baja", "value": 2}
                ],
            ),
            width=8,
        ),
    ],
    row=False,
)

boton_aplicar_filtros = dbc.FormGroup(
    [
        dbc.Col(
            dbc.Button("Aplicar filtros", color="primary", className="mr-1"),
            width=10,
        )
    ],
    row=True,
)

##############
### Datos ###
###########



form_sliders = dbc.Form([year_input, month_input])

form_checboxes =dbc.Row(
    [
        dbc.Col(radios_estado_forza),
        dbc.Col(check_calidad_aplicacion)
    ],
    form=True
)

form_boton = dbc.Form([boton_aplicar_filtros])


@app.callback(Output("comparar-grupos-table", "children"), [Input('pathname-intermedio','children')],[State("url","pathname"),State("url","hash")])
@cache.memoize()
def actualizar_select_bloque(path,url,hash):
    etapa = url.split("-")[0][1:]
    categoria = hash[1:]
    if path =='comparar-grupos':
        return query_para_tabla(etapa,categoria)

    return None
