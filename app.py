import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.db.session import check_connection, init_db

# ── DB ─────────────────────────────────────────────────────────────────────────
db_ok = check_connection()
if db_ok:
    init_db()

# ── App instance ───────────────────────────────────────────────────────────────
from app.dash_app import app, server  # noqa: F401

# ── Importar pages (registra callbacks como efecto secundario) ─────────────────
from app.pages.dashboard import callbacks as _dash_cb              # noqa: F401
from app.pages.dashboard.layout import layout as dashboard_layout
from app.pages.registro import callbacks as _reg_cb                # noqa: F401
from app.pages.registro.layout import layout as registro_layout
from app.pages.estado_de_cuenta import callbacks as _ec_cb         # noqa: F401
from app.pages.estado_de_cuenta.layout import layout as ec_layout
from app.pages.metas import callbacks as _metas_cb                 # noqa: F401
from app.pages.metas.layout import layout as metas_layout
from app.pages.configuracion import callbacks as _cfg_cb           # noqa: F401
from app.pages.configuracion.layout import layout as config_layout

import dash_bootstrap_components as dbc  # noqa: E402
from dash import Input, Output, dcc, html  # noqa: E402
from dash.exceptions import PreventUpdate  # noqa: E402

# ── Nav definition ─────────────────────────────────────────────────────────────
_TABS = [
    ("dashboard",        "Dashboard"),
    ("registro",         "Registro"),
    ("estado_de_cuenta", "Estado de Cuenta"),
    ("metas",            "Metas"),
    ("configuracion",    "Configuración"),
]

_mes_badge = date.today().strftime("%b %Y")

# ── Custom dark nav ────────────────────────────────────────────────────────────
_nav = html.Nav(
    [
        html.Div(
            [
                html.Span("CF", style={"color": "var(--cf-accent)"}),
                html.Span("//", className="cf-logo-slash"),
                html.Span("FLOW"),
                html.Span("finanzas personales", className="cf-logo-sub"),
            ],
            className="cf-logo",
        ),
        html.Div(
            [
                html.Button(
                    label,
                    id=f"nav-{tab_id}",
                    className="cf-nav-tab active" if tab_id == "dashboard" else "cf-nav-tab",
                    n_clicks=0,
                )
                for tab_id, label in _TABS
            ],
            className="cf-nav-tabs",
        ),
        html.Div(
            [
                html.Div(_mes_badge, className="cf-badge"),
                html.Div(
                    "● En línea" if db_ok else "● Sin DB",
                    className="cf-badge cf-badge-online",
                ),
            ],
            className="cf-nav-right",
        ),
    ],
    className="cf-nav",
)

# ── DB status bar ──────────────────────────────────────────────────────────────
_db_bar = html.Div(
    "● Conectado a PostgreSQL" if db_ok else "⚠ Sin conexión a PostgreSQL — revisa DATABASE_URL",
    style={
        "background": "rgba(0,229,160,0.08)" if db_ok else "rgba(255,71,87,0.1)",
        "color": "var(--cf-accent)" if db_ok else "var(--cf-danger)",
        "borderBottom": "1px solid var(--cf-border)",
        "fontSize": "12px",
        "textAlign": "center",
        "padding": "6px 28px",
    },
)

# ── Root layout ────────────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        _nav,
        _db_bar,
        dcc.Location(id="url"),
        dcc.Store(id="active-tab",        data="dashboard"),
        dcc.Store(id="store-refresh",     data=0),
        dcc.Store(id="store-tx-trigger",  data=0),
        dcc.Store(id="store-cfg-trigger", data=0),
        html.Div(id="page-content"),
    ]
)


# ── Merge triggers → store-refresh ────────────────────────────────────────────
@app.callback(
    Output("store-refresh",    "data"),
    Input("store-tx-trigger",  "data"),
    Input("store-cfg-trigger", "data"),
    prevent_initial_call=True,
)
def merge_refresh(tx, cfg):
    return (tx or 0) + (cfg or 0)


# ── Nav tab switching ──────────────────────────────────────────────────────────
@app.callback(
    Output("active-tab", "data"),
    *[Output(f"nav-{tid}", "className") for tid, _ in _TABS],
    *[Input(f"nav-{tid}", "n_clicks") for tid, _ in _TABS],
    prevent_initial_call=True,
)
def switch_tab(*_args):
    from dash import ctx
    tid = ctx.triggered_id
    if tid is None:
        raise PreventUpdate
    active = tid.replace("nav-", "")
    classes = [
        "cf-nav-tab active" if f"nav-{t}" == tid else "cf-nav-tab"
        for t, _ in _TABS
    ]
    return active, *classes


# ── Page render ────────────────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("active-tab",    "data"),
)
def render_page(tab):
    pages = {
        "dashboard":        dashboard_layout,
        "registro":         registro_layout,
        "estado_de_cuenta": ec_layout,
        "metas":            metas_layout,
        "configuracion":    config_layout,
    }
    return pages.get(tab, html.Div(
        html.P("Página no encontrada.", style={"color": "var(--cf-muted)", "padding": "32px"})
    ))


if __name__ == "__main__":
    debug = os.getenv("DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
