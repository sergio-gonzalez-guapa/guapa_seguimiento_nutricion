import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import datetime
from dateutil.relativedelta import relativedelta
import io
import db_connection
from app import app,cache, dbc_table_to_pandas

from dash_extensions import Download
from dash_extensions.snippets import send_bytes

from .layouts_predefinidos import elementos 

#Elementos filtro
year_input = dbc.FormGroup(
    [
        dbc.Label("Año", html_for="comparar-grupos-year-slider"),
        dcc.RangeSlider(
        id='comparar-grupos-year-slider',
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
        dbc.Label("Mes", html_for="comparar-grupos-month-slider"),
        dcc.RangeSlider(
        id='comparar-grupos-month-slider',
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

checklist_estado_forza = dbc.FormGroup(
    [
        dbc.Label("Estado de forzamiento", html_for="estado-forza-grupos-checklist", width=2),
        dbc.Col(
            dbc.Checklist(
                id="estado-forza-grupos-checklist",
                options=[
                    {"label": "Forzado", "value": 1},
                    {"label": "No forzado", "value": 3},
                    {"label": "Parcialmente forzado","value": 5},
                ],
            ),
            width=8,
        ),
    ],
    row=False,
)

def label_aplicaciones (i):
    if i==5:
        return "5+"
    elif i==-1:
        return "<0"
    else:
        return str(i)

aplicaciones_tardias_input = dbc.FormGroup(
    [
        dbc.Label("aplicaciones tardías", html_for="comparar-grupos-tardias-slider"),
        dcc.RangeSlider(
        id='comparar-grupos-tardias-slider',
        min=0,
        max=5,
        step=1,
        value=[0, 5],
        marks={ i:label_aplicaciones(i) for i in range(0,6)},
        vertical=True,
        verticalHeight=150
    )
    ]
)


aplicaciones_adelantadas_input = dbc.FormGroup(
    [
        dbc.Label("aplicaciones adelantadas", html_for="comparar-grupos-adelantadas-slider"),
        dcc.RangeSlider(
        id='comparar-grupos-adelantadas-slider',
        min=0,
        max=5,
        step=1,
        value=[0, 5],
        marks={ i:label_aplicaciones(i) for i in range(0,6)},
        vertical=True,
        verticalHeight=150
    )
    ]
)

aplicaciones_pendientes_input = dbc.FormGroup(
    [
        dbc.Label("aplicaciones pendientes", html_for="comparar-grupos-pendientes-slider"),
        dcc.RangeSlider(
        id='comparar-grupos-pendientes-slider',
        min=-1,
        max=5,
        step=1,
        value=[-1, 5],
        marks={ i:label_aplicaciones(i) for i in range(-1,6)},
        vertical=True,
        verticalHeight=150
    )
    ]
)

boton_aplicar_filtros = dbc.FormGroup(
    [
        dbc.Col(
            dbc.Button("Aplicar filtros",id="filtrar-grupos-btn", color="primary", className="mr-1"),
            width=10,
        ),
        html.Br(),
        dbc.Col(
            dbc.Button("Exportar a Excel",id="exportar-excel-btn", color="success", className="mr-1"),
            width=10,
        ),
        Download(id="download")
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
layout = elementos.DashLayout(extra_elements=[form_sliders,form_checboxes,html.H5("", id="h3-dias-objetivo"),
html.H5("", id="h3-rango-inferior"),
html.H5("", id="h3-rango-superior"),
 form_boton])


#Agrego elementos
layout.crear_elemento(tipo="table",element_id="comparar-grupos-table",  label="Detalle bloques")

layout.ordenar_elementos(["comparar-grupos-table"])

#Consultas
calidad_grupos = """select grupo, 
min(fecha_siembra) as fecha_siembra,
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) as numero_bloques,
SUM(CASE WHEN bloque IS NOT NULL THEN 1 ELSE 0 END) - SUM(CASE WHEN finduccion IS NOT NULL THEN 1 ELSE 0 END) as bloques_por_forzar,
max(aplicaciones_con_retraso) as max_aplicaciones_tardias,
max(aplicaciones_muy_proximas) as max_aplicaciones_adelantadas,
max(aplicaciones_esperadas - num_aplicaciones_realizadas) as max_aplicaciones_pendientes

from calidad_aplicaciones 
WHERE etapa2 =%s and categoria=%s
group by(grupo)
order by 2"""

def query_para_tabla(etapa, categoria,years,months,estado_forza,tardias,adelantadas,pendientes):
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
    
    consulta["fecha_siembra"]= pd.to_datetime(consulta["fecha_siembra"]).dt.date

    consulta = consulta[(consulta['fecha_siembra']>=datetime.date(years[0],months[0],1)) & (consulta['fecha_siembra']<datetime.date(years[1],months[1],1) + relativedelta(months=1))]

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

    return table.children


@app.callback([Output("comparar-grupos-table", "children"),Output("h3-dias-objetivo", "children"),
Output("h3-rango-inferior", "children"),Output("h3-rango-superior", "children")],
[Input('pathname-intermedio','children'),
Input("filtrar-grupos-btn", "n_clicks")],[State("url","pathname"),
State("url","hash"), State('comparar-grupos-year-slider',"value"),
State('comparar-grupos-month-slider',"value"),State('estado-forza-grupos-checklist','value'),
State('comparar-grupos-tardias-slider',"value"),State('comparar-grupos-adelantadas-slider',"value"),
State('comparar-grupos-pendientes-slider',"value")])
@cache.memoize()
def actualizar_select_bloque(path,n,url,hash,years,months,estado_forza,tardias,adelantadas,pendientes):
    if path =='comparar-grupos':
        dicc_homologacion = {"preforza":"Post Siembra",
        "postforza":"Post Forza",
        "semillero":"Post Poda",
        "nutricion":"fertilizante",
        "herbicidas":"herbicida",
        "fungicidas":"fungicida",
        "insecticidas":"insecticida"}

        
        etapa = url.split("-")[0][1:]
        categoria = hash[1:]
        nueva_consulta = db_connection.query("""SELECT dias_entre_aplicaciones, tolerancia_rango_inferior, tolerancia_rango_superior FROM rangos_calidad_aplicaciones
    WHERE etapa=%s and categoria = %s""",[dicc_homologacion[etapa],dicc_homologacion[categoria] ])

        
        
        return query_para_tabla(etapa,categoria,years,months,estado_forza,tardias,adelantadas,pendientes), f"* días entre aplicaciones: {nueva_consulta.iat[0,0]}", f"* límite inferior de tolerancia : {nueva_consulta.iat[0,1]}", f"* límite superior de tolerancia : {nueva_consulta.iat[0,2]}"
    return None, "","",""

@app.callback(
Output("download", "data"),
[Input("exportar-excel-btn", "n_clicks")],
[State("comparar-grupos-table", "children")])
def download_as_csv(n_clicks, table_data):
    if (not n_clicks) or (table_data is None):
      raise PreventUpdate
    df = dbc_table_to_pandas(table_data)

    # download_buffer = io.StringIO()
    # df.to_csv(download_buffer, index=False)
    # download_buffer.seek(0)
    # return dict(content=download_buffer.getvalue(), filename="tabla_comparacion.csv")

    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.save()

    return send_bytes(to_xlsx, "comparacion_grupos.xlsx")