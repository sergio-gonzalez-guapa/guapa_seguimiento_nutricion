import dash_core_components as dcc
import dash_html_components as html
import dash_table
import data_processing as dp
import pandas as pd


#Hacer consulta para mostrar bloques del GS
data = dp.retorna_ultimas_aplicaciones_nutricion_preforza_pc().groupby(['apldate','nombre_formula','grupo_siembra','dias_desde_ultima_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)
data.rename(columns={"apldate":"fecha aplicación","dias_desde_ultima_aplicacion":"días transcurridos",
"bloque":"bloques","nombre_formula":"fórmula aplicada"},inplace=True)
_cols=[{"name": i, "id": i} for i in data.columns]
data_as_dict = data.to_dict('records')



def crear_filtro():
    content =html.Div([
       dash_table.DataTable(id='dt-ultimas-aplicaciones-nutricion-pc',
       data=data_as_dict,
       columns=_cols,
       style_cell={
        'height': 'auto',
        # all three widths are needed
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }
        
        )
    ])
    return content

