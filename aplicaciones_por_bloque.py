import dash_core_components as dcc
import dash_html_components as html
import dash_table

content =html.Div([
    dcc.Dropdown(
        id='demo-dropdown',
        options=[
            {'label': 'bloque 10120', 'value': 10120},
            {'label': 'bloque 10220', 'value': 10220},
            {'label': 'bloque 10320', 'value': 10320},
            {'label': 'bloque 10419', 'value': 10419},
            {'label': 'bloque 10519', 'value': 10519},
            {'label': 'bloque 10619', 'value': 10619}
        ],
        value=10120
    ),
    html.Div(dash_table.DataTable(id='data-table-1'))
])

