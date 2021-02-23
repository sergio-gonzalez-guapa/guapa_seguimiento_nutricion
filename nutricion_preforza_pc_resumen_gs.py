import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
year_input = dbc.FormGroup(
    [
        dbc.Label("Año", html_for="nutricion-preforza-year"),
        dcc.RangeSlider(
        id='nutricion-preforza-year',
        min=2014,
        max=2021,
        step=1,
        value=[2014, 2021],
        marks={
        2014: '2014',
        2016: '2016',
        2018: '2018',
        2020: '2020'
    }
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
        4: 'abril',
        8: 'agosto',
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
            width=10,
        ),
    ],
    row=True,
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
            width=10,
        ),
    ],
    row=True,
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


form = dbc.Form([year_input, month_input,radios_estado_forza,check_calidad_aplicacion,
                boton_aplicar_filtros,tabla])