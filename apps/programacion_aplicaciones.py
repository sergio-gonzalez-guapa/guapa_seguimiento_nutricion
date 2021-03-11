import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
from .layouts_predefinidos import elementos 

from app import app

#Definición de parámetros
opciones = options=[
                        {"label": "Option 1", "value": 1},
                        {"label": "Option 2", "value": 2},
                    ]
id_select = "select-aplicacion"

table_header = [
    html.Thead(html.Tr([html.Th("First Name"), html.Th("Last Name")]))
]

row1 = html.Tr([html.Td("Arthur"), html.Td("Dent")])
row2 = html.Tr([html.Td("Ford"), html.Td("Prefect")])
row3 = html.Tr([html.Td("Zaphod"), html.Td("Beeblebrox")])
row4 = html.Tr([html.Td("Trillian"), html.Td("Astra")])

table_body = [html.Tbody([row1, row2, row3, row4])]
contenido_tabla=table_header+table_body
#Creación de elementos gráficos
seleccion = elementos.crear_layout_select (label="Seleccione un bloque",content=opciones,element_id=id_select)

tabla = elementos.crear_layout_tabla (label= "Estado de bloques", content=contenido_tabla,element_id=None)

## Elementos fijos
layout = html.Div(
    [
        seleccion, tabla        
    ]
)


#Lo de dp:

def retorna_ultimas_aplicaciones_nutricion_preforza_pc():
    try:
        info_bloques = pd.read_sql_query(query.info_bloques,connection)
        info_bloques.query("finduccion!=finduccion",inplace=True)
        categorias_insumos_temp = categorias_insumos.query("categorias_por_insumo=='Fertilizante'")
        
        cedulas_por_bloque = pd.read_sql_query(query.cedulas,connection,params =[tuple(set(info_bloques.blocknumber.to_list()))])
        formulas_nutricion  = '''
        select distinct codigo
        from formulas_det where insumo in %s 
        '''
        aplicaciones_nutricion = pd.read_sql_query(formulas_nutricion,connection,params =[tuple(set(categorias_insumos_temp.insumo.unique()))])
        aplicaciones_validas = '''
        select codigo,
        formula,
        apldate 
        from mantenimientocampos 
        where codigo in %s and formula in %s and apldate>'2020-01-01'::date
        '''
        cedulas_utilizadas = pd.read_sql_query(aplicaciones_validas,connection,params =[tuple(set(cedulas_por_bloque.codigo.unique())),tuple(set(aplicaciones_nutricion.codigo.unique()))])

        total_aplicaciones_nutricion = cedulas_utilizadas.merge(cedulas_por_bloque,how="left",on="codigo")
        total_aplicaciones_nutricion.sort_values(by=["blocknumber","apldate"],inplace=True)
        total_aplicaciones_nutricion.drop_duplicates(subset="blocknumber",keep="last",inplace=True)

        nombres_formulas_query = '''
        select codigo as formula,
        descripcion as nombre_formula
        from formulas 
        where codigo in %s
        '''

        descripcion_formulas_nutricion = pd.read_sql_query(nombres_formulas_query,connection,params =[tuple(set(total_aplicaciones_nutricion.formula.unique()))])

        
        total_aplicaciones_nutricion_nombradas = total_aplicaciones_nutricion.merge(descripcion_formulas_nutricion,
        on="formula",how="left").merge(info_bloques[["blocknumber","descripcion","grupo_siembra"]].rename(columns={"descripcion":"bloque"}),on="blocknumber",how="left")
        total_aplicaciones_nutricion_nombradas.sort_values(by="apldate",inplace=True)
        total_aplicaciones_nutricion_nombradas["hoy"]= datetime.today()
        total_aplicaciones_nutricion_nombradas["dias_desde_ultima_aplicacion"]=(total_aplicaciones_nutricion_nombradas["hoy"]-total_aplicaciones_nutricion_nombradas["apldate"]).dt.days
        total_aplicaciones_nutricion_nombradas["apldate"]= total_aplicaciones_nutricion_nombradas["apldate"].dt.strftime('%d-%B-%Y')
        total_aplicaciones_nutricion_nombradas.drop(["codigo","formula","blocknumber","hoy"],axis=1,inplace=True)

        return total_aplicaciones_nutricion_nombradas
        
    except Exception as e:
        print("hubo un error",e)
        connection.rollback()

        


# #Hacer consulta para mostrar bloques del GS
# data = dp.retorna_ultimas_aplicaciones_nutricion_preforza_pc().groupby(['apldate','nombre_formula','grupo_siembra','dias_desde_ultima_aplicacion'],dropna=False)['bloque'].apply(', '.join).reset_index()
# data.sort_values(by="dias_desde_ultima_aplicacion",ascending=False,inplace=True)
# data.rename(columns={"apldate":"fecha aplicación","dias_desde_ultima_aplicacion":"días transcurridos",
# "bloque":"bloques","nombre_formula":"fórmula aplicada"},inplace=True)
# _cols=[{"name": i, "id": i} for i in data.columns]
# data_as_dict = data.to_dict('records')



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







