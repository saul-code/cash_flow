from datetime import date

import dash_bootstrap_components as dbc
from dash import Input, Output, State, no_update
from dateutil.relativedelta import relativedelta

from app.dash_app import app
from app.db.models import Categoria, ParcialidadMSI, Tarjeta, Transaccion
from app.db.session import SessionLocal


@app.callback(
    Output("r-dd-tarjeta",  "options"),
    Output("r-dd-categoria", "options"),
    Input("url",             "pathname"),
    Input("store-refresh",   "data"),
)
def r_load_options(_pathname, _refresh):
    session = SessionLocal()
    try:
        tarjetas   = session.query(Tarjeta).order_by(Tarjeta.banco).all()
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
        print(f"[r_load_options] {e}")
        return [], []
    finally:
        session.close()


@app.callback(
    Output("r-collapse-msi", "is_open"),
    Input("r-sw-msi", "value"),
)
def r_toggle_msi(sw):
    return bool(sw)


@app.callback(
    Output("r-alert-guardar",  "children"),
    Output("store-tx-trigger", "data"),
    Output("r-inp-fecha",      "value"),
    Output("r-inp-monto",      "value"),
    Output("r-inp-desc",       "value"),
    Output("r-dd-tarjeta",     "value"),
    Output("r-dd-categoria",   "value"),
    Output("r-dd-tipo",        "value"),
    Output("r-sw-msi",         "value"),
    Output("r-inp-meses",      "value"),
    Input("r-btn-guardar",     "n_clicks"),
    State("r-inp-fecha",       "value"),
    State("r-inp-monto",       "value"),
    State("r-inp-desc",        "value"),
    State("r-dd-tarjeta",      "value"),
    State("r-dd-categoria",    "value"),
    State("r-dd-tipo",         "value"),
    State("r-sw-msi",          "value"),
    State("r-inp-meses",       "value"),
    State("store-tx-trigger",  "data"),
    prevent_initial_call=True,
)
def r_guardar(n_clicks, fecha, monto, desc, tarjeta_id, cat_id, tipo, es_msi, meses, refresh):
    _no_clear = (no_update,) * 8

    if not all([fecha, monto is not None, desc, tarjeta_id, tipo]):
        return (
            dbc.Alert("Completa los campos obligatorios: fecha, monto, descripción, tarjeta y tipo.", color="warning", dismissable=True),
            refresh, *_no_clear,
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
                session.add(ParcialidadMSI(
                    transaccion_id=tx.id,
                    numero_pago=num,
                    monto_parcialidad=monto_parcialidad,
                    mes_cobro=mes_cobro,
                ))

        session.commit()
        msg = f"Transacción guardada (ID {tx.id})."
        if es_msi and plazo > 1:
            monto_parc = round(float(monto) / plazo, 2)
            msg += f" {plazo} parcialidades MSI de ${monto_parc:,.2f} c/u."

        return (
            dbc.Alert(msg, color="success", dismissable=True),
            (refresh or 0) + 1,
            str(date.today()), None, "", None, None, "cargo", False, 3,
        )
    except Exception as e:
        session.rollback()
        print(f"[r_guardar] {e}")
        return (
            dbc.Alert(f"Error al guardar: {e}", color="danger", dismissable=True),
            refresh, *_no_clear,
        )
    finally:
        session.close()
