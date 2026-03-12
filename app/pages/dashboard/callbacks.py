from calendar import monthrange
from datetime import date, timedelta

import plotly.graph_objects as go
from dash import Input, Output, State, html, no_update
from sqlalchemy import func

from app.dash_app import app
from app.db.models import Categoria, MetaAhorro, Tarjeta, Transaccion
from app.db.session import SessionLocal

# ── Palette for categories ──────────────────────────────────────────────────────
_CAT_COLORS = {
    "Alimentos":       ("rgba(255,107,53,0.15)", "#fb923c"),
    "Transporte":      ("rgba(251,191,36,0.12)", "#fbbf24"),
    "Entretenimiento": ("rgba(0,229,160,0.12)",  "#00e5a0"),
    "Tecnología":      ("rgba(0,153,255,0.15)",  "#60a5fa"),
    "Suscripciones":   ("rgba(162,89,255,0.15)", "#c084fc"),
    "Ingreso":         ("rgba(0,229,160,0.12)",  "#00e5a0"),
    "Salud":           ("rgba(255,71,87,0.15)",  "#ff4757"),
    "Educación":       ("rgba(0,153,255,0.12)",  "#38bdf8"),
}
_DONUT_COLORS = ["#0099ff", "#00e5a0", "#ff6b35", "#a259ff", "#ff4757", "#fbbf24"]

_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#5a6580", family="DM Sans"),
    margin=dict(t=0, b=0, l=0, r=0),
)


def _cat_style(nombre: str):
    bg, color = _CAT_COLORS.get(nombre, ("rgba(255,255,255,0.08)", "#e8edf5"))
    return {"background": bg, "color": color}


def _render_table(rows, search: str = "", filter_type: str = "todas"):
    trs = []
    for r in rows:
        if search and search.lower() not in (r.descripcion or "").lower():
            continue
        if filter_type == "cargos" and r.tipo_movimiento != "cargo":
            continue
        if filter_type == "abonos" and r.tipo_movimiento != "abono":
            continue
        if filter_type == "msi" and not r.es_msi:
            continue

        sign = "−" if r.tipo_movimiento == "cargo" else "+"
        monto_cls = "cf-amount-cargo" if r.tipo_movimiento == "cargo" else "cf-amount-abono"
        cat_name = r.categoria.nombre if r.categoria else "—"
        tarjeta_str = r.tarjeta.banco + (f" •{r.tarjeta.terminacion}" if r.tarjeta.terminacion else "")

        trs.append(
            html.Tr(
                [
                    html.Td(r.fecha.strftime("%d %b"), className="cf-date-cell"),
                    html.Td(r.descripcion),
                    html.Td(f"{sign}${r.monto:,.2f}", className=monto_cls),
                    html.Td(
                        html.Span(
                            r.tipo_movimiento.capitalize(),
                            style={"color": "var(--cf-accent)" if r.tipo_movimiento == "abono" else "var(--cf-muted)", "fontSize": "12px"},
                        )
                    ),
                    html.Td(tarjeta_str, style={"fontSize": "12px"}),
                    html.Td(
                        html.Span(cat_name, className="cf-cat-badge", style=_cat_style(cat_name))
                        if cat_name != "—"
                        else html.Span("—", style={"color": "var(--cf-muted)", "fontSize": "11px"})
                    ),
                    html.Td(
                        html.Span(f"{r.plazo_msi} MSI", className="cf-msi-pill")
                        if r.es_msi and r.plazo_msi and r.plazo_msi > 1
                        else html.Span("—", style={"color": "var(--cf-muted)", "fontSize": "11px"})
                    ),
                ]
            )
        )
    return trs


