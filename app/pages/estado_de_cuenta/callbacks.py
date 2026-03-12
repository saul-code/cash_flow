from datetime import date

from dash import Input, Output, html
from sqlalchemy import func

from app.dash_app import app
from app.db.models import Categoria, Transaccion
from app.db.session import SessionLocal

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


def _cat_style(nombre: str):
    bg, color = _CAT_COLORS.get(nombre, ("rgba(255,255,255,0.08)", "#e8edf5"))
    return {"background": bg, "color": color}


# ── Filter chips ───────────────────────────────────────────────────────────────
@app.callback(
    Output("ec-filter-tipo",  "data"),
    Output("ec-chip-todas",   "className"),
    Output("ec-chip-cargos",  "className"),
    Output("ec-chip-abonos",  "className"),
    Output("ec-chip-msi",     "className"),
    Input("ec-chip-todas",    "n_clicks"),
    Input("ec-chip-cargos",   "n_clicks"),
    Input("ec-chip-abonos",   "n_clicks"),
    Input("ec-chip-msi",      "n_clicks"),
    prevent_initial_call=True,
)
def ec_switch_filter(*_):
    from dash import ctx
    mapping = {
        "ec-chip-todas":  "todas",
        "ec-chip-cargos": "cargos",
        "ec-chip-abonos": "abonos",
        "ec-chip-msi":    "msi",
    }
    active = mapping.get(ctx.triggered_id, "todas")
    cls = {k: "cf-chip active" if v == active else "cf-chip" for k, v in mapping.items()}
    return active, cls["ec-chip-todas"], cls["ec-chip-cargos"], cls["ec-chip-abonos"], cls["ec-chip-msi"]


# ── Table + resumen ────────────────────────────────────────────────────────────
@app.callback(
    Output("ec-tabla-body", "children"),
    Output("ec-resumen",    "children"),
    Input("store-refresh",   "data"),
    Input("ec-search",       "value"),
    Input("ec-filter-tipo",  "data"),
    Input("ec-sel-mes",      "value"),
    Input("ec-sel-year",     "value"),
)
def ec_update_tabla(_, search, filter_tipo, mes, year):
    session = SessionLocal()
    search = (search or "").lower()
    filter_tipo = filter_tipo or "todas"
    try:
        mes_i = int(mes or date.today().month)
        year_i = int(year or date.today().year)
        from calendar import monthrange
        last_day = monthrange(year_i, mes_i)[1]
        desde = date(year_i, mes_i, 1)
        hasta = date(year_i, mes_i, last_day)

        query = session.query(Transaccion).filter(
            Transaccion.fecha >= desde,
            Transaccion.fecha <= hasta,
        )
        if filter_tipo == "cargos":
            query = query.filter(Transaccion.tipo_movimiento == "cargo")
        elif filter_tipo == "abonos":
            query = query.filter(Transaccion.tipo_movimiento == "abono")
        elif filter_tipo == "msi":
            query = query.filter(Transaccion.es_msi == True)

        rows = query.order_by(Transaccion.fecha.desc(), Transaccion.id.desc()).all()

        if search:
            rows = [r for r in rows if search in (r.descripcion or "").lower()]

        # Resumen chips
        total_cargos = sum(r.monto for r in rows if r.tipo_movimiento == "cargo")
        total_abonos = sum(r.monto for r in rows if r.tipo_movimiento == "abono")
        resumen = [
            html.Span(f"Cargos: ${total_cargos:,.0f}", style={"fontFamily": "'Space Mono',monospace", "fontSize": "12px", "color": "var(--cf-danger)"}),
            html.Span(f"Abonos: ${total_abonos:,.0f}", style={"fontFamily": "'Space Mono',monospace", "fontSize": "12px", "color": "var(--cf-accent)"}),
            html.Span(f"{len(rows)} transacciones", style={"fontSize": "11px", "color": "var(--cf-muted)"}),
        ]

        if not rows:
            tabla = html.Div(
                "Sin transacciones en el período seleccionado.",
                style={"padding": "32px", "textAlign": "center", "color": "var(--cf-muted)", "fontSize": "13px"},
            )
            return tabla, resumen

        trs = []
        for r in rows:
            sign = "−" if r.tipo_movimiento == "cargo" else "+"
            monto_cls = "cf-amount-cargo" if r.tipo_movimiento == "cargo" else "cf-amount-abono"
            cat_name = r.categoria.nombre if r.categoria else "—"
            tarjeta_str = r.tarjeta.banco + (f" •{r.tarjeta.terminacion}" if r.tarjeta.terminacion else "")
            trs.append(
                html.Tr([
                    html.Td(r.fecha.strftime("%d %b %Y"), className="cf-date-cell"),
                    html.Td(r.descripcion),
                    html.Td(f"{sign}${r.monto:,.2f}", className=monto_cls),
                    html.Td(html.Span(
                        r.tipo_movimiento.capitalize(),
                        style={"color": "var(--cf-accent)" if r.tipo_movimiento == "abono" else "var(--cf-muted)", "fontSize": "12px"},
                    )),
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
                ])
            )

        tabla = html.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Fecha"), html.Th("Descripción"), html.Th("Monto"),
                    html.Th("Tipo"), html.Th("Tarjeta"), html.Th("Categoría"), html.Th("MSI"),
                ])),
                html.Tbody(trs),
            ],
            className="cf-table",
        )
        return tabla, resumen
    except Exception as e:
        print(f"[ec_update_tabla] {e}")
        return html.P(f"Error: {e}", style={"color": "var(--cf-danger)", "padding": "16px"}), []
    finally:
        session.close()
