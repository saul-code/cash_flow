import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, html, no_update

from app.dash_app import app
from app.db.models import PerfilFinanciero, Tarjeta
from app.db.session import SessionLocal

# ── Formulario: Agregar Tarjeta ────────────────────────────────────────────────
tarjeta_form = dbc.Card(
    [
        dbc.CardHeader(html.H5("Agregar Tarjeta", className="mb-0")),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Banco", html_for="cfg-banco"),
                                dbc.Input(
                                    id="cfg-banco",
                                    placeholder="BBVA, Santander, HSBC...",
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Alias", html_for="cfg-alias"),
                                dbc.Input(
                                    id="cfg-alias",
                                    placeholder="Mi BBVA Oro (opcional)",
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Terminación", html_for="cfg-terminacion"),
                                dbc.Input(
                                    id="cfg-terminacion",
                                    placeholder="1234",
                                    maxLength=4,
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Día de Corte", html_for="cfg-dia-corte"),
                                dbc.Input(
                                    id="cfg-dia-corte",
                                    type="number",
                                    min=1,
                                    max=31,
                                    step=1,
                                    placeholder="1–31",
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Días para Pago", html_for="cfg-dias-pago"),
                                dbc.Input(
                                    id="cfg-dias-pago",
                                    type="number",
                                    min=1,
                                    max=60,
                                    step=1,
                                    placeholder="ej. 20",
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Label("Límite de Crédito ($)", html_for="cfg-limite"),
                            dbc.Input(
                                id="cfg-limite",
                                type="number",
                                placeholder="0.00 (opcional)",
                                min=0,
                                step=0.01,
                            ),
                        ],
                        md=6,
                    ),
                    className="mb-3",
                ),
                dbc.Button(
                    "Guardar Tarjeta",
                    id="btn-guardar-tarjeta",
                    color="primary",
                    className="w-100",
                ),
                html.Div(id="alert-cfg-tarjeta", className="mt-3"),
            ]
        ),
    ],
    className="shadow-sm mb-4",
)

# ── Formulario: Perfil Financiero ──────────────────────────────────────────────
perfil_form = dbc.Card(
    [
        dbc.CardHeader(html.H5("Perfil Financiero", className="mb-0")),
        dbc.CardBody(
            [
                dbc.Label("Ingreso Mensual Neto ($)", html_for="cfg-ingreso"),
                dbc.Input(
                    id="cfg-ingreso",
                    type="number",
                    placeholder="0.00",
                    min=0,
                    step=0.01,
                    className="mb-1",
                ),
                html.P(
                    "Se usa para calcular el porcentaje de gasto vs ingreso.",
                    className="text-muted small mb-3",
                ),
                dbc.Button(
                    "Guardar Perfil",
                    id="btn-guardar-perfil",
                    color="success",
                    className="w-100",
                ),
                html.Div(id="alert-cfg-perfil", className="mt-3"),
            ]
        ),
    ],
    className="shadow-sm mb-4",
)

# ── Tabla de tarjetas registradas ──────────────────────────────────────────────
tarjetas_card = dbc.Card(
    [
        dbc.CardHeader(html.H5("Tarjetas Registradas", className="mb-0")),
        dbc.CardBody(
            dash_table.DataTable(
                id="tabla-tarjetas",
                columns=[
                    {"name": "Banco", "id": "banco"},
                    {"name": "Alias", "id": "alias"},
                    {"name": "Terminación", "id": "terminacion"},
                    {"name": "Día de Corte", "id": "dia_corte"},
                    {"name": "Días para Pago", "id": "dias_pago"},
                    {"name": "Límite", "id": "limite"},
                ],
                data=[],
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
            )
        ),
    ],
    className="shadow-sm",
)

# ── Layout completo de la pestaña ──────────────────────────────────────────────
layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(tarjeta_form, md=7, className="mb-4"),
                dbc.Col(perfil_form, md=5, className="mb-4"),
            ]
        ),
        dbc.Row(dbc.Col(tarjetas_card, className="mb-4")),
    ]
)

# ── Callbacks ──────────────────────────────────────────────────────────────────


