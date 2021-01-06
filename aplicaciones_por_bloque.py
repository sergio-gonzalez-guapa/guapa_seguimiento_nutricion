import dash_core_components as dcc
import dash_html_components as html
import dash_table



def crear_filtro(df):
    lista_dicts = [{"label":row["descripcion"],"value":row["codigo"]} for index,row in df.iterrows()]
    content =html.Div([
        dcc.Dropdown(
            id='formula-dropdown',
            options=lista_dicts
        ),
       dash_table.DataTable(id='data-table-detalle-formulas')
    ])
    return content

