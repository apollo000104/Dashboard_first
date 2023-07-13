# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import pandas as pd
from pathlib import Path

from PIL import Image
from datetime import date
from datetime import datetime
from functools import lru_cache

import dash_auth
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, State, dash_table

# import flask
# from werkzeug.middleware.dispatcher import DispatcherMiddleware
# from werkzeug.serving import run_simple

# sys.path.append( str( Path( __file__ ).absolute().parents[ 1 ] ) )

# from modules.analysis.connector import *
from modules.analysis.connector_xml import *
# from modules.analysis.connector_db import *

# server = flask.Flask(__name__)

app = Dash(
    __name__, 
    # url_base_pathname='/',
    # server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {
            "name": "viewport", 
            "content": "width=device-width, initial-scale=1"
        }
    ]
)

# # Додавання JavaScript-коду
# app.clientside_callback(
#     """
#     function(highlight_row, table_id, row_index) {
#         var table = document.getElementById(table_id);
#         var rows = table.getElementsByTagName('tr');

#         // Зняття виділення з усіх рядків
#         Array.from(rows).forEach(function(row) {
#             row.style.backgroundColor = '';
#         });

#         // Виділення вибраного рядка
#         var selected_row = rows[row_index + 1]; // +1 для пропуску заголовка
#         selected_row.style.backgroundColor = 'lightblue';

#         return '';
#     }
#     """,
#     Output('tbl-analytics-customer', 'style_data_conditional'),
#     [Input('tbl-analytics-customer', 'selected_rows')],
#     [State('tbl-analytics-customer', 'id'), State('tbl-analytics-customer', 'derived_virtual_indices')]
# )

VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': '123456',
    'Галина': '09052023',
    'Олександр': '15052023', 
    'User1': '0987654321',
    'User2': '2143658709',
    'User3': '1q2w3e4r5t'
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# app.css.append_css({
#     'external_url': (
#         'https://raw.githubusercontent.com/plotly/dash-sample-apps/master/apps/dash-oil-and-gas/assets/stylesheet.css'
#     )
# })

# @server.route("/")
# def my_dash_app():
#     return app.index()

# @server.route("/testss")
# def my_dash():
#     return 'LOL'

# application = DispatcherMiddleware(
#     server,
#     {"/main": app.server},
# )


ENTERPRISES = {
    'center-kyiv': {
        'name': 'Автоцентр Київ',
        'logo': 'dashboard/images/center-kyiv.png',
        'db_config_path': 'dashboard/configs/center-kyiv.yaml'

    }
}


LOGO = Image.open('dashboard/images/logo.png')


CONTENT_STYLE = {
    # 'width': '100%',
    # 'max-width': '1200px',  # встановіть максимальну ширину для контенту
    'margin': '0 auto',  # центруємо контент на сторінці
    'padding-top': '80px', # встановіть висоту вашої навігаційної панелі

}


