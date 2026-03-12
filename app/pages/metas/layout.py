import dash_bootstrap_components as dbc
from dash import html

_COLOR_OPTS = [
    {"label": "Azul",    "value": "#0099ff"},
    {"label": "Verde",   "value": "#00e5a0"},
    {"label": "Naranja", "value": "#ff6b35"},
    {"label": "Morado",  "value": "#a259ff"},
    {"label": "Rojo",    "value": "#ff4757"},
    {"label": "Amarillo","value": "#fbbf24"},
]

layout = html.Div(
    [
        dbc.Row(
            [
                # Left: existing goals
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div("Mis Metas de Ahorro", className="cf-card-label", style={"marginBottom": "16px"}),
                                html.Div(id="m-lista-metas"),
                            ],
                            className="cf-card",
                            style={"padding": "24px"},
                        )
                    ],
                    md=7,
                    className="mb-4",
                ),
                # Right: new goal form
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div("Nueva Meta", className="cf-card-label", style={"marginBottom": "16px"}),
                                dbc.Label("Nombre"),
                                dbc.Input(id="m-inp-nombre", placeholder="Ej. Vacaciones, MacBook...", className="mb-3"),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Emoji"),
                                                dbc.Input(id="m-inp-emoji", placeholder="🎯", maxLength=2, className="mb-3"),
                                            ],
                                            width=4,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Color"),
                                                dbc.Select(
                                                    id="m-sel-color",
                                                    options=_COLOR_OPTS,
                                                    value="#0099ff",
                                                    className="mb-3",
                                                ),
                                            ],
                                            width=8,
                                        ),
                                    ]
                                ),
                                dbc.Label("Monto Objetivo ($)"),
                                dbc.Input(id="m-inp-objetivo", type="number", placeholder="0.00", min=0, step=0.01, className="mb-3"),
                                dbc.Label("Monto Actual ($)"),
                                dbc.Input(id="m-inp-actual", type="number", placeholder="0.00", min=0, step=0.01, className="mb-3"),
                                dbc.Button("Agregar Meta", id="m-btn-guardar", color="primary", className="w-100"),
                                html.Div(id="m-alert", className="mt-3"),
                            ],
                            className="cf-card",
                            style={"padding": "24px"},
                        )
                    ],
                    md=5,
                    className="mb-4",
                ),
            ]
        ),
        html.Div(className="cf-spacer"),
    ],
    className="cf-page",
)
