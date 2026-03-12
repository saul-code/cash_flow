from datetime import date

import dash_bootstrap_components as dbc
from dash import dcc, html

_this_year  = date.today().year
_this_month = date.today().month

_month_opts = [
    {"label": m, "value": i}
    for i, m in enumerate(
        ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        start=1,
    )
]

layout = html.Div(
    [
        # ── Header + filters ───────────────────────────────────────────────────
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Estado de Cuenta", className="cf-card-label", style={"marginBottom": "0"}),
                        html.Div("Historial completo de transacciones", style={"fontSize": "11px", "color": "var(--cf-muted)"}),
                    ]
                ),
                # Summary chips (rendered by callback)
                html.Div(id="ec-resumen", style={"display": "flex", "gap": "12px", "alignItems": "center", "flexWrap": "wrap"}),
            ],
            className="cf-table-header-bar",
        ),

        # Filters row
        html.Div(
            [
                dbc.Input(
                    id="ec-search",
                    placeholder="🔍  Buscar por descripción...",
                    style={
                        "background": "var(--cf-surface2)",
                        "border": "1px solid var(--cf-border)",
                        "borderRadius": "8px",
                        "color": "var(--cf-text)",
                        "fontSize": "12px",
                        "height": "32px",
                        "width": "240px",
                        "padding": "0 12px",
                    },
                ),
                html.Div(
                    [
                        dbc.Select(
                            id="ec-sel-mes",
                            options=_month_opts,
                            value=_this_month,
                            style={"fontSize": "12px", "height": "32px", "width": "130px"},
                        ),
                        dbc.Select(
                            id="ec-sel-year",
                            options=[{"label": str(y), "value": y} for y in range(_this_year - 3, _this_year + 1)],
                            value=_this_year,
                            style={"fontSize": "12px", "height": "32px", "width": "90px"},
                        ),
                    ],
                    style={"display": "flex", "gap": "8px"},
                ),
                dcc.Store(id="ec-filter-tipo", data="todas"),
                html.Div("Todas",  id="ec-chip-todas",  className="cf-chip active", n_clicks=0),
                html.Div("Cargos", id="ec-chip-cargos", className="cf-chip", n_clicks=0),
                html.Div("Abonos", id="ec-chip-abonos", className="cf-chip", n_clicks=0),
                html.Div("MSI",    id="ec-chip-msi",    className="cf-chip", n_clicks=0),
            ],
            className="cf-ec-filters",
        ),

        # Table
        html.Div(id="ec-tabla-body", style={"overflowX": "auto"}),
    ],
    className="cf-table-card cf-page",
    style={"borderRadius": "14px", "margin": "24px 28px", "overflow": "hidden"},
)