offcanvas = html.Div(
    [
        dbc.NavLink(
            "Фільтрація", 
            id="open-offcanvas", 
            n_clicks=0,
            style={'font-size': '20px', 'color': '#004fd0', 'margin-right': '20px', 'cursor': 'pointer'}),
        dbc.Offcanvas(
            dbc.Col(
                [
                    html.H6("Фільтрація", className="display-6"),
                    html.Hr(),
                    # html.P('Оберіть тип вибору дати:'),
                    # dcc.RadioItems(
                    #     id='date-picker-type',
                    #     options=[
                    #         {'label': 'Діапазон дат', 'value': 'range'},
                    #         {'label': 'Один день', 'value': 'single'}
                    #     ],
                    #     value='single',
                    #     labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                    # ),
                    html.Div(id='date-picker-container'),
                    dbc.Row(
                        [
                            html.P('Діапазон'),
                            dcc.DatePickerRange(
                            id='my-date-picker-range',
                            month_format='M/Y',
                            first_day_of_week=1,
                            start_date=date(2023, 5, 12),
                            end_date=date(2023, 5, 12),
                            # end_date=datetime.now().strftime("%Y-%m-%d"),
                            clearable=False,
                            display_format = 'DD.MM.YYYY',
                            style={
                                'margin-left': '40px',
                                'margin-right': '40px',
                            }
                            ),
                        ],
                        # style={
                        #     'margin-left': '15px',
                        #     'margin-right': '15px',

                        # }
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            html.P('Запис'),
                            dcc.Dropdown(
                                ['За записом', 'Без запису'], 
                                'За записом', 
                                id='dropdown-period',
                                placeholder="Виберіть",
                            ),
                            # html.Div(id='dd-output-container')
                        ],
                        # style={
                        #     'margin-left': '15px',
                        #     'margin-right': '15px',

                        # }
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            html.P('Участки'),
                            dcc.Dropdown(
                                ['Всі', 'Зона ТО і ремонту','Малярно-кузовна дільниця','Дільниця додаткового обладнання'],
                                'Всі', 
                                id='dropdown-section',
                                placeholder="Виберіть",
                            ),
                            # html.Div(id='dd-output-container')
                        ],
                        # style={
                        #     'margin-left': '15px',
                        #     'margin-right': '15px',

                        # }
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            html.P('Менеджер'),
                            dcc.Dropdown(
                                [
                                    'Всі', 'Безкоровайний О. Г.','Жельчик І. О.', 'Козолій С. Л.', 'Куделя О. А.', 'Курило В. В.', 'Мейта І. С.', 
                                    'Москаленко О. В.', 'Онищенко А. П.', 'Слабій В. О.', 'Стогній І. О.', 'Швець С. Л.', 'Ющенко С. М.'
                                ],
                                'Всі', 
                                id='dropdown-manager',
                                placeholder="Виберіть",
                            ),
                            # html.Div(id='dd-output-container')
                        ],
                        # style={
                        #     'margin-left': '15px',
                        #     'margin-right': '15px',

                        # }
                    ),
                    html.Hr(),
                    dbc.Row(
                        html.Div(
                        [
                            dbc.Button(
                                "Пошук", 
                                className="me-1",
                                id='search-button',
                            ),
                        ],
                        id='output-container-date-picker-range',
                        className="d-grid gap-2",
                        )
                    ),
                ]
            ),
            id="offcanvas",
            # title="Фільтр",
            is_open=False,
            scrollable=True,
            # backdrop=False
        ),
    ]
)

# @app.callback(
#     Output('date-picker-container', 'children'),
#     Input('date-picker-type', 'value')
# )
# def update_date_picker(date_picker_type):
#     if date_picker_type == 'range':
#         return dcc.DatePickerRange(
#             id='my-date-picker-range',
#             month_format='M/Y',
#             first_day_of_week=1,
#             start_date=date(2023, 5, 12),
#             end_date=date(2023, 6, 12),
#             # end_date=datetime.now().strftime("%Y-%m-%d"),
#             clearable=False,
#             display_format = 'DD.MM.YYYY',
#             style={
#                 'margin-left': '40px',
#                 'margin-right': '40px',
#             }
#         )
#     elif date_picker_type == 'single':
#         return dcc.DatePickerSingle(
#             id='my-date-picker-range',
#             date=date.today(),
#             display_format='DD.MM.YYYY',
#             style={'margin-left': '40px', 'margin-right': '40px'}
#         )
#     return None

@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


def nb_gantt(pathname):
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=LOGO, height="50px")),
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Autotrading", 
                                    className="ms-3",
                                    style={
                                        'font-size': '30px',
                                        'text-align': 'center',
                                        'color': '#004fd0',
                                        # 'justify-content': 'center'
                                    }
                                )
                            ),
                        ],
                        align="center",
                        className="g-0",
                        id="navbar-logo",
                        style={
                            "textDecoration": "none",
                            'display': 'flex',
                            'align-items': 'center',
                        },
                    ),
                    style={
                        "textDecoration": "none",
                        'margin-left': '20px',
                        'text-align': 'center',
                        'display': 'block',
                    },
                    href="/"
                ),
                dbc.Nav(
                    [
                        dbc.NavLink("Назад до таблиць", href=f"/{pathname.split('/')[1]}", style={'font-size': '20px', 'color': '#004fd0', 'margin-right': '20px'}),
                        dbc.NavLink("Підприємства", href="/", style={'font-size': '20px', 'color': '#004fd0', 'margin-right': '20px'}),
                        offcanvas,
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
            ],
            fluid=True,
            style={
                'text-align': 'center',
                'padding': '10px',
            },
        ),
        color="white",
        dark=False,
        fixed="top",
        style={
            'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
        }
    )

    return navbar


