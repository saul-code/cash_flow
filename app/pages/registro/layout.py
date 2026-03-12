from datetime import date

import dash_bootstrap_components as dbc
from dash import dcc, html

layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div("Registrar Transacción", className="cf-card-label", style={"marginBottom": "16px"}),
                                # Fecha + Monto
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Fecha"),
                                                dbc.Input(id="r-inp-fecha", type="date", value=str(date.today())),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Monto ($)"),
                                                dbc.Input(id="r-inp-monto", type="number", placeholder="0.00", min=0, step=0.01),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                # Descripción
                                dbc.Label("Descripción"),
                                dbc.Input(
                                    id="r-inp-desc",
                                    type="text",
                                    placeholder="Ej. Amazon, Supermercado...",
                                    className="mb-3",
                                ),
                                # Tarjeta + Categoría
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Tarjeta"),
                                                dcc.Dropdown(id="r-dd-tarjeta", placeholder="Seleccionar...", clearable=False),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Categoría"),
                                                dcc.Dropdown(id="r-dd-categoria", placeholder="Sin categoría", clearable=True),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                # Tipo + MSI switch
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Tipo"),
                                                dcc.Dropdown(
                                                    id="r-dd-tipo",
                                                    options=[
                                                        {"label": "Cargo",  "value": "cargo"},
                                                        {"label": "Abono",  "value": "abono"},
                                                    ],
                                                    value="cargo",
                                                    clearable=False,
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("MSI"),
                                                dbc.Switch(id="r-sw-msi", label="Activar MSI", value=False, className="mt-1"),
                                            ],
                                            width=6,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                # Plazo MSI (collapse)
                                dbc.Collapse(
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                dbc.Label("Número de meses"),
                                                dbc.Input(id="r-inp-meses", type="number", value=3, min=2, max=36, step=1),
                                            ],
                                            width=8,
                                        ),
                                        className="mb-3",
                                    ),
                                    id="r-collapse-msi",
                                    is_open=False,
                                ),
                                # Submit
                                dbc.Button("Guardar Transacción", id="r-btn-guardar", color="primary", className="w-100 mt-1"),
                                html.Div(id="r-alert-guardar", className="mt-3"),
                            ],
                            className="cf-card",
                            style={"padding": "28px 32px"},
                        )
                    ]
                ),
                md=6, lg=5,
                className="mx-auto",
            ),
            className="justify-content-center mt-4",
        ),
        html.Div(className="cf-spacer"),
    ],
    className="cf-page",
)
