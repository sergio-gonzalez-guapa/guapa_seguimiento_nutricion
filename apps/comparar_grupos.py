import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output

from app import app



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

grupossiembra = ["GS0120","GS0220"]
mes = [1,1]
estado_forzamiento = ["Forzado","No forzado"]
link = ["page-3","www.google.com"]

df = pd.DataFrame({"gs":grupossiembra, "mes":mes, "estado forza":estado_forzamiento,
                  "link":link})
df_drop_link = df.drop(columns='link')

tabla = html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df_drop_link.columns])] +

        # Body
        [html.Tr([
            html.Td(df.iloc[i][col]) if col != 'gs' else html.Td(html.A(href=df.iloc[i]['link'], children=df.iloc[i][col], target='_blank')) for col in df_drop_link.columns 
        ]) for i in range(len(df))]
    ) 


form_sliders = dbc.Form([year_input, month_input])

form_checboxes =dbc.Row(
    [
        dbc.Col(radios_estado_forza),
        dbc.Col(check_calidad_aplicacion)
    ],
    form=True
)

form_boton = dbc.Form([boton_aplicar_filtros])

#Estructura de tablas
df_nutricion = pd.DataFrame(
    {
        "Grupo de siembra": ["GS2020", "GS2120", "GS2220", "GS2320"],
        "Indicador de calidad": ["alta", "alta", "baja", "baja"],
    }
)

df_proteccion = pd.DataFrame(
    {
        "First Name": ["Protección", "Ford", "Zaphod", "Trillian"],
        "Last Name": ["Dent", "Prefect", "Beeblebrox", "Astra"],
    }
)

df_herbicida = pd.DataFrame(
    {
        "First Name": ["Herbicida", "Ford", "Zaphod", "Trillian"],
        "Last Name": ["Dent", "Prefect", "Beeblebrox", "Astra"],
    }
)

def crear_tabla(hash):
    if hash=="#proteccion":
        df = df_proteccion
    elif hash=="#herbicida":
        df = df_herbicida
    else:
        df =df_nutricion

    return [form_sliders,form_checboxes,form_boton,dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True,size="md")]

def crear_layout (hash="nutricion"):

    

    content = dbc.Card(
    dbc.CardBody(
        [
            form_sliders,
            html.Div(crear_tabla(hash),id = "comparar-grupos-content")
        ]
    ),
    className="mt-3"
)
    return content

