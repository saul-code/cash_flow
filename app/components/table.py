import dash_bootstrap_components as dbc
from dash import Input, Output, dash_table, html

from app.dash_app import app
from app.db.models import Transaccion
from app.db.session import SessionLocal

# ── Layout ─────────────────────────────────────────────────────────────────────
layout = dbc.Card(
    [
        dbc.CardHeader(html.H5("Últimas 20 Transacciones", className="mb-0")),
        dbc.CardBody(
            dash_table.DataTable(
                id="tabla-transacciones",
                columns=[
                    {"name": "Fecha",       "id": "fecha"},
                    {"name": "Descripción", "id": "descripcion"},
                    {"name": "Monto",       "id": "monto"},
                    {"name": "Tipo",        "id": "tipo_movimiento"},
                    {"name": "Tarjeta",     "id": "tarjeta"},
                    {"name": "Categoría",   "id": "categoria"},
                    {"name": "MSI",         "id": "msi"},
                ],
                data=[],
                page_size=20,
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "8px 12px",
                    "fontFamily": "inherit",
                    "fontSize": "14px",
                },
                style_header={
                    "fontWeight": "bold",
                    "backgroundColor": "#f8f9fa",
                    "borderBottom": "2px solid #dee2e6",
                },
                style_data_conditional=[
                    {
                        "if": {
                            "filter_query": '{tipo_movimiento} = "cargo"',
                            "column_id": "monto",
                        },
                        "color": "#dc3545",
                        "fontWeight": "600",
                    },
                    {
                        "if": {
                            "filter_query": '{tipo_movimiento} = "abono"',
                            "column_id": "monto",
                        },
                        "color": "#198754",
                        "fontWeight": "600",
                    },
                ],
            )
        ),
    ],
    className="shadow-sm",
)

# ── Callback ───────────────────────────────────────────────────────────────────


@app.callback(
    Output("tabla-transacciones", "data"),
    Input("store-refresh", "data"),
)
def update_tabla(_refresh):
    session = SessionLocal()
    try:
        rows = (
            session.query(Transaccion)
            .order_by(Transaccion.fecha.desc(), Transaccion.id.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "fecha": str(r.fecha),
                "descripcion": r.descripcion,
                "monto": f"${r.monto:,.2f}",
                "tipo_movimiento": r.tipo_movimiento,
                "tarjeta": r.tarjeta.banco
                + (f" *{r.tarjeta.terminacion}" if r.tarjeta.terminacion else ""),
                "categoria": r.categoria.nombre if r.categoria else "—",
                "msi": f"{r.plazo_msi}p" if r.es_msi else "—",
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[update_tabla] {e}")
        return []
    finally:
        session.close()
