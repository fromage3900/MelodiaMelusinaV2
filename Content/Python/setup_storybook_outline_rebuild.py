"""Headless/editor entry: force-rebuild storybook PP graph."""
from __future__ import annotations

import setup_storybook_outline as storybook

if __name__ == "__main__":
    raise SystemExit(storybook.build_all(force=True))