# ── KPI cards ──────────────────────────────────────────────────────────────────
@app.callback(
    Output("d-kpi-saldo",     "children"),
    Output("d-kpi-saldo-sub", "children"),
    Output("d-kpi-gasto",     "children"),
    Output("d-kpi-gasto-sub", "children"),
    Output("d-kpi-pago",      "children"),
    Output("d-kpi-pago-sub",  "children"),
    Input("store-refresh", "data"),
)
def d_update_kpis(_):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    try:
        total_cargos = session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo_movimiento == "cargo").scalar() or 0.0
        total_abonos = session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo_movimiento == "abono").scalar() or 0.0
        saldo = total_abonos - total_cargos
        saldo_str = f"${saldo:,.0f}"
        saldo_sub = html.Span("balance acumulado (abonos − cargos)", style={"fontSize": "11px"})

        gasto_mes = session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.tipo_movimiento == "cargo",
            Transaccion.fecha >= mes_inicio,
        ).scalar() or 0.0
        gasto_str = f"${gasto_mes:,.0f}"
        gasto_sub = html.Span(f"cargos registrados en {hoy.strftime('%b %Y')}", style={"fontSize": "11px"})

        tarjetas = session.query(Tarjeta).all()
        fechas_pago = []
        proximo_tarjeta = None
        for t in tarjetas:
            try:
                if hoy.day <= t.dia_corte:
                    año, mes = hoy.year, hoy.month
                else:
                    mes = hoy.month + 1 if hoy.month < 12 else 1
                    año = hoy.year if hoy.month < 12 else hoy.year + 1
                dia_real = min(t.dia_corte, monthrange(año, mes)[1])
                fp = date(año, mes, dia_real) + timedelta(days=t.dias_limite_pago)
                fechas_pago.append((fp, t))
            except Exception:
                continue

        if fechas_pago:
            fp, pt = min(fechas_pago, key=lambda x: x[0])
            delta = (fp - hoy).days
            pago_str = f"${pt.limite_credito:,.0f}" if pt.limite_credito else "—"
            if delta < 0:
                pago_sub = html.Span(f"Vencido — {fp.strftime('%d %b %Y')}", style={"color": "var(--cf-danger)", "fontSize": "11px"})
            elif delta == 0:
                pago_sub = html.Span(f"{pt.banco} — Hoy", style={"color": "var(--cf-warn)", "fontSize": "11px"})
            else:
                pago_sub = html.Span(f"{pt.banco} •{pt.terminacion or '—'}  · {fp.strftime('%d %b %Y')} (en {delta}d)", style={"fontSize": "11px"})
        else:
            pago_str = "—"
            pago_sub = html.Span("Sin tarjetas registradas", style={"fontSize": "11px"})

        return saldo_str, saldo_sub, gasto_str, gasto_sub, pago_str, pago_sub
    except Exception as e:
        print(f"[d_update_kpis] {e}")
        return "—", "", "—", "", "—", ""
    finally:
        session.close()


# ── ¿Me alcanza? ───────────────────────────────────────────────────────────────
@app.callback(
    Output("d-alcanza-result", "children"),
    Output("d-alcanza-result", "className"),
    Input("d-btn-alcanza", "n_clicks"),
    State("d-alcanza-input", "value"),
    prevent_initial_call=True,
)
def d_check_alcanza(_, gasto_deseado):
    if gasto_deseado is None:
        return "Ingresa un monto primero.", "cf-alcanza-result"
    session = SessionLocal()
    try:
        total_abonos = session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo_movimiento == "abono").scalar() or 0.0
        total_cargos = session.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo_movimiento == "cargo").scalar() or 0.0
        saldo = total_abonos - total_cargos
        restante = saldo - float(gasto_deseado)
        if restante >= 0:
            return f"✓ Sí te alcanza — te quedan ${restante:,.2f}", "cf-alcanza-result ok"
        else:
            return f"✗ No te alcanza — te faltan ${abs(restante):,.2f}", "cf-alcanza-result no"
    except Exception as e:
        return f"Error: {e}", "cf-alcanza-result"
    finally:
        session.close()


# ── Flujo period chips ─────────────────────────────────────────────────────────
@app.callback(
    Output("d-flujo-period",  "data"),
    Output("d-chip-semana",   "className"),
    Output("d-chip-mes",      "className"),
    Output("d-chip-3m",       "className"),
    Input("d-chip-semana",    "n_clicks"),
    Input("d-chip-mes",       "n_clicks"),
    Input("d-chip-3m",        "n_clicks"),
    prevent_initial_call=True,
)
def d_switch_period(n_s, n_m, n_3):
    from dash import ctx
    tid = ctx.triggered_id
    mapping = {"d-chip-semana": "semana", "d-chip-mes": "mes", "d-chip-3m": "3m"}
    active = mapping.get(tid, "semana")
    cls = {k: "cf-chip active" if v == active else "cf-chip" for k, v in mapping.items()}
    return active, cls["d-chip-semana"], cls["d-chip-mes"], cls["d-chip-3m"]


