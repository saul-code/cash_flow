import os

from dotenv import load_dotenv

load_dotenv()

from app.db.session import check_connection, init_db

# ── DB ─────────────────────────────────────────────────────────────────────────
db_ok = check_connection()
if db_ok:
    init_db()

# ── App instance ───────────────────────────────────────────────────────────────
from app.dash_app import app, server  # noqa: E402, F401

# ── Importar componentes (registra callbacks como efecto secundario) ───────────
from app.components.charts import charts_layout, kpi_row  # noqa: E402
from app.components.config import layout as config_layout  # noqa: E402
from app.components.form import layout as form_layout      # noqa: E402
from app.components.table import layout as table_layout    # noqa: E402

# ── Dependencias de layout ─────────────────────────────────────────────────────
import dash_bootstrap_components as dbc  # noqa: E402
from dash import Input, Output, dcc, html  # noqa: E402

# ── Navbar ─────────────────────────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container(
        dbc.NavbarBrand("Cash Flow — Finanzas Personales", className="fw-bold fs-5"),
        fluid=True,
    ),
    color="primary",
    dark=True,
)

# ── Layout principal ───────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                dcc.Location(id="url"),
                dcc.Store(id="store-refresh", data=0),
                dcc.Store(id="store-tx-trigger", data=0),
                dcc.Store(id="store-cfg-trigger", data=0),
                dbc.Alert(
                    "Conexión a PostgreSQL: OK"
                    if db_ok
                    else "Conexión a PostgreSQL: FALLO — revisa DATABASE_URL",
                    color="success" if db_ok else "danger",
                    dismissable=True,
                    className="mt-3 mb-2",
                ),
                dbc.Tabs(
                    [
                        dbc.Tab(label="Dashboard",     tab_id="tab-dashboard"),
                        dbc.Tab(label="Registro",      tab_id="tab-registro"),
                        dbc.Tab(label="Configuración", tab_id="tab-config"),
                    ],
                    id="tabs-main",
                    active_tab="tab-dashboard",
                    className="mb-4",
                ),
                html.Div(id="tab-content"),
            ],
            fluid=True,
            className="px-4",
        ),
    ]
)

# ── Callback de navegación ─────────────────────────────────────────────────────


@app.callback(
    Output("store-refresh", "data"),
    Input("store-tx-trigger", "data"),
    Input("store-cfg-trigger", "data"),
    prevent_initial_call=True,
)
def merge_refresh(tx, cfg):
    return (tx or 0) + (cfg or 0)


@app.callback(
    Output("tab-content", "children"),
    Input("tabs-main", "active_tab"),
)
def render_tab(tab):
    if tab == "tab-dashboard":
        return html.Div(
            [
                # Fila 1: KPI Cards
                kpi_row,
                # Fila 2: Gráfica ancho completo
                dbc.Row(
                    dbc.Col(charts_layout, className="mb-4")
                ),
                # Fila 3: Tabla de transacciones
                dbc.Row(
                    dbc.Col(table_layout, className="mb-4")
                ),
            ]
        )

    if tab == "tab-registro":
        return dbc.Row(
            dbc.Col(form_layout, md=6, lg=5, className="mx-auto mb-4"),
            className="justify-content-center mt-2",
        )

    if tab == "tab-config":
        return config_layout

    return html.P("Pestaña no encontrada.")


if __name__ == "__main__":
    debug = os.getenv("DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
