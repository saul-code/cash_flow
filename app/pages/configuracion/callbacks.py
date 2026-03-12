import dash_bootstrap_components as dbc
from dash import Input, Output, State, no_update

from app.dash_app import app
from app.db.models import PerfilFinanciero, Tarjeta
from app.db.session import SessionLocal


# ── Guardar tarjeta ────────────────────────────────────────────────────────────
@app.callback(
    Output("c-alert-tarjeta",  "children"),
    Output("store-cfg-trigger", "data"),
    Output("c-banco",          "value"),
    Output("c-alias",          "value"),
    Output("c-terminacion",    "value"),
    Output("c-dia-corte",      "value"),
    Output("c-dias-pago",      "value"),
    Output("c-limite",         "value"),
    Input("c-btn-tarjeta",     "n_clicks"),
    State("c-banco",           "value"),
    State("c-alias",           "value"),
    State("c-terminacion",     "value"),
    State("c-dia-corte",       "value"),
    State("c-dias-pago",       "value"),
    State("c-limite",          "value"),
    State("store-cfg-trigger", "data"),
    prevent_initial_call=True,
)
def c_guardar_tarjeta(_, banco, alias, terminacion, dia_corte, dias_pago, limite, refresh):
    _no_clear = (no_update,) * 6
    if not all([banco, dia_corte, dias_pago]):
        return (
            dbc.Alert("Banco, día de corte y días para pago son obligatorios.", color="warning", dismissable=True),
            refresh, *_no_clear,
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
            dbc.Alert(f"Tarjeta '{tarjeta.banco}' guardada (ID {tarjeta.id}).", color="success", dismissable=True),
            (refresh or 0) + 1,
            "", "", "", None, None, None,
        )
    except Exception as e:
        session.rollback()
        print(f"[c_guardar_tarjeta] {e}")
        return (dbc.Alert(f"Error: {e}", color="danger", dismissable=True), refresh, *_no_clear)
    finally:
        session.close()


# ── Perfil financiero ──────────────────────────────────────────────────────────
@app.callback(
    Output("c-ingreso",      "value"),
    Output("c-alert-perfil", "children"),
    Input("c-btn-perfil",    "n_clicks"),
    Input("store-refresh",   "data"),
    State("c-ingreso",       "value"),
    prevent_initial_call=False,
)
def c_perfil_handler(n_clicks, _refresh, ingreso):
    from dash import ctx
    if ctx.triggered_id != "c-btn-perfil":
        session = SessionLocal()
        try:
            perfil = session.query(PerfilFinanciero).first()
            return (perfil.ingreso_mensual if perfil else None), no_update
        except Exception as e:
            print(f"[c_load_perfil] {e}")
            return None, no_update
        finally:
            session.close()

    if ingreso is None:
        return no_update, dbc.Alert("Ingresa el ingreso mensual.", color="warning", dismissable=True)

    session = SessionLocal()
    try:
        perfil = session.query(PerfilFinanciero).first()
        if perfil:
            perfil.ingreso_mensual = float(ingreso)
        else:
            session.add(PerfilFinanciero(ingreso_mensual=float(ingreso)))
        session.commit()
        return float(ingreso), dbc.Alert(f"Perfil actualizado: ${float(ingreso):,.2f}/mes.", color="success", dismissable=True)
    except Exception as e:
        session.rollback()
        return no_update, dbc.Alert(f"Error: {e}", color="danger", dismissable=True)
    finally:
        session.close()


# ── Tabla tarjetas ─────────────────────────────────────────────────────────────
@app.callback(
    Output("c-tabla-tarjetas", "data"),
    Input("store-refresh",     "data"),
)
def c_update_tabla(_):
    session = SessionLocal()
    try:
        tarjetas = session.query(Tarjeta).order_by(Tarjeta.banco).all()
        return [
            {
                "banco":       t.banco,
                "alias":       t.nombre_alias or "—",
                "terminacion": f"*{t.terminacion}" if t.terminacion else "—",
                "dia_corte":   t.dia_corte,
                "dias_pago":   t.dias_limite_pago,
                "limite":      f"${t.limite_credito:,.2f}" if t.limite_credito else "—",
            }
            for t in tarjetas
        ]
    except Exception as e:
        print(f"[c_update_tabla] {e}")
        return []
    finally:
        session.close()