# ── Flujo chart ────────────────────────────────────────────────────────────────
@app.callback(
    Output("d-chart-flujo", "figure"),
    Input("store-refresh",   "data"),
    Input("d-flujo-period",  "data"),
)
def d_update_flujo(_, period):
    session = SessionLocal()
    hoy = date.today()
    if period == "3m":
        dias = 90
    elif period == "mes":
        dias = hoy.day
    else:
        dias = 7
    desde = hoy - timedelta(days=dias - 1)

    try:
        rows = (
            session.query(Transaccion.fecha, Transaccion.tipo_movimiento, Transaccion.monto)
            .filter(Transaccion.fecha >= desde)
            .all()
        )
        fechas_set = [desde + timedelta(days=i) for i in range(dias)]
        ingresos = {f: 0.0 for f in fechas_set}
        egresos  = {f: 0.0 for f in fechas_set}
        for fecha, tipo, monto in rows:
            if fecha in ingresos:
                if tipo == "abono":
                    ingresos[fecha] += monto
                else:
                    egresos[fecha] += monto

        x = [d.strftime("%d %b") for d in fechas_set]
        y_ing = [ingresos[d] for d in fechas_set]
        y_eg  = [egresos[d]  for d in fechas_set]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y_ing, name="Ingresos",
            line=dict(color="#00e5a0", width=2),
            fill="tozeroy",
            fillcolor="rgba(0,229,160,0.1)",
            mode="lines",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=y_eg, name="Egresos",
            line=dict(color="#ff4757", width=2),
            fill="tozeroy",
            fillcolor="rgba(255,71,87,0.08)",
            mode="lines",
        ))
        fig.update_layout(
            **_DARK,
            showlegend=False,
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#5a6580"), tickmode="auto", nticks=7),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=9, color="#5a6580"), tickprefix="$"),
            hovermode="x unified",
        )
        return fig
    except Exception as e:
        print(f"[d_update_flujo] {e}")
        return go.Figure(layout=_DARK)
    finally:
        session.close()


