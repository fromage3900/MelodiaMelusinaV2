"""Reload the studio panel and open it. Run once from Execute Python Script."""
import importlib

import melodia_studio_panel as studio

importlib.reload(studio)
studio.open_studio()
