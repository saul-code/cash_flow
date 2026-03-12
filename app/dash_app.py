import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    assets_folder="assets",  # Por defecto es 'assets', pero asegúrate de no haberlo cambiado
    title="CF//FLOW",
    suppress_callback_exceptions=True,
)
server = app.server
