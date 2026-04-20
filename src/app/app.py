"""
CdE Macroeconomic Dashboard
Modular Shiny application with error-resilient data loading.
"""

import logging
from pathlib import Path

from shiny import App, ui

from data import load_data_store, get_last_update_time
from styles import CUSTOM_CSS
from pages import activity, prices

# Static assets directory
WWW_DIR = Path(__file__).parent / "www"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load data with error isolation
# ---------------------------------------------------------------------------
logger.info("Loading data store...")
data_store = load_data_store()

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
app_ui = ui.page_navbar(
    # Custom CSS injection
    ui.head_content(ui.HTML(CUSTOM_CSS)),

    # Tabs
    activity.page_ui(data_store),
    prices.page_ui(data_store),

    # Spacer pushes logo to the right
    ui.nav_spacer(),

    # Logo on the right
    ui.nav_control(
        ui.tags.a(
            ui.tags.img(src="logo_cde.png", height="36px", style="margin-right: 10px;"),
            href="https://circulodeempresarios.org",
            target="_blank",
        ),
    ),

    title=ui.div(
        "La economia en datos",
        style="display: flex; align-items: center; font-weight: 700;",
    ),
    id="main_navbar",
    navbar_options=ui.navbar_options(bg="#1e2d3d", theme="dark"),
    footer=ui.div(
        ui.p(
            "Fuentes: INE, Eurostat, Yahoo Finance, Banco de Espana | ",
            ui.tags.strong("Circulo de Empresarios"),
        ),
        class_="dashboard-footer",
    ),
)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
def server(input, output, session):
    activity.page_server(input, output, session, data_store)
    prices.page_server(input, output, session, data_store)


app = App(app_ui, server, static_assets=WWW_DIR)
