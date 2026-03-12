from datetime import date

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update
from dateutil.relativedelta import relativedelta

from app.dash_app import app
from app.db.models import Categoria, ParcialidadMSI, Tarjeta, Transaccion
from app.db.session import SessionLocal

# ── Layout ─────────────────────────────────────────────────────────────────────
layout = dbc.Card(
    [
        dbc.CardHeader(html.H5("Registrar Transacción", className="mb-0")),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Fecha", html_for="inp-fecha"),
                                dbc.Input(
                                    id="inp-fecha",
                                    type="date",
                                    value=str(date.today()),
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Monto ($)", html_for="inp-monto"),
                                dbc.Input(
                                    id="inp-monto",
                                    type="number",
                                    placeholder="0.00",
                                    min=0,
                                    step=0.01,
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Label("Descripción", html_for="inp-desc"),
                dbc.Input(
                    id="inp-desc",
                    type="text",
                    placeholder="Ej. Amazon, Supermercado...",
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Tarjeta", html_for="dd-tarjeta"),
                                dcc.Dropdown(
                                    id="dd-tarjeta",
                                    placeholder="Seleccionar...",
                                    clearable=False,
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Categoría", html_for="dd-categoria"),
                                dcc.Dropdown(
                                    id="dd-categoria",
                                    placeholder="Sin categoría",
                                    clearable=True,
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Tipo"),
                                dcc.Dropdown(
                                    id="dd-tipo",
                                    options=[
                                        {"label": "Cargo", "value": "cargo"},
                                        {"label": "Abono", "value": "abono"},
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
                                dbc.Switch(
                                    id="sw-msi",
                                    label="Activar MSI",
                                    value=False,
                                    className="mt-1",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Collapse(
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Label("Número de meses", html_for="inp-meses"),
                                dbc.Input(
                                    id="inp-meses",
                                    type="number",
                                    value=3,
                                    min=2,
                                    max=36,
                                    step=1,
                                ),
                            ],
                            width=8,
                        ),
                        className="mb-3",
                    ),
                    id="collapse-msi",
                    is_open=False,
                ),
                dbc.Button(
                    "Guardar",
                    id="btn-guardar",
                    color="primary",
                    className="w-100 mt-1",
                ),
                html.Div(id="alert-guardar", className="mt-3"),
            ]
        ),
    ],
    className="shadow-sm h-100",
)

# ── Callbacks ──────────────────────────────────────────────────────────────────


@app.callback(
    Output("dd-tarjeta", "options"),
    Output("dd-categoria", "options"),
    Input("url", "pathname"),
    Input("store-refresh", "data"),
)
def load_options(_pathname, _refresh):
    session = SessionLocal()
    try:
        tarjetas = session.query(Tarjeta).order_by(Tarjeta.banco).all()
        categorias = session.query(Categoria).order_by(Categoria.nombre).all()
        t_opts = [
            {
                "label": t.banco
                + (f" — {t.nombre_alias}" if t.nombre_alias else "")
                + (f" *{t.terminacion}" if t.terminacion else ""),
                "value": t.id,
            }
            for t in tarjetas
        ]
        c_opts = [{"label": c.nombre, "value": c.id} for c in categorias]
        return t_opts, c_opts
    except Exception as e:
        print(f"[load_options] {e}")
        return [], []
    finally:
        session.close()


@app.callback(
    Output("collapse-msi", "is_open"),
    Input("sw-msi", "value"),
)
def toggle_msi_collapse(sw):
    return bool(sw)


@app.callback(
    Output("alert-guardar", "children"),
    Output("store-tx-trigger", "data"),
    Output("inp-fecha", "value"),
    Output("inp-monto", "value"),
    Output("inp-desc", "value"),
    Output("dd-tarjeta", "value"),
    Output("dd-categoria", "value"),
    Output("dd-tipo", "value"),
    Output("sw-msi", "value"),
    Output("inp-meses", "value"),
    Input("btn-guardar", "n_clicks"),
    State("inp-fecha", "value"),
    State("inp-monto", "value"),
    State("inp-desc", "value"),
    State("dd-tarjeta", "value"),
    State("dd-categoria", "value"),
    State("dd-tipo", "value"),
    State("sw-msi", "value"),
    State("inp-meses", "value"),
    State("store-tx-trigger", "data"),
    prevent_initial_call=True,
)
def guardar_transaccion(
    n_clicks, fecha, monto, desc, tarjeta_id, cat_id, tipo, es_msi, meses, refresh_count
):
    _no_clear = (no_update,) * 8

    if not all([fecha, monto is not None, desc, tarjeta_id, tipo]):
        return (
            dbc.Alert(
                "Completa los campos obligatorios: fecha, monto, descripción, tarjeta y tipo.",
                color="warning",
                dismissable=True,
            ),
            refresh_count,
            *_no_clear,
        )

    session = SessionLocal()
    try:
        fecha_dt = date.fromisoformat(fecha)
        plazo = int(meses) if es_msi and meses else 1

        tx = Transaccion(
            tarjeta_id=int(tarjeta_id),
            categoria_id=int(cat_id) if cat_id else None,
            fecha=fecha_dt,
            descripcion=desc.strip(),
            monto=float(monto),
            tipo_movimiento=tipo,
            es_msi=bool(es_msi),
            plazo_msi=plazo,
        )
        session.add(tx)
        session.flush()

        if es_msi and plazo > 1:
            monto_parcialidad = round(float(monto) / plazo, 2)
            for num in range(1, plazo + 1):
                mes_cobro = fecha_dt.replace(day=1) + relativedelta(months=num)
                session.add(
                    ParcialidadMSI(
                        transaccion_id=tx.id,
                        numero_pago=num,
                        monto_parcialidad=monto_parcialidad,
                        mes_cobro=mes_cobro,
                    )
                )

        session.commit()

        msg = f"Transacción guardada (ID {tx.id})."
        if es_msi and plazo > 1:
            msg += f" {plazo} parcialidades MSI de ${monto_parcialidad:,.2f} c/u."

        return (
            dbc.Alert(msg, color="success", dismissable=True),
            (refresh_count or 0) + 1,
            str(date.today()),  # inp-fecha
            None,  # inp-monto
            "",  # inp-desc
            None,  # dd-tarjeta
            None,  # dd-categoria
            "cargo",  # dd-tipo
            False,  # sw-msi
            3,  # inp-meses
        )
    except Exception as e:
        session.rollback()
        print(f"[guardar] {e}")
        return (
            dbc.Alert(f"Error al guardar: {e}", color="danger", dismissable=True),
            refresh_count,
            *_no_clear,
        )
    finally:
        session.close()