def nb_main(pathname):
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=LOGO, height="50px")),
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Autotrading", 
                                    className="ms-3",
                                    style={
                                        'font-size': '30px',
                                        'text-align': 'center',
                                        'color': '#004fd0',
                                        # 'justify-content': 'center'
                                    }
                                )
                            ),
                        ],
                        align="center",
                        className="g-0",
                        id="navbar-logo",
                        style={
                            "textDecoration": "none",
                            'display': 'flex',
                            'align-items': 'center',
                        },
                    ),
                    style={
                        "textDecoration": "none",
                        'margin-left': '20px',
                        'text-align': 'center',
                        'display': 'block',
                    },
                    href="/"
                ),
                dbc.Nav(
                    [
                        dbc.NavLink("Підприємства", href="/", style={'font-size': '20px', 'color': '#004fd0', 'margin-right': '20px'}),
                        dbc.NavLink("Діаграма Gantt", href=f"{pathname}/gantt-chart", style={'font-size': '20px', 'color': '#004fd0', 'margin-right': '20px'}),
                        offcanvas,
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
            ],
            fluid=True,
            style={
                'text-align': 'center',
                'padding': '10px',
                # 'border-bottom': '1px solid #ccc',
            },
        ),
        color="white",
        dark=False,
        fixed="top",
        style={
            'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
        }
    )

    return navbar

navbar_main = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="50px")),
                        dbc.Col(
                            dbc.NavbarBrand(
                                "Autotrading", 
                                className="ms-3",
                                style={
                                    'font-size': '30px',
                                    'text-align': 'center',
                                    'color': '#004fd0',
                                    # 'justify-content': 'center'
                                }
                            )
                        ),
                    ],
                    align="center",
                    className="g-0",
                    id="navbar-logo",
                    style={
                        "textDecoration": "none",
                        'display': 'flex',
                        'align-items': 'center',
                    },
                ),
                style={
                    "textDecoration": "none",
                    'margin-left': '20px',
                    'text-align': 'center',
                    'display': 'block',
                },
                href="/"
            ),
            # dbc.NavItem(
            #     dbc.NavLink("Підприємства", href="/", style={'font-size': '20px'}),
            # )
        ],
        fluid=True,
        style={
            'text-align': 'center',
            'padding': '10px',
            # 'border-bottom': '1px solid #ccc',
        },
    ),
    color="white",
    dark=False,
    fixed="top",
    style={
        'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
    }
)


# MAIN PAGE
main_page = dbc.Container(
    [
        # cards
        html.Div(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H2("Автоцентр Київ", className="display-6"),
                                html.Hr(className="my-2"),
                                html.P(
                                    "Показники стадій процесу обслуговування клієнтів"
                                ),
                                dbc.Button("Перейти", href="/center-kyiv", id='search-button', outline=True, color='primary', className="d-grid gap-2"),
                            ],
                            className="h-100 p-5 bg-light border rounded-3",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H2("Автоцентр Дніпро", className="display-6"),
                                html.Hr(className="my-2"),
                                html.P(
                                    "Показники стадій процесу обслуговування клієнтів"
                                ),
                                dbc.Button("Перейти", href="/center-dnipro", id='search-button', outline=True, color='primary', className="d-grid gap-2"),
                            ],
                            className="h-100 p-5 bg-light border rounded-3",
                        ),
                        md=6,
                    )
                ]
            )
        )
    ]
)


content = dbc.Container(
    id="page-content", 
    style=CONTENT_STYLE,
    fluid=True,
)

app.layout = dbc.Container(
    [
        dcc.Location(id="url"),
        navbar_main,
        html.Hr(),
        content,
    ],
    fluid=True,
    # style={"width": "100%"} 
)