# ── Donut + legend ─────────────────────────────────────────────────────────────
@app.callback(
    Output("d-chart-donut",      "figure"),
    Output("d-categoria-legend", "children"),
    Input("store-refresh", "data"),
)
def d_update_donut(_):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    try:
        gastos_cat = (
            session.query(Categoria.nombre, func.sum(Transaccion.monto).label("total"))
            .join(Transaccion, Transaccion.categoria_id == Categoria.id)
            .filter(Transaccion.tipo_movimiento == "cargo", Transaccion.fecha >= mes_inicio)
            .group_by(Categoria.nombre)
            .all()
        )
        if not gastos_cat:
            fig = go.Figure(go.Pie(values=[1], labels=["Sin datos"], hole=0.6,
                                   marker_colors=["rgba(255,255,255,0.05)"]))
            fig.update_traces(textinfo="none", hoverinfo="none")
            fig.update_layout(**_DARK, showlegend=False)
            return fig, html.P("Sin gastos este mes.", style={"color": "var(--cf-muted)", "fontSize": "12px"})

        nombres = [r.nombre for r in gastos_cat]
        valores = [r.total for r in gastos_cat]
        total   = sum(valores)
        colors  = _DONUT_COLORS[: len(nombres)]

        fig = go.Figure(go.Pie(
            values=valores, labels=nombres, hole=0.65,
            marker_colors=colors,
        ))
        fig.update_traces(
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
        )
        fig.update_layout(**_DARK, showlegend=False)
        fig.add_annotation(
            text=f"${total:,.0f}", x=0.5, y=0.5, showarrow=False,
            font=dict(size=11, color="#e8edf5", family="Space Mono"),
        )

        legend = html.Div(
            [
                html.Div(
                    [
                        html.Span(style={"width": "8px", "height": "8px", "borderRadius": "50%", "background": colors[i], "display": "inline-block", "marginRight": "6px"}),
                        html.Span(n, style={"fontSize": "12px"}),
                        html.Span(
                            f"  ${v:,.0f}  ",
                            style={"fontFamily": "'Space Mono', monospace", "fontSize": "12px", "marginLeft": "auto"},
                        ),
                        html.Span(
                            f"{v/total*100:.0f}%",
                            style={"color": "var(--cf-muted)", "fontSize": "10px"},
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                )
                for i, (n, v) in enumerate(zip(nombres, valores))
            ]
        )
        return fig, legend
    except Exception as e:
        print(f"[d_update_donut] {e}")
        return go.Figure(layout=_DARK), html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Tarjetas list ──────────────────────────────────────────────────────────────
@app.callback(
    Output("d-tarjetas-list", "children"),
    Input("store-refresh", "data"),
)
def d_update_tarjetas(_):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    try:
        tarjetas = session.query(Tarjeta).order_by(Tarjeta.banco).all()
        if not tarjetas:
            return html.P("Sin tarjetas. Agrega una en Configuración.", style={"color": "var(--cf-muted)", "fontSize": "12px"})
        items = []
        for t in tarjetas:
            gasto = session.query(func.sum(Transaccion.monto)).filter(
                Transaccion.tarjeta_id == t.id,
                Transaccion.tipo_movimiento == "cargo",
                Transaccion.fecha >= mes_inicio,
            ).scalar() or 0.0

            banco_lower = (t.banco or "").lower()
            if "visa" in banco_lower or "banamex" in banco_lower or "hsbc" in banco_lower:
                chip_cls = "cf-card-chip visa"
                chip_txt = "VISA"
            elif "bbva" in banco_lower or "master" in banco_lower or "santander" in banco_lower:
                chip_cls = "cf-card-chip mc"
                chip_txt = "MC"
            elif "amex" in banco_lower or "american" in banco_lower:
                chip_cls = "cf-card-chip amex"
                chip_txt = "AMEX"
            else:
                chip_cls = "cf-card-chip default"
                chip_txt = (t.banco or "?")[:3].upper()

            if t.limite_credito and t.limite_credito > 0:
                pct = min(gasto / t.limite_credito * 100, 100)
                bar_color = "var(--cf-accent)" if pct < 60 else "var(--cf-warn)" if pct < 85 else "var(--cf-danger)"
                limit_txt = f"${gasto:,.0f}/${t.limite_credito:,.0f}"
                right = html.Div(
                    [
                        html.Div(limit_txt, className="cf-tarjeta-limit-text"),
                        html.Div(html.Div(style={"width": f"{pct:.0f}%", "background": bar_color, "height": "100%", "borderRadius": "2px"}), className="cf-limit-bar"),
                    ],
                    className="cf-tarjeta-right",
                )
            else:
                right = html.Div(html.Div("Sin límite", style={"fontSize": "11px", "color": "var(--cf-muted)"}), className="cf-tarjeta-right")

            items.append(
                html.Div(
                    [
                        html.Div(chip_txt, className=chip_cls),
                        html.Div(
                            [
                                html.Div(t.nombre_alias or t.banco, className="cf-tarjeta-name"),
                                html.Div(f"•••• {t.terminacion}" if t.terminacion else t.banco, className="cf-tarjeta-num"),
                            ],
                            className="cf-tarjeta-info",
                        ),
                        right,
                    ],
                    className="cf-tarjeta-item",
                )
            )
        return items
    except Exception as e:
        print(f"[d_update_tarjetas] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Próximos pagos ─────────────────────────────────────────────────────────────
@app.callback(
    Output("d-pagos-list", "children"),
    Input("store-refresh", "data"),
)
def d_update_pagos(_):
    session = SessionLocal()
    hoy = date.today()
    try:
        tarjetas = session.query(Tarjeta).all()
        pagos = []
        for t in tarjetas:
            try:
                if hoy.day <= t.dia_corte:
                    año, mes = hoy.year, hoy.month
                else:
                    mes = hoy.month + 1 if hoy.month < 12 else 1
                    año = hoy.year if hoy.month < 12 else hoy.year + 1
                dia_real = min(t.dia_corte, monthrange(año, mes)[1])
                fp = date(año, mes, dia_real) + timedelta(days=t.dias_limite_pago)
                delta = (fp - hoy).days
                gasto = session.query(func.sum(Transaccion.monto)).filter(
                    Transaccion.tarjeta_id == t.id,
                    Transaccion.tipo_movimiento == "cargo",
                    Transaccion.fecha >= hoy.replace(day=1),
                ).scalar() or 0.0
                pagos.append((fp, delta, t, gasto))
            except Exception:
                continue

        if not pagos:
            return html.P("Sin tarjetas registradas.", style={"color": "var(--cf-muted)", "fontSize": "12px"})

        pagos.sort(key=lambda x: x[0])
        items = []
        for fp, delta, t, gasto in pagos[:4]:
            if delta < 0:
                dot_color = "var(--cf-danger)"
                date_txt  = f"{fp.strftime('%d %b %Y')} · vencido"
                monto_color = "var(--cf-danger)"
            elif delta <= 7:
                dot_color = "var(--cf-danger)"
                date_txt  = f"{fp.strftime('%d %b %Y')} · en {delta}d"
                monto_color = "var(--cf-danger)"
            elif delta <= 15:
                dot_color = "var(--cf-warn)"
                date_txt  = f"{fp.strftime('%d %b %Y')} · en {delta}d"
                monto_color = "var(--cf-warn)"
            else:
                dot_color = "var(--cf-accent)"
                date_txt  = f"{fp.strftime('%d %b %Y')} · en {delta}d"
                monto_color = "var(--cf-muted)"

            items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(style={"background": dot_color}, className="cf-pago-dot"),
                                html.Div(
                                    [
                                        html.Div(t.nombre_alias or t.banco, className="cf-pago-name"),
                                        html.Div(date_txt, className="cf-pago-date"),
                                    ]
                                ),
                            ],
                            className="cf-pago-left",
                        ),
                        html.Div(f"${gasto:,.0f}", className="cf-pago-monto", style={"color": monto_color}),
                    ],
                    className="cf-pago-item",
                )
            )
        return items
    except Exception as e:
        print(f"[d_update_pagos] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Metas de ahorro ────────────────────────────────────────────────────────────
@app.callback(
    Output("d-metas-list", "children"),
    Input("store-refresh", "data"),
)
def d_update_metas(_):
    session = SessionLocal()
    try:
        metas = session.query(MetaAhorro).all()
        if not metas:
            return html.P("Sin metas. Créalas en la pestaña Metas.", style={"color": "var(--cf-muted)", "fontSize": "12px"})
        items = []
        for m in metas:
            pct = min(m.monto_actual / m.monto_objetivo * 100, 100) if m.monto_objetivo > 0 else 0
            items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(f"{m.emoji} {m.nombre}", className="cf-meta-name"),
                                html.Span(f"${m.monto_actual:,.0f} / ${m.monto_objetivo:,.0f}", className="cf-meta-vals"),
                            ],
                            className="cf-meta-row",
                        ),
                        html.Div(
                            html.Div(style={"width": f"{pct:.0f}%", "background": m.color or "var(--cf-accent2)"}, className="cf-prog-fill"),
                            className="cf-prog-bar",
                        ),
                    ]
                )
            )
        return items
    except Exception as e:
        print(f"[d_update_metas] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Proyección ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("d-proyeccion", "children"),
    Input("store-refresh", "data"),
)
def d_update_proyeccion(_):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    dias_mes = monthrange(hoy.year, hoy.month)[1]
    dias_transcurridos = max(hoy.day, 1)
    try:
        from app.db.models import PerfilFinanciero
        gasto_mes = session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.tipo_movimiento == "cargo",
            Transaccion.fecha >= mes_inicio,
        ).scalar() or 0.0

        perfil = session.query(PerfilFinanciero).first()
        ingreso = perfil.ingreso_mensual if perfil else 0.0

        tasa_diaria = gasto_mes / dias_transcurridos
        proyectado = tasa_diaria * dias_mes

        if ingreso > 0:
            limite = ingreso * 0.80
            diferencia = limite - proyectado
            if diferencia >= 0:
                estado_txt = f"Al fin de mes gastarás ≈ ${proyectado:,.0f}"
                estado_sub = f"de tu ingreso ${ingreso:,.0f} — vas bien ✓"
                estado_style = {"background": "rgba(0,229,160,0.08)", "border": "1px solid rgba(0,229,160,0.2)", "color": "var(--cf-accent)"}
            else:
                estado_txt = f"Al fin de mes gastarás ≈ ${proyectado:,.0f}"
                estado_sub = f"superas el 80% de tu ingreso (${limite:,.0f})"
                estado_style = {"background": "rgba(255,107,53,0.08)", "border": "1px solid rgba(255,107,53,0.2)", "color": "var(--cf-warn)"}
        else:
            estado_txt = f"Proyección mensual: ${proyectado:,.0f}"
            estado_sub = "Configura tu ingreso para más detalles"
            estado_style = {"background": "var(--cf-surface2)", "border": "1px solid var(--cf-border)", "color": "var(--cf-text)"}

        ahorro_posible = ingreso - proyectado if ingreso > 0 else 0
        tip_txt = f"💡 A este ritmo ahorrarás ${max(ahorro_posible, 0):,.0f} este mes." if ingreso > 0 else "💡 Agrega tu ingreso mensual en Configuración."

        return [
            html.Div(
                [
                    html.Div(estado_txt, style={"fontFamily": "'Space Mono', monospace", "fontSize": "16px", "marginBottom": "2px"}),
                    html.Div(estado_sub, style={"fontSize": "11px", "color": "var(--cf-muted)"}),
                ],
                style={**estado_style, "padding": "12px 14px", "borderRadius": "10px", "marginBottom": "10px"},
            ),
            html.Div(
                tip_txt,
                style={"padding": "10px 14px", "background": "var(--cf-surface2)", "border": "1px solid var(--cf-border)", "borderRadius": "10px", "fontSize": "12px", "color": "var(--cf-muted)"},
            ),
        ]
    except Exception as e:
        print(f"[d_update_proyeccion] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)"})
    finally:
        session.close()


