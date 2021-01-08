import dash_core_components as dcc
import dash_html_components as html
import dash_table



def crear_filtro(df):
    lista_dicts = [{"label":row["descripcion"],"value":row["codigo"]} for _,row in df.iterrows()]
    content =html.Div([
        dcc.Dropdown(
            id='formula-dropdown',
            options=lista_dicts,
            value='P55'
        ),
       dash_table.DataTable(id='data-table-detalle-formulas',style_cell={
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0},
        css=[{
        'selector': '.dash-table-tooltip',
        'rule': 'background-color: white; font-family: monospace; font-size: 10px;  width: max-content; max-width: 200px; top: 100%;left: 50%;margin-left: -60px;'
    }]
        
        )
    ])
    return content

