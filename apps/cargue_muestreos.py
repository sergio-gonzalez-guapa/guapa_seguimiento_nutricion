import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import base64
import dash_table
import io
from app import app
from .layouts_predefinidos import elementos 




layout = html.Div([
    dcc.Upload(id="upload-cargue-peso-planta",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            }),
html.Div(id="data-table-cargue-peso-planta")]
)

def parse_contents(contents, filename, date=None):
    
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    print("decodifica el contenido")
    try:
        if 'xlsx' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div([
            'Seleccione un archivo en formato excel xlsx'
        ])
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    
    else:
        
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

        return html.Div([
        html.H5(filename),

        dash_table.DataTable(
            data=df_resultado.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:20] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

# @app.callback(Output("data-table-cargue-peso-planta", "children"),
#  [Input("upload-cargue-peso-planta", 'filename'),
#               Input("upload-cargue-peso-planta", 'contents')])
# def actualizar_tabla(contents, filename):
#     print("entra a este actualizar tabla")

#     return parse_contents(contents,filename)