@app.callback(
    Output("alert-cfg-tarjeta", "children"),
    Output("store-cfg-trigger", "data"),
    Output("cfg-banco", "value"),
    Output("cfg-alias", "value"),
    Output("cfg-terminacion", "value"),
    Output("cfg-dia-corte", "value"),
    Output("cfg-dias-pago", "value"),
    Output("cfg-limite", "value"),
    Input("btn-guardar-tarjeta", "n_clicks"),
    State("cfg-banco", "value"),
    State("cfg-alias", "value"),
    State("cfg-terminacion", "value"),
    State("cfg-dia-corte", "value"),
    State("cfg-dias-pago", "value"),
    State("cfg-limite", "value"),
    State("store-cfg-trigger", "data"),
    prevent_initial_call=True,
)
def guardar_tarjeta(
    n, banco, alias, terminacion, dia_corte, dias_pago, limite, refresh
):
    _no_clear = (no_update,) * 6

    if not all([banco, dia_corte, dias_pago]):
        return (
            dbc.Alert(
                "Banco, día de corte y días para pago son obligatorios.",
                color="warning",
                dismissable=True,
            ),
            refresh,
            *_no_clear,
        )

    session = SessionLocal()
    try:
        tarjeta = Tarjeta(
            banco=banco.strip(),
            nombre_alias=alias.strip() if alias else None,
            terminacion=terminacion.strip() if terminacion else None,
            dia_corte=int(dia_corte),
            dias_limite_pago=int(dias_pago),
            limite_credito=float(limite) if limite else None,
        )
        session.add(tarjeta)
        session.commit()

        return (
            dbc.Alert(
                f"Tarjeta '{tarjeta.banco}' guardada (ID {tarjeta.id}).",
                color="success",
                dismissable=True,
            ),
            (refresh or 0) + 1,
            "",  # cfg-banco
            "",  # cfg-alias
            "",  # cfg-terminacion
            None,  # cfg-dia-corte
            None,  # cfg-dias-pago
            None,  # cfg-limite
        )
    except Exception as e:
        session.rollback()
        print(f"[guardar_tarjeta] {e}")
        return (
            dbc.Alert(f"Error al guardar: {e}", color="danger", dismissable=True),
            refresh,
            *_no_clear,
        )
    finally:
        session.close()


@app.callback(
    Output("cfg-ingreso", "value"),
    Output("alert-cfg-perfil", "children"),
    Input("btn-guardar-perfil", "n_clicks"),
    Input("store-refresh", "data"),
    State("cfg-ingreso", "value"),
    prevent_initial_call=False,
)
def perfil_handler(n_clicks, _refresh, ingreso):
    from dash import ctx

    # Cargar valor guardado al inicializar o al refrescar
    if ctx.triggered_id != "btn-guardar-perfil":
        session = SessionLocal()
        try:
            perfil = session.query(PerfilFinanciero).first()
            return (perfil.ingreso_mensual if perfil else None), no_update
        except Exception as e:
            print(f"[load_perfil] {e}")
            return None, no_update
        finally:
            session.close()

    # Guardar cuando se presiona el botón
    if ingreso is None:
        return no_update, dbc.Alert(
            "Ingresa el ingreso mensual.", color="warning", dismissable=True
        )

    session = SessionLocal()
    try:
        perfil = session.query(PerfilFinanciero).first()
        if perfil:
            perfil.ingreso_mensual = float(ingreso)
        else:
            session.add(PerfilFinanciero(ingreso_mensual=float(ingreso)))
        session.commit()
        return float(ingreso), dbc.Alert(
            f"Perfil actualizado: ingreso mensual ${float(ingreso):,.2f}.",
            color="success",
            dismissable=True,
        )
    except Exception as e:
        session.rollback()
        print(f"[guardar_perfil] {e}")
        return no_update, dbc.Alert(
            f"Error al guardar: {e}", color="danger", dismissable=True
        )
    finally:
        session.close()


@app.callback(
    Output("tabla-tarjetas", "data"),
    Input("store-refresh", "data"),
)
def update_cards_table(_refresh):
    session = SessionLocal()
    try:
        tarjetas = session.query(Tarjeta).order_by(Tarjeta.banco).all()
        return [
            {
                "banco": t.banco,
                "alias": t.nombre_alias or "—",
                "terminacion": f"*{t.terminacion}" if t.terminacion else "—",
                "dia_corte": t.dia_corte,
                "dias_pago": t.dias_limite_pago,
                "limite": f"${t.limite_credito:,.2f}" if t.limite_credito else "—",
            }
            for t in tarjetas
        ]
    except Exception as e:
        print(f"[update_cards_table] {e}")
        return []
    finally:
        session.close()
