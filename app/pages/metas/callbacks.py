import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, no_update

from app.dash_app import app
from app.db.models import MetaAhorro
from app.db.session import SessionLocal


def _render_meta(m: MetaAhorro):
    pct = min(m.monto_actual / m.monto_objetivo * 100, 100) if m.monto_objetivo > 0 else 0
    color = m.color or "#0099ff"
    return html.Div(
        [
            html.Div(
                [
                    html.Span(f"{m.emoji} {m.nombre}", className="cf-meta-name"),
                    html.Span(f"${m.monto_actual:,.2f} / ${m.monto_objetivo:,.2f}", className="cf-meta-vals"),
                ],
                className="cf-meta-row",
            ),
            html.Div(
                html.Div(
                    style={"width": f"{pct:.1f}%", "background": color, "height": "100%", "borderRadius": "3px"},
                ),
                className="cf-prog-bar",
            ),
            html.Div(
                [
                    html.Span(f"{pct:.0f}% completado", style={"fontSize": "11px", "color": "var(--cf-muted)"}),
                    html.Span(
                        f"Faltan ${max(m.monto_objetivo - m.monto_actual, 0):,.2f}",
                        style={"fontSize": "11px", "color": "var(--cf-muted)"},
                    ),
                ],
                style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"},
            ),
            # Update current amount + delete
            html.Div(
                [
                    dbc.Input(
                        id={"type": "m-inp-update", "index": m.id},
                        type="number",
                        placeholder="Actualizar monto actual...",
                        min=0, step=0.01,
                        style={"fontSize": "12px", "height": "28px", "flex": "1"},
                    ),
                    dbc.Button("✓", id={"type": "m-btn-update", "index": m.id}, color="primary",   size="sm", style={"padding": "2px 10px"}),
                    dbc.Button("✕", id={"type": "m-btn-delete", "index": m.id}, color="danger",    size="sm", style={"padding": "2px 10px"}),
                ],
                style={"display": "flex", "gap": "6px", "marginTop": "8px"},
            ),
        ],
        className="cf-meta-item",
    )


# ── List metas ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("m-lista-metas", "children"),
    Input("store-refresh",  "data"),
)
def m_list_metas(_):
    session = SessionLocal()
    try:
        metas = session.query(MetaAhorro).all()
        if not metas:
            return html.Div(
                [
                    html.Div("🎯", style={"fontSize": "32px", "marginBottom": "8px"}),
                    html.P("Sin metas todavía.", style={"color": "var(--cf-muted)", "fontSize": "13px"}),
                    html.P("Crea tu primera meta de ahorro.", style={"color": "var(--cf-muted)", "fontSize": "12px"}),
                ],
                style={"textAlign": "center", "padding": "32px 0"},
            )
        return [_render_meta(m) for m in metas]
    except Exception as e:
        print(f"[m_list_metas] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Add new meta ───────────────────────────────────────────────────────────────
@app.callback(
    Output("m-alert",              "children"),
    Output("store-refresh",        "data", allow_duplicate=True),
    Output("m-inp-nombre",         "value"),
    Output("m-inp-emoji",     "value"),
    Output("m-inp-objetivo",  "value"),
    Output("m-inp-actual",    "value"),
    Input("m-btn-guardar",    "n_clicks"),
    State("m-inp-nombre",     "value"),
    State("m-inp-emoji",      "value"),
    State("m-sel-color",      "value"),
    State("m-inp-objetivo",   "value"),
    State("m-inp-actual",     "value"),
    State("store-refresh",    "data"),
    prevent_initial_call=True,
)
def m_guardar(_, nombre, emoji, color, objetivo, actual, refresh):
    if not nombre or objetivo is None:
        return (
            dbc.Alert("Nombre y monto objetivo son requeridos.", color="warning", dismissable=True),
            no_update, no_update, no_update, no_update, no_update,
        )
    session = SessionLocal()
    try:
        meta = MetaAhorro(
            nombre=nombre.strip(),
            emoji=emoji.strip() if emoji else "🎯",
            color=color or "#0099ff",
            monto_objetivo=float(objetivo),
            monto_actual=float(actual) if actual else 0.0,
        )
        session.add(meta)
        session.commit()
        return (
            dbc.Alert(f"Meta '{meta.nombre}' creada.", color="success", dismissable=True),
            (refresh or 0) + 1,
            "", "🎯", None, None,
        )
    except Exception as e:
        session.rollback()
        print(f"[m_guardar] {e}")
        return (
            dbc.Alert(f"Error: {e}", color="danger", dismissable=True),
            no_update, no_update, no_update, no_update, no_update,
        )
    finally:
        session.close()


# ── Update meta amount ─────────────────────────────────────────────────────────
@app.callback(
    Output("store-refresh", "data", allow_duplicate=True),
    Input({"type": "m-btn-update", "index": "__match_all__"}, "n_clicks"),
    State({"type": "m-inp-update", "index": "__match_all__"}, "value"),
    State("store-refresh", "data"),
    prevent_initial_call=True,
)
def m_update_monto(n_clicks_list, values, refresh):
    from dash import ctx
    if not ctx.triggered_id:
        return no_update
    meta_id = ctx.triggered_id["index"]
    idx = next(
        (i for i, t in enumerate(ctx.inputs_list[0]) if t["id"]["index"] == meta_id),
        None,
    )
    if idx is None or values[idx] is None:
        return no_update
    session = SessionLocal()
    try:
        meta = session.get(MetaAhorro, meta_id)
        if meta:
            meta.monto_actual = float(values[idx])
            session.commit()
        return (refresh or 0) + 1
    except Exception as e:
        session.rollback()
        print(f"[m_update_monto] {e}")
        return no_update
    finally:
        session.close()


# ── Delete meta ────────────────────────────────────────────────────────────────
@app.callback(
    Output("store-refresh", "data", allow_duplicate=True),
    Input({"type": "m-btn-delete", "index": "__match_all__"}, "n_clicks"),
    State("store-refresh", "data"),
    prevent_initial_call=True,
)
def m_delete_meta(_, refresh):
    from dash import ctx
    if not ctx.triggered_id:
        return no_update
    meta_id = ctx.triggered_id["index"]
    session = SessionLocal()
    try:
        meta = session.get(MetaAhorro, meta_id)
        if meta:
            session.delete(meta)
            session.commit()
        return (refresh or 0) + 1
    except Exception as e:
        session.rollback()
        print(f"[m_delete_meta] {e}")
        return no_update
    finally:
        session.close()
