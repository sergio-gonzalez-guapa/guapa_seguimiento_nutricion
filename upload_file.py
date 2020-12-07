import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import base64
import io
import dash_table

def parse_contents(contents, filename, date):
    _, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        # Assume that the user uploaded a CSV file

        lista_titulos = ["fecha_aplicacion","formula","bloque","area_bruta","cant_ha","aplicado","unidad_de_medida","usuario","otro","otro2"]
        data = pd.read_csv(io.StringIO(decoded.decode('latin-1')),encoding="latin-1",header=None,names=lista_titulos,dtype = object)
        
        data.index = list(range(len(data)))
        #Corregir fecha
        data["fecha_aplicacion"] = pd.to_datetime(data["fecha_aplicacion"],format='%d/%m/%Y')
        lista_producto = list(np.delete(data.usuario.unique(),[0]))

        #Índice de productos
        df_indexes = data.query("usuario==@lista_producto").usuario.reset_index()
        df_indexes.columns =["indice","producto"]
        df_indexes["indice"] = df_indexes["indice"]+1
        df_indexes["indice_previo"]= df_indexes.shift(1).indice
        df_indexes.fillna(0,inplace=True)
        print(len(lista_producto))
        lista_dfs = []
        for _,row in df_indexes.iterrows():
            indice_inicial = int(row["indice_previo"])
            indice_final = int(row["indice"])
            df_temp = data[data.index.isin(  range(indice_inicial,indice_final))].copy()
            df_temp["producto"] = row["producto"]
            df_temp.drop(["otro","otro2","usuario"],axis=1,inplace=True)
            lista_dfs.append(df_temp)

        df_indexes["size"] = df_indexes["indice"]-df_indexes["indice_previo"]

        new_data = data.iloc[:,0:7]
        new_data.columns = ["fecha_aplicacion","formula","bloque","area_bruta","cant_ha","aplicado","unidad_de_medida"]

        new_data["area_bruta"] = new_data["area_bruta"].astype('float')

        
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([

        dash_table.DataTable(
            data=new_data.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in new_data.columns]
        )
    ])


    
content = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arrastre o  ',
            html.A('selecciones archivos')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])