def center(pathname):
    content = dbc.Container(
        [
            nb_main(pathname),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Аналітичні показники", className="card-title"),
                            html.P(
                                className="card-text",
                                id='card-text1'
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                ),
            ),
            html.Br(),
            dcc.Loading(
                id="loading-2",
                type="default",
                children=dbc.Row(id='tbl1'),
            ),
            html.Br(),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Показники виконання процедури", className="card-title"),
                            html.P(
                                className="card-text",
                                id='card-text2'
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                ),
            ),
            html.Br(),
            dcc.Loading(
                id="loading-3",
                type="default",
                children=dbc.Row(id='tbl2'),
            ),
            html.Br(),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Шлях клієнта по крокам", className="card-title"),
                            html.P(
                                className="card-text",
                                id='card-text3'
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                ),
            ),
            html.Br(),
            dcc.Loading(
                id="loading-4",
                type="default",
                children=dbc.Row(id='tbl3'),
            ),
            html.Br(),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Тривалість кожного етапу по клієнту", className="card-title"),
                            html.P(
                                className="card-text",
                                id='card-text5'
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                ),
            ),
            html.Br(),
            dcc.Loading(
                id="loading-6",
                type="default",
                children=dbc.Row(id='tbl-analytics-customer'),
            ),
            html.Br(),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Інформація по кожному клієнту", className="card-title"),
                            html.P(
                                className="card-text",
                                id='card-text6'
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                ),
            ),
            html.Br(),
            dcc.Loading(
                id="loading-7",
                type="default",
                children=dbc.Row(id='tbl-main'),
            ),
            html.Br(),
        ],
        style={
            'color': '#004fd0'
        }
    )
        
    return content

def gantt(pathname):
    content = dbc.Container(
        [
            nb_gantt(pathname),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Діаграма Gantt", className="card-title"),
                            html.P(
                                "Етапи обслуговування клієнтів у відсотках",
                                className="card-text"
                            ),
                        ]
                    ),
                    style={
                        'width': '100%',
                        'text-align': 'center',
                    }
                )
            ),
            html.Br(),
            dcc.Loading(
                id="loading-2",
                type="default",
                children=html.Div(id='graph'),
            ),
        ],
        style={
            'color': '#004fd0'
        }
    )
        
    return content


@app.callback(
    [
        # Output("loading-output", "children"), 
        Output("graph", "children"),
        # Output("card-text6", "children"),
    ],
    [
        Input('search-button', 'n_clicks'),
    ],
    [
        State('my-date-picker-range', 'start_date'),
        State('my-date-picker-range', 'end_date'),
        State('dropdown-period', 'value'),
        State('dropdown-section', 'value'),
        State('dropdown-manager', 'value')

    ],
)
def updated_gantt(n_clicks, start_date, end_date, value_record, value_section, value_manager):

    # print(value_period, value_section, start_date, end_date)
    table1, table2, table3, main, describe_areas, analytics_customer = get(value_record, value_section, value_manager, start_date, end_date)

    analytics_customer_gantt = pd.DataFrame()
    analytics_customer_gantt['ПІБ'] = analytics_customer['ПІБ']
    # analytics_customer_gantt['Прийом замовлення'] = abs(analytics_customer['Підготовка до візиту'])
    analytics_customer_gantt['Прийом автомобіля'] = abs(analytics_customer['Прийомка'])
    analytics_customer_gantt['Ремонт'] = abs(analytics_customer['Очікування ремонту']) + abs(analytics_customer['Ремонт загальний'])
    analytics_customer_gantt['Видача автомобіля'] = abs(analytics_customer['Видача'])
    analytics_customer_gantt['Шлях клієнта'] = analytics_customer_gantt['Прийом автомобіля'] + analytics_customer_gantt['Ремонт'] + analytics_customer_gantt['Видача автомобіля']
    # analytics_customer_gantt['Шлях клієнта з запису'] = abs(analytics_customer['Шлях клієнта з запису, діб'] * 24 * 60)
    # analytics_customer_gantt['Прийом замовлення %'] = analytics_customer_gantt['Прийом замовлення'] * 100 / analytics_customer_gantt['Шлях клієнта з запису']
    analytics_customer_gantt['Прийом автомобіля %'] = analytics_customer_gantt['Прийом автомобіля'] * 100 / analytics_customer_gantt['Шлях клієнта']
    analytics_customer_gantt['Ремонт %'] = analytics_customer_gantt['Ремонт'] * 100 / analytics_customer_gantt['Шлях клієнта']
    analytics_customer_gantt['Видача автомобіля %'] = analytics_customer_gantt['Видача автомобіля'] * 100 / analytics_customer_gantt['Шлях клієнта']

    analytics_customer_gantt = analytics_customer_gantt.round(2)
    analytics_customer_gantt = analytics_customer_gantt.dropna(how='any')
    print(analytics_customer_gantt)
    contents = get_gantt(analytics_customer_gantt)
    
    return contents



