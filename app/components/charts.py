from calendar import monthrange
from datetime import date, timedelta

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from sqlalchemy import func

from app.dash_app import app
from app.db.models import Categoria, Tarjeta, Transaccion
from app.db.session import SessionLocal


# ── Helpers ────────────────────────────────────────────────────────────────────
def _kpi_card(title: str, value_id: str, subtitle: str, color: str = "primary"):
    return dbc.Card(
        dbc.CardBody(
            [
                html.P(
                    title,
                    className="text-muted text-uppercase fw-semibold mb-1",
                    style={"fontSize": "0.75rem", "letterSpacing": "0.05em"},
                ),
                html.H3(
                    "—",
                    id=value_id,
                    className=f"fw-bold text-{color} mb-1",
                ),
                html.P(subtitle, className="text-muted mb-0", style={"fontSize": "0.8rem"}),
            ]
        ),
        className="shadow-sm h-100",
    )


# ── Layout ─────────────────────────────────────────────────────────────────────
kpi_row = dbc.Row(
    [
        dbc.Col(
            _kpi_card("Saldo Actual", "kpi-saldo", "balance acumulado (abonos − cargos)", "primary"),
            md=4,
            className="mb-4",
        ),
        dbc.Col(
            _kpi_card("Gasto del Mes", "kpi-gasto", "total de cargos en el mes", "danger"),
            md=4,
            className="mb-4",
        ),
        dbc.Col(
            _kpi_card("Próximo Pago", "kpi-pago", "fecha límite más cercana", "warning"),
            md=4,
            className="mb-4",
        ),
    ],
    className="mt-3",
)

charts_layout = dbc.Card(
    [
        dbc.CardHeader(html.H5("Resumen del Mes", className="mb-0")),
        dbc.CardBody(
            [
                dcc.Graph(
                    id="chart-pie",
                    config={"displayModeBar": False},
                    style={"height": "320px"},
                ),
                html.Hr(),
                html.H6("Uso de crédito — tarjeta seleccionada", className="mb-2"),
                html.Div(id="div-progress"),
            ]
        ),
    ],
    className="shadow-sm h-100",
)

# ── Callbacks ──────────────────────────────────────────────────────────────────


@app.callback(
    Output("kpi-saldo", "children"),
    Output("kpi-gasto", "children"),
    Output("kpi-pago", "children"),
    Input("store-refresh", "data"),
)
def update_kpis(_refresh):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    try:
        total_cargos = (
            session.query(func.sum(Transaccion.monto))
            .filter(Transaccion.tipo_movimiento == "cargo")
            .scalar() or 0.0
        )
        total_abonos = (
            session.query(func.sum(Transaccion.monto))
            .filter(Transaccion.tipo_movimiento == "abono")
            .scalar() or 0.0
        )
        saldo_str = f"${total_abonos - total_cargos:,.2f}"

        gasto_mes = (
            session.query(func.sum(Transaccion.monto))
            .filter(
                Transaccion.tipo_movimiento == "cargo",
                Transaccion.fecha >= mes_inicio,
            )
            .scalar() or 0.0
        )
        gasto_str = f"${gasto_mes:,.2f}"

        # Próximo pago: fecha límite más cercana entre todas las tarjetas
        tarjetas = session.query(Tarjeta).all()
        fechas_pago = []
        for t in tarjetas:
            try:
                if hoy.day <= t.dia_corte:
                    año, mes = hoy.year, hoy.month
                else:
                    mes = hoy.month + 1 if hoy.month < 12 else 1
                    año = hoy.year if hoy.month < 12 else hoy.year + 1
                dia_real = min(t.dia_corte, monthrange(año, mes)[1])
                fecha_pago = date(año, mes, dia_real) + timedelta(days=t.dias_limite_pago)
                fechas_pago.append(fecha_pago)
            except Exception:
                continue

        if fechas_pago:
            proximo = min(fechas_pago)
            delta = (proximo - hoy).days
            if delta < 0:
                pago_str = f"Vencido ({proximo.strftime('%d/%m/%Y')})"
            elif delta == 0:
                pago_str = f"Hoy — {proximo.strftime('%d/%m/%Y')}"
            else:
                pago_str = f"{proximo.strftime('%d/%m/%Y')} (en {delta}d)"
        else:
            pago_str = "Sin tarjetas"

        return saldo_str, gasto_str, pago_str

    except Exception as e:
        print(f"[update_kpis] {e}")
        return "—", "—", "—"
    finally:
        session.close()


@app.callback(
    Output("chart-pie", "figure"),
    Output("div-progress", "children"),
    Input("store-refresh", "data"),
    Input("dd-tarjeta", "value"),
)
def update_charts(_refresh, tarjeta_id):
    session = SessionLocal()
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    try:
        # Pie chart: gastos por categoría del mes
        gastos_cat = (
            session.query(Categoria.nombre, func.sum(Transaccion.monto).label("total"))
            .join(Transaccion, Transaccion.categoria_id == Categoria.id)
            .filter(
                Transaccion.tipo_movimiento == "cargo",
                Transaccion.fecha >= mes_inicio,
            )
            .group_by(Categoria.nombre)
            .all()
        )

        if gastos_cat:
            df = pd.DataFrame(gastos_cat, columns=["Categoría", "Monto"])
            fig = px.pie(
                df,
                values="Monto",
                names="Categoría",
                title=f"Gastos · {hoy.strftime('%B %Y')}",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(margin=dict(t=40, b=10, l=10, r=10))
        else:
            fig = go.Figure()
            fig.update_layout(
                title=f"Sin gastos registrados · {hoy.strftime('%B %Y')}",
                annotations=[
                    {
                        "text": "Sin datos",
                        "showarrow": False,
                        "font": {"size": 14},
                        "x": 0.5,
                        "y": 0.5,
                    }
                ],
                margin=dict(t=40, b=10, l=10, r=10),
            )

        # Progress bar: uso de crédito de la tarjeta seleccionada
        if tarjeta_id:
            tarjeta = session.get(Tarjeta, int(tarjeta_id))
            if tarjeta and tarjeta.limite_credito:
                total_mes = (
                    session.query(func.sum(Transaccion.monto))
                    .filter(
                        Transaccion.tarjeta_id == int(tarjeta_id),
                        Transaccion.tipo_movimiento == "cargo",
                        Transaccion.fecha >= mes_inicio,
                    )
                    .scalar()
                    or 0.0
                )
                pct = min(round(total_mes / tarjeta.limite_credito * 100, 1), 100)
                color = "success" if pct < 60 else "warning" if pct < 85 else "danger"
                progress = [
                    html.P(
                        f"${total_mes:,.2f} de ${tarjeta.limite_credito:,.2f} ({pct}%)",
                        className="mb-1 small fw-semibold",
                    ),
                    dbc.Progress(
                        value=pct,
                        color=color,
                        striped=(pct >= 85),
                        animated=(pct >= 85),
                        style={"height": "18px"},
                    ),
                ]
            else:
                progress = html.P(
                    "Esta tarjeta no tiene límite de crédito registrado.",
                    className="text-muted small",
                )
        else:
            progress = html.P(
                "Selecciona una tarjeta para ver el uso de crédito.",
                className="text-muted small",
            )

        return fig, progress

    except Exception as e:
        print(f"[update_charts] {e}")
        return go.Figure(), dbc.Alert(f"Error: {e}", color="danger")
    finally:
        session.close()
