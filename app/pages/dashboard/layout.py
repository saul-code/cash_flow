from datetime import date

import dash_bootstrap_components as dbc
from dash import dcc, html

_mes = date.today().strftime("%B %Y").capitalize()

layout = html.Div(
    [
        # ── Top KPI cards ──────────────────────────────────────────────────────
        html.Div(
            [
                # Saldo disponible
                html.Div(
                    [
                        html.Div("Saldo Disponible", className="cf-card-label"),
                        html.Div("—", id="d-kpi-saldo", className="cf-card-value green"),
                        html.Div(id="d-kpi-saldo-sub", className="cf-card-sub"),
                    ],
                    className="cf-card green",
                ),
                # Gasto del mes
                html.Div(
                    [
                        html.Div("Gasto del Mes", className="cf-card-label"),
                        html.Div("—", id="d-kpi-gasto", className="cf-card-value blue"),
                        html.Div(id="d-kpi-gasto-sub", className="cf-card-sub"),
                    ],
                    className="cf-card blue",
                ),
                # Próximo pago
                html.Div(
                    [
                        html.Div("Próximo Pago", className="cf-card-label"),
                        html.Div("—", id="d-kpi-pago", className="cf-card-value orange"),
                        html.Div(id="d-kpi-pago-sub", className="cf-card-sub"),
                    ],
                    className="cf-card orange",
                ),
                # ¿Me alcanza?
                html.Div(
                    [
                        html.Div("¿Me alcanza?", className="cf-card-label"),
                        html.Div(
                            "¿Cuánto quiero gastar?",
                            style={"fontSize": "11px", "color": "var(--cf-muted)", "marginBottom": "8px"},
                        ),
                        html.Div(
                            [
                                dbc.Input(
                                    id="d-alcanza-input",
                                    type="number",
                                    placeholder="0.00",
                                    className="cf-mini-input",
                                    style={"flex": "1", "maxWidth": "130px"},
                                ),
                                html.Button("Calcular", id="d-btn-alcanza", className="cf-btn-check"),
                            ],
                            style={"display": "flex", "alignItems": "center", "gap": "8px"},
                        ),
                        html.Div(id="d-alcanza-result"),
                    ],
                    className="cf-card cf-alcanza-card",
                ),
            ],
            className="cf-topline",
        ),

        # ── Main grid ──────────────────────────────────────────────────────────
        html.Div(
            [
                # Left column: chart + upload
                html.Div(
                    [
                        # Flujo chart
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            "Flujo del Mes — Ingresos vs Egresos",
                                            className="cf-chart-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("Semana", id="d-chip-semana", className="cf-chip active", n_clicks=0),
                                                html.Div("Mes",    id="d-chip-mes",    className="cf-chip", n_clicks=0),
                                                html.Div("3M",     id="d-chip-3m",     className="cf-chip", n_clicks=0),
                                            ],
                                            className="cf-chip-group",
                                        ),
                                    ],
                                    className="cf-chart-header",
                                ),
                                dcc.Store(id="d-flujo-period", data="semana"),
                                dcc.Graph(
                                    id="d-chart-flujo",
                                    config={"displayModeBar": False},
                                    style={"height": "200px"},
                                ),
                                html.Div(
                                    [
                                        html.Span("● Ingresos", style={"fontSize": "11px", "color": "var(--cf-accent)"}),
                                        html.Span("● Egresos",  style={"fontSize": "11px", "color": "var(--cf-danger)", "marginLeft": "16px"}),
                                        html.Span("● MSI no cuenta como gasto real", style={"fontSize": "11px", "color": "var(--cf-muted)", "marginLeft": "16px"}),
                                    ],
                                    style={"marginTop": "8px"},
                                ),
                            ],
                            className="cf-chart-card",
                        ),

                        # Upload zone
                        html.Div(
                            [
                                html.Div("NUEVO", className="cf-new-badge"),
                                html.Div("📄", className="cf-upload-icon"),
                                html.Div("Importar Estado de Cuenta", className="cf-upload-title"),
                                html.Div(
                                    "Arrastra tu PDF o imagen — la app detecta y llena las transacciones automáticamente",
                                    className="cf-upload-sub",
                                ),
                                html.Div(
                                    [html.Div(p, className="cf-upload-pill") for p in
                                     ["PDF", "PNG / JPG", "Banamex", "BBVA", "Santander", "Amex"]],
                                    className="cf-upload-pills",
                                ),
                            ],
                            className="cf-upload-zone",
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column", "gap": "14px"},
                ),

                # Right: side panel
                html.Div(
                    [
                        # Mis tarjetas
                        html.Div(
                            [
                                html.Div("Mis Tarjetas", className="cf-section-title"),
                                html.Div(id="d-tarjetas-list"),
                                html.Div(
                                    "+ Agregar tarjeta",
                                    className="cf-link",
                                    style={"marginTop": "12px", "textAlign": "center"},
                                ),
                            ],
                            className="cf-card",
                            style={"padding": "18px 20px"},
                        ),
                        # Próximos pagos
                        html.Div(
                            [
                                html.Div("Próximos Pagos", className="cf-section-title"),
                                html.Div(id="d-pagos-list"),
                            ],
                            className="cf-card",
                            style={"padding": "18px 20px"},
                        ),
                        # Metas de ahorro
                        html.Div(
                            [
                                html.Div("Metas de Ahorro", className="cf-section-title"),
                                html.Div(id="d-metas-list"),
                                html.Div(
                                    "+ Nueva meta",
                                    className="cf-link",
                                    style={"marginTop": "8px", "textAlign": "center"},
                                ),
                            ],
                            className="cf-meta-card",
                        ),
                    ],
                    className="cf-side-panel",
                ),
            ],
            className="cf-main-grid",
        ),

        # ── Bottom grid ────────────────────────────────────────────────────────
        html.Div(
            [
                # Gasto por categoría
                html.Div(
                    [
                        html.Div(f"Gasto por Categoría — {_mes}", className="cf-card-label", style={"marginBottom": "12px"}),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="d-chart-donut",
                                    config={"displayModeBar": False},
                                    style={"width": "130px", "height": "130px", "flexShrink": "0"},
                                ),
                                html.Div(id="d-categoria-legend", style={"flex": "1"}),
                            ],
                            style={"display": "flex", "alignItems": "center", "gap": "24px"},
                        ),
                    ],
                    className="cf-card",
                ),
                # Proyección
                html.Div(
                    [
                        html.Div(
                            "Proyección — Si sigues así",
                            className="cf-card-label",
                            style={"marginBottom": "12px"},
                        ),
                        html.Div(id="d-proyeccion"),
                    ],
                    className="cf-card",
                ),
            ],
            className="cf-grid-bottom",
        ),

        # ── Transactions table ─────────────────────────────────────────────────
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Últimas Transacciones", className="cf-table-title"),
                        html.Div(
                            [
                                dbc.Input(
                                    id="d-search",
                                    placeholder="🔍  Buscar...",
                                    style={
                                        "background": "var(--cf-surface2)",
                                        "border": "1px solid var(--cf-border)",
                                        "borderRadius": "8px",
                                        "color": "var(--cf-text)",
                                        "fontSize": "12px",
                                        "height": "32px",
                                        "width": "200px",
                                        "padding": "0 12px",
                                    },
                                ),
                                dcc.Store(id="d-tabla-filter", data="todas"),
                                html.Div("Todas", id="d-chip-todas",  className="cf-chip active", n_clicks=0),
                                html.Div("Cargos", id="d-chip-cargos", className="cf-chip", n_clicks=0),
                                html.Div("Abonos", id="d-chip-abonos", className="cf-chip", n_clicks=0),
                                html.Div("MSI",    id="d-chip-msi-f",  className="cf-chip", n_clicks=0),
                            ],
                            style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap"},
                        ),
                    ],
                    className="cf-table-header-bar",
                ),
                html.Div(id="d-tabla-body", style={"overflowX": "auto"}),
            ],
            className="cf-table-card",
        ),

        html.Div(className="cf-spacer"),
    ],
    className="cf-page",
)