# ── Filter chips ───────────────────────────────────────────────────────────────
@app.callback(
    Output("d-tabla-filter",  "data"),
    Output("d-chip-todas",    "className"),
    Output("d-chip-cargos",   "className"),
    Output("d-chip-abonos",   "className"),
    Output("d-chip-msi-f",    "className"),
    Input("d-chip-todas",     "n_clicks"),
    Input("d-chip-cargos",    "n_clicks"),
    Input("d-chip-abonos",    "n_clicks"),
    Input("d-chip-msi-f",     "n_clicks"),
    prevent_initial_call=True,
)
def d_switch_filter(*_):
    from dash import ctx
    mapping = {
        "d-chip-todas":  "todas",
        "d-chip-cargos": "cargos",
        "d-chip-abonos": "abonos",
        "d-chip-msi-f":  "msi",
    }
    active = mapping.get(ctx.triggered_id, "todas")
    cls = {k: "cf-chip active" if v == active else "cf-chip" for k, v in mapping.items()}
    return active, cls["d-chip-todas"], cls["d-chip-cargos"], cls["d-chip-abonos"], cls["d-chip-msi-f"]


# ── Transactions table ─────────────────────────────────────────────────────────
@app.callback(
    Output("d-tabla-body", "children"),
    Input("store-refresh",    "data"),
    Input("d-search",         "value"),
    Input("d-tabla-filter",   "data"),
)
def d_update_tabla(_, search, filter_type):
    session = SessionLocal()
    search = search or ""
    filter_type = filter_type or "todas"
    try:
        rows = (
            session.query(Transaccion)
            .order_by(Transaccion.fecha.desc(), Transaccion.id.desc())
            .limit(50)
            .all()
        )
        trs = _render_table(rows, search, filter_type)
        if not trs:
            return html.Div(
                "Sin transacciones que coincidan.",
                style={"padding": "24px", "textAlign": "center", "color": "var(--cf-muted)", "fontSize": "13px"},
            )
        return html.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Fecha"), html.Th("Descripción"), html.Th("Monto"),
                    html.Th("Tipo"), html.Th("Tarjeta"), html.Th("Categoría"), html.Th("MSI"),
                ])),
                html.Tbody(trs),
            ],
            className="cf-table",
        )
    except Exception as e:
        print(f"[d_update_tabla] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)", "padding": "16px"})
    finally:
        session.close()