@app.callback(
    [
        # Output("loading-output", "children"), 
        Output("tbl1", "children"),
        Output("tbl2", "children"),
        Output("tbl3", "children"),
        Output("tbl-analytics-customer", "children"),
        Output("tbl-main", "children"),
        Output("card-text1", "children"),
        Output("card-text2", "children"),
        Output("card-text3", "children"),
        Output("card-text5", "children"),
        Output("card-text6", "children"),
    ],
    [
        Input('search-button', 'n_clicks'),
        # Input('dropdown-period', 'value'),
        # Input('dropdown-section', 'value')
    ],
    [
        State('my-date-picker-range', 'start_date'),
        State('my-date-picker-range', 'end_date'),
        State('dropdown-period', 'value'),
        State('dropdown-section', 'value'),
        State('dropdown-manager', 'value')

    ],
)
def update_center(n_clicks, start_date, end_date, value_record, value_section, value_manager):

    # print(value_period, value_section, start_date, end_date)
    table1, table2, table3, main, describe_areas, analytics_customer = get(value_record, value_section, value_manager, start_date, end_date)

    if value_record == 'За записом':
        tipheader = [
            'Показник',
            'Створення запис на СТО - Вхідний дзвінок',
            'Плановий заїзд – Створення ЗН, норма: більше або дорівнює 15',
            'Заїзд в зону сервісу – Заїзд на територію, норма: більше 0',
            'Проведення ЗН – Заїзд на територію',
            'Заїзд в зону сервісу - Проведення ЗН',
            'Виїзд з зони сервісу – Заїзд в зону сервісу',
            'Кінець роботи - Початок роботи',
            'Ремонт загальний - Ремонт відсканований',
            'Закриття ЗН - Виїзд в зони сервісу',
            'Виїзд з території – Закриття ЗН',
            'Плановий заїзд – Створення запис на СТО',
            'Виїзд території – Заїзд на територію',
            'Виїзд з території – Плановий заїзд',
            'Кількість закритих нормогодин в ЗН / Ремонт загальний'
        ]

        # describe_areas_after = describe_areas.copy()
        # describe_areas_after.columns = [
        #     ['', 'Прийом замовлення', 'Прийом замовлення', 'Прийом автомобіля', 'Прийом автомобіля', 'Ремонт', 'Ремонт', 'Ремонт', 'Ремонт', 'Видача автомобіля', 'Видача автомобіля', 'Аналітичні показники', 'Аналітичні показники', 'Аналітичні показники', 'Аналітичні показники'],
        #     describe_areas_after.columns
        # ]

        analytics_customer_after = analytics_customer.copy()
        analytics_customer_after.columns = [
            ['', '', '', 'Прийом замовлення', 'Прийом замовлення', 'Прийом автомобіля', 'Прийом автомобіля', 'Ремонт', 'Ремонт', 'Ремонт', 'Ремонт', 'Видача автомобіля', 'Видача автомобіля', 'Аналітичні показники', 'Аналітичні показники', 'Аналітичні показники', 'Аналітичні показники'],
            analytics_customer_after.columns
        ]

        # === table 1 ===
        tipheader_table1 = [
            'Показник',
            'Плановий заїзд – Створення запис на СТО',
            'Виїзд з території – Плановий заїзд',
            'Виїзд території – Заїзд на територію',
            'Кількість закритих нормогодин в ЗН / Ремонт загальний'
        ]

        table1 = [
            dash_table.DataTable(
                data=table1.to_dict('records'),
                tooltip_data=[
                    {
                        column: {'value': tipheader_table1[i], 'type': 'markdown'}
                        for i, (column, _) in zip(range(len(table1.columns)), row.items())
                    } for row in table1.to_dict('records')
                ],
                tooltip_duration=None,
                # merge_duplicate_headers=True,
                columns=[{'name': i, 'id': i} for i in table1.columns],
            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 1 ===

        # === table 2 ===
        # tipheader_table2 = [
        #     '',
        #     '',
        #     'Кількість значень по полю підготовка до візиту більше або дорівнює 15 хвилин',
        #     'Кількість значень по полю підготовка до візиту менше 15 хвилин',
        #     '',
        #     'Кількість мінусових значень по колонці перебування після завершення ремонту'
        # ]

        table2 = [
            dash_table.DataTable(
                data=table2.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in table2.columns],
                fixed_columns={'headers': True, 'data': 1},
                # tooltip_data = [
                #     {
                #         column: {'value': tipheader_table2[i], 'type': 'markdown'}
                #         if column in ['Кількість Н-З, підготовлених завчасно', 'Кількість Н-З НЕ підготовлених завчасно', 'Кількість заїздів закритих після виїзду клієнта']
                #         else {'value': row[column], 'type': 'markdown'}
                #         for i, (column, _) in enumerate(row.items())
                #     }
                #     for row in table2.to_dict('records')
                # ],

            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 2 ===

        # === table 3 ===
        tipheader_table3 = [
            'Показник',
            'Плановий заїзд – Створення ЗН, норма: більше 15',
            'Заїзд в зону сервісу – Заїзд на територію, норма: більше 0',
            'Заїзд в зону сервісу - Проведення ЗН',
            'Виїзд з зони сервісу – Заїзд в зону сервісу',
            'Закриття ЗН - Виїзд в зони сервісу',
            'Ремонт загальний - Ремонт відсканований',
            'Виїзд з території – Закриття ЗН',
        ]

        table3 = [
            dash_table.DataTable(
                data=table3.to_dict('records'),
                tooltip_data=[
                    {
                        column: {'value': tipheader_table3[i], 'type': 'markdown'}
                        for i, (column, _) in zip(range(len(table3.columns)), row.items())
                    } for row in table3.to_dict('records')
                ],
                tooltip_duration=None,
                # merge_duplicate_headers=True,
                columns=[{'name': i, 'id': i} for i in table3.columns],
            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 3 ===

    elif value_record == 'Без запису':
        tipheader = [
            'Показник',
            'Створення ЗН - Заїзд на парковку',
            'Заїзд в зону сервісу – Заїзд на територію, норма: більше 0',
            'Заїзд в зону сервісу - Проведення ЗН',
            'Виїзд з зони сервісу – Заїзд в зону сервісу',
            'Кінець роботи - Початок роботи',
            'Ремонт загальний - Ремонт відсканований',
            'Закриття ЗН - Виїзд в зони сервісу',
            'Виїзд з території – Закриття ЗН',
            'Виїзд території – Заїзд на територію',
            'Кількість закритих нормогодин в ЗН / Ремонт загальний'
        ]

        # describe_areas_after = describe_areas.copy()
        # describe_areas_after.columns = [
        #     ['', '', '', '', 'Ремонт', 'Ремонт', '', '', '', '', ''],
        #     describe_areas_after.columns
        # ]
        analytics_customer = analytics_customer[
            [
                'ПІБ', 'Держ. номер', 'Заявка ТО', 'Очікування клієнта в черзі', 'Прийомка', 'Очікування ремонту', 'Ремонт загальний', 
                'Ремонт відсканований', 'Очікування в ремзоні (простої)', 'Видача', 'Перебування авто після завершення ремонту', 
                'Тривалість візиту, години', 'Коефіцієнт ефективності'
            ]
        ]
        analytics_customer_after = analytics_customer.copy()
        analytics_customer_after.columns = [
            ['', '', '', '', '', 'Ремонт', 'Ремонт', 'Ремонт', 'Ремонт', 'Видача автомобіля', 'Видача автомобіля', 'Аналітичні показники', 'Аналітичні показники'],
            analytics_customer_after.columns
        ]

        # === table 1 ===
        tipheader_table1 = [
            'Показник',
            'Плановий заїзд – Створення запис на СТО',
            'Виїзд з території – Плановий заїзд',
            'Виїзд території – Заїзд на територію',
            'Кількість закритих нормогодин в ЗН / Ремонт загальний'
        ]

        table1 = [
            dash_table.DataTable(
                data=table1.to_dict('records'),
                tooltip_data=[
                    {
                        column: {'value': tipheader_table1[i], 'type': 'markdown'}
                        for i, (column, _) in zip(range(len(table1.columns)), row.items())
                    } for row in table1.to_dict('records')
                ],
                tooltip_duration=None,
                # merge_duplicate_headers=True,
                columns=[{'name': i, 'id': i} for i in table1.columns],
            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 1 ===

        # === table 2 ===
        # tipheader_table2 = [
        #     '',
        #     '',
        #     'Кількість значень по полю підготовка до візиту більше або дорівнює 15 хвилин',
        #     'Кількість значень по полю підготовка до візиту менше 15 хвилин',
        #     '',
        #     'Кількість мінусових значень по колонці перебування після завершення ремонту'
        # ]

        table2 = [
            dash_table.DataTable(
                data=table2.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in table2.columns],
                fixed_columns={'headers': True, 'data': 1},
                # tooltip_data = [
                #     {
                #         column: {'value': tipheader_table2[i], 'type': 'markdown'}
                #         if column in ['Кількість Н-З, підготовлених завчасно', 'Кількість Н-З НЕ підготовлених завчасно', 'Кількість заїздів закритих після виїзду клієнта']
                #         else {'value': row[column], 'type': 'markdown'}
                #         for i, (column, _) in enumerate(row.items())
                #     }
                #     for row in table2.to_dict('records')
                # ],

            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 2 ===

        # === table 3 ===
        tipheader_table3 = [
            'Показник',
            'Плановий заїзд – Створення ЗН, норма: більше 15',
            'Заїзд в зону сервісу – Заїзд на територію, норма: більше 0',
            'Заїзд в зону сервісу - Проведення ЗН',
            'Виїзд з зони сервісу – Заїзд в зону сервісу',
            'Закриття ЗН - Виїзд в зони сервісу',
            'Ремонт загальний - Ремонт відсканований',
            'Виїзд з території – Закриття ЗН',
        ]

        table3 = [
            dash_table.DataTable(
                data=table3.to_dict('records'),
                tooltip_data=[
                    {
                        column: {'value': tipheader_table3[i], 'type': 'markdown'}
                        for i, (column, _) in zip(range(len(table3.columns)), row.items())
                    } for row in table3.to_dict('records')
                ],
                tooltip_duration=None,
                # merge_duplicate_headers=True,
                columns=[{'name': i, 'id': i} for i in table3.columns],
            
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center',
                    # 'color': 'black',
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'lineHeight': '15px',
                },
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#f2f2f2',
                    'fontWeight': 'bold',
                    'font-family': 'Arial, sans-serif',
                    # 'padding': '10px',
                    'textAlign': 'center',
                    'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                    'fontSize': '16px',
                    # 'whiteSpace': 'nowrap',
                    # 'textOverflow': 'ellipsis',
                    # 'overflow': 'hidden',
                },
            ),
        ]
        # === end table 3 ===

    if value_section == 'Всі':
        text1 = f"Показники по всіх зонах в хвилинах"
        text2 = f"Показники по всіх зонах в хвилинах"
        text3 = f"Показники по всіх зонах в хвилинах"
        text5 = f"Показники по всіх зонах в хвилинах"
        text6 = f"Детальна інформація по всіх зонах"
    else:
        text1 = f"Показники в хвилинах ({value_section})"
        text2 = f"Показники в хвилинах ({value_section})"
        text3 = f"Показники в хвилинах ({value_section})"
        text5 = f"Показники в хвилинах ({value_section})"
        text6 = f"Детальна інформація ({value_section})"

    tipheader.remove('Показник')
    tipheader.insert(0, 'ПІБ')
    # tipheader.insert(1, 'Телефон')
    tipheader.insert(1, 'Держ. номер')
    tipheader.insert(2, 'Заявка ТО')

    # analytics_customer.rename(columns={'ПІБ': 'Прізвище Імʼя По-батькові'}, inplace=True)
    table_analytics_customer = [
        dash_table.DataTable(
            data=analytics_customer.to_dict('records'),
            # tooltip_header={analytics_customer.columns[i]: tipheader[i] for i in range(len(analytics_customer.columns))},
            tooltip_data=[
                {
                    column: {'value': tipheader[i], 'type': 'markdown'}
                    for i, (column, _) in zip(range(len(analytics_customer.columns)), row.items())
                } for row in analytics_customer.to_dict('records')
            ],
            tooltip_duration=None,
            merge_duplicate_headers=True,
            columns=[{'name': [i[0], i[1]], 'id': i[1], 'deletable': True} for i in analytics_customer_after.columns],
            sort_action='native',
            style_data_conditional=(
                [
                    {
                        'if': {
                            'filter_query': '{{Підготовка до візиту}} < {}'.format(15),
                            'column_id': 'Підготовка до візиту'
                        },
                        'backgroundColor': '#FF0000',
                        'color': 'black'
                    }
                ]
                +
                [
                    {
                        'if': {
                            'filter_query': '{{Прийомка}} < {}'.format(0),
                            'column_id': 'Прийомка'
                        },
                        'backgroundColor': '#FF0000',
                        'color': 'black'
                    }
                ]
            ),
            style_cell_conditional=(
            ),
            style_cell={
                'height': 'auto',

                # all three widths are needed
                'minWidth': '50px', 'width': '180px', 'maxWidth': '180px',
                'whiteSpace': 'normal',
                'font-family': 'Arial, sans-serif',

                # 'overflow': 'hidden',
                # 'textOverflow': 'ellipsis',
                # 'maxWidth': 0,

                'textAlign': 'center',
            },
            style_header={
                'backgroundColor': '#f2f2f2',
                'fontWeight': 'bold',
                'font-family': 'Arial, sans-serif',
                # 'padding': '10px',
                'textAlign': 'center',
                'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
                'fontSize': '16px',
                # 'whiteSpace': 'nowrap',
                # 'textOverflow': 'ellipsis',
                # 'overflow': 'hidden',
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px',
                'font-size': '14px',
                'text-align': 'center',
                'font-family': 'Arial, sans-serif',
                'color': '#004fd0'
            },
            fixed_columns={'headers': True, 'data': 1},
            fixed_rows={'headers': True},
            style_table={
                'minWidth': '100%',
                'overflowX': 'auto',
            },
            # style_cell ={'width': '100px'},
            # page_action='none',
            virtualization=True,
            # tooltip_duration=None
            # id='tbl-analytics-known',
        ),
    ]

    table_main = dash_table.DataTable(
        data=main.to_dict('records'),
        tooltip_header={i: i for i in main.columns},
        # columns=[{'name': i, 'id': i} for i in main.columns],
        columns=[{'name': i, 'id': i, 'className': 'one-line', 'deletable': True} if i in ['Марка', 'Модель'] else {'name': i, 'id': i, 'deletable': True} for i in main.columns],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '15px',
            'font-size': '14px',
            'text-align': 'center',
            'font-family': 'Arial, sans-serif',
        },
        style_cell={
            # 'padding': '10px',
            'height': 'auto',
            'minWidth': '50px', 'width': '180px', 'maxWidth': '180px',
            'whiteSpace': 'normal',
            # 'overflow': 'hidden',
            # 'textOverflow': 'ellipsis',
            'font-family': 'Arial, sans-serif',
        },
        style_header={
            'backgroundColor': '#f2f2f2',
            'fontWeight': 'bold',
            'font-family': 'Arial, sans-serif',
            # 'padding': '10px',
            'textAlign': 'center',
            'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
            'fontSize': '16px',
            # 'whiteSpace': 'nowrap',
            # 'textOverflow': 'ellipsis',
            # 'overflow': 'hidden',
        },
        style_table={
                'minWidth': '100%',
                'overflowX': 'auto',
        },
        # page_action='native',
        # page_size=20,
        sort_action='native',
        virtualization=True,
        fixed_columns={'headers': True, 'data': 1},
        fixed_rows={'headers': True},
    )

    return table1, table2, table3, table_analytics_customer, table_main, text1, text2, text3, text5, text6,


# CALLBACKS 

# URLs
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")],
)
def render_page_content(pathname):

    if pathname == "/":
        return main_page
    
    elif "/center-kyiv" == pathname:
        return center(pathname)
    
    elif "/center-kyiv/gantt-chart" == pathname:
        return gantt(pathname)

    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


if __name__ == '__main__':
    # run_simple("127.0.0.1", 8050, application, use_reloader=True)
    # app.run_server('0.0.0.0', '8000')
    # app.run_server(debug=True)
    app.run(debug=True)