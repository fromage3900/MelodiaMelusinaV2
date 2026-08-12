"""Dry-run site publish path resolution (no render, no git)."""
import json
import os
import sys
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
if str(DEPLOY) not in sys.path:
    sys.path.insert(0, str(DEPLOY))

# Import resolver without registering full addon
sys.path.insert(0, str(DEPLOY / "surreal_arch"))
# Prefer Tools helper for consistency
tools = DEPLOY.parent / "Tools"
if str(tools) not in sys.path:
    sys.path.insert(0, str(tools))

from melodia_website_root import resolve_website_root  # noqa: E402

site = resolve_website_root(DEPLOY.parent)
plates = site / "content" / "site-plates.json"
assets = site / "generated" / "assets" / "character"
report = {
    "ok": True,
    "website_root": str(site),
    "exists": site.is_dir(),
    "plates_json": str(plates),
    "plates_exists": plates.is_file(),
    "character_assets": str(assets),
    "character_assets_exists": assets.is_dir(),
    "env_MELODIA_WEBSITE_ROOT": os.environ.get("MELODIA_WEBSITE_ROOT", ""),
}
print(json.dumps(report, indent=2))
out = DEPLOY.parent / "Saved" / "Audit" / "site_publish_dry_last.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out}")
if not site.is_dir() or not plates.is_file():
    sys.exit(1)
print("site_publish_dry: OK")
