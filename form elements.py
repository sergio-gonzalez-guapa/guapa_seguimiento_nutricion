import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

controls = dbc.FormGroup(
    [
        html.P('Dropdown', style={         #The <p> tag defines a paragraph.
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='dropdown',
            options=[{
                'label': 'Value One',
                'value': 'value1'
            }, {
                'label': 'Value Two',
                'value': 'value2'
            },
                {
                    'label': 'Value Three',
                    'value': 'value3'
            },
                {
                    'label': 'Value Four',
                    'value': 'value4'
            },

                {
                    'label': 'Value Five',
                    'value': 'value5'
            }

            ],
            value=['value1'],  # default value
            multi=True
        ),
        html.Br(),  #The HTML <br> element produces a line break in text (carriage-return). It is useful for writing a poem or an address, where the division of lines is significant.
        html.P('Range Slider', style={        #The <p> tag defines a paragraph.
            'textAlign': 'center'
        }),
        dcc.RangeSlider(
            id='range_slider',
            min=0, # this was 0
            max=20, #this was 20
            step=0.5,
            value=[5, 15]
        ),
        html.P('Check Box', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.Checklist(
            id='check_list',
            options=[{
                'label': 'Value One',
                'value': 'value1'
            },
                {
                    'label': 'Value Two',
                    'value': 'value2'
                },
                {
                    'label': 'Value Three',
                    'value': 'value3'
                }
            ],
            value=['value1', 'value2'],
            inline=True
        )]),
        html.Br(),
        html.P('Radio Items', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.RadioItems(
            id='radio_items',
            options=[{
                'label': 'Value One',
                'value': 'value1'
            },
                {
                    'label': 'Value Two',
                    'value': 'value2'
                },
                {
                    'label': 'Value Three',
                    'value': 'value3'
                }
            ],
            value='value1',
            style={
                'margin': 'auto'
            }
        )]),
        html.Br(),
        dbc.Button(
            id='submit_button',
            n_clicks=0,
            children='Submit',
            color='primary',
            block=True
        ),
    ]
)
