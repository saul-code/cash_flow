import dash_bootstrap_components as dbc
from dash import dash_table, html

layout = html.Div(
    [
        dbc.Row(
            [
                # Agregar Tarjeta
                dbc.Col(
                    html.Div(
                        [
                            html.Div("Agregar Tarjeta", className="cf-card-label", style={"marginBottom": "16px"}),
                            dbc.Row(
                                [
                                    dbc.Col([dbc.Label("Banco"), dbc.Input(id="c-banco", placeholder="BBVA, Santander, HSBC...")], md=6),
                                    dbc.Col([dbc.Label("Alias"), dbc.Input(id="c-alias", placeholder="Mi BBVA Oro (opcional)")], md=6),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col([dbc.Label("Terminación"), dbc.Input(id="c-terminacion", placeholder="1234", maxLength=4)], md=4),
                                    dbc.Col([dbc.Label("Día de Corte"), dbc.Input(id="c-dia-corte", type="number", min=1, max=31, step=1, placeholder="1–31")], md=4),
                                    dbc.Col([dbc.Label("Días para Pago"), dbc.Input(id="c-dias-pago", type="number", min=1, max=60, step=1, placeholder="ej. 20")], md=4),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                dbc.Col([dbc.Label("Límite de Crédito ($)"), dbc.Input(id="c-limite", type="number", placeholder="0.00 (opcional)", min=0, step=0.01)], md=6),
                                className="mb-3",
                            ),
                            dbc.Button("Guardar Tarjeta", id="c-btn-tarjeta", color="primary", className="w-100"),
                            html.Div(id="c-alert-tarjeta", className="mt-3"),
                        ],
                        className="cf-card",
                        style={"padding": "24px"},
                    ),
                    md=7,
                    className="mb-4",
                ),
                # Perfil Financiero
                dbc.Col(
                    html.Div(
                        [
                            html.Div("Perfil Financiero", className="cf-card-label", style={"marginBottom": "16px"}),
                            dbc.Label("Ingreso Mensual Neto ($)"),
                            dbc.Input(id="c-ingreso", type="number", placeholder="0.00", min=0, step=0.01, className="mb-1"),
                            html.P(
                                "Se usa para proyecciones y alertas de gasto.",
                                className="text-muted small mb-3",
                                style={"color": "var(--cf-muted) !important", "fontSize": "11px"},
                            ),
                            dbc.Button("Guardar Perfil", id="c-btn-perfil", color="success", className="w-100"),
                            html.Div(id="c-alert-perfil", className="mt-3"),
                        ],
                        className="cf-card",
                        style={"padding": "24px"},
                    ),
                    md=5,
                    className="mb-4",
                ),
            ]
        ),
        # Tarjetas registradas
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Div("Tarjetas Registradas", className="cf-card-label", style={"marginBottom": "16px"}),
                        dash_table.DataTable(
                            id="c-tabla-tarjetas",
                            columns=[
                                {"name": "Banco",          "id": "banco"},
                                {"name": "Alias",          "id": "alias"},
                                {"name": "Terminación",    "id": "terminacion"},
                                {"name": "Día de Corte",   "id": "dia_corte"},
                                {"name": "Días para Pago", "id": "dias_pago"},
                                {"name": "Límite",         "id": "limite"},
                            ],
                            data=[],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "11px 16px", "fontFamily": "DM Sans, sans-serif", "fontSize": "13px"},
                            style_header={"fontWeight": "500", "fontSize": "10px", "letterSpacing": "0.1em", "textTransform": "uppercase"},
                        ),
                    ],
                    className="cf-card",
                    style={"padding": "24px"},
                ),
                className="mb-4",
            )
        ),
        html.Div(className="cf-spacer"),
    ],
    className="cf-page",
)
