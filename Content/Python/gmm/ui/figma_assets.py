"""Figma Asset Loader — loads Melodia Game UI design tokens and raster assets.

Source: G:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/Source/MelodiaGameUI/
Manifest: pipeline/figma/figma_game_ui_manifest.json
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygame


@dataclass
class FigmaAsset:
    figma: str
    filename: str
    kind: str  # "alpha" | "texture"
    ue_dest: str
    web_use: str
    source: str
    web: str


def load_figma_manifest(manifest_path: Optional[str] = None) -> list[FigmaAsset]:
    """Load the Figma game UI manifest."""
    if manifest_path is None:
        # Default to project location
        root = Path(__file__).resolve().parents[4]  # BS_GodFile
        manifest_path = root / "pipeline" / "figma" / "figma_game_ui_manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assets = []
    for entry in data["entries"]:
        assets.append(FigmaAsset(**entry))
    return assets


class FigmaAssetLoader:
    """Loads and caches Figma design assets for PyGame."""

    def __init__(self, assets: Optional[list[FigmaAsset]] = None):
        self.assets = assets or load_figma_manifest()
        self._cache: dict[str, pygame.Surface] = {}
        self._source_dir = Path(self.assets[0].source).parent if self.assets else None

    def get(self, key: str) -> Optional[pygame.Surface]:
        """Get asset by web_use key (e.g., 'grade-perfect', 'highway-bg')."""
        if key in self._cache:
            return self._cache[key]

        asset = next((a for a in self.assets if a.web_use == key), None)
        if not asset:
            return None

        return self._load_asset(asset)

    def _load_asset(self, asset: FigmaAsset) -> Optional[pygame.Surface]:
        """Load a single asset from disk."""
        path = Path(asset.source)
        if not path.exists():
            # Try relative to source dir
            if self._source_dir:
                path = self._source_dir / asset.filename
            if not path.exists():
                print(f"[FigmaAssetLoader] Missing: {path}")
                return None

        try:
            # Ensure pygame display is initialized for convert_alpha
            if not pygame.display.get_init():
                pygame.display.set_mode((1, 1), pygame.HIDDEN)
            surf = pygame.image.load(str(path)).convert_alpha()
            self._cache[asset.web_use] = surf
            return surf
        except Exception as e:
            print(f"[FigmaAssetLoader] Failed to load {path}: {e}")
            return None

    def preload_all(self):
        """Preload all assets into cache."""
        for asset in self.assets:
            self._load_asset(asset)

    def get_grade_assets(self) -> dict[str, pygame.Surface]:
        """Get all 4 grade pop assets."""
        return {
            "perfect": self.get("grade-perfect"),
            "great": self.get("grade-great"),
            "good": self.get("grade-good"),
            "miss": self.get("grade-miss"),
        }

    def get_rhythm_assets(self) -> dict[str, pygame.Surface]:
        """Get rhythm highway assets."""
        return {
            "highway_bg": self.get("highway-bg"),
            "hitline": self.get("hitline"),
            "note_head": self.get("note-head"),
            "staff_tile": self.get("staff-tile"),
            "sheen_sweep": self.get("sheen-sweep"),
        }

    def get_ui_assets(self) -> dict[str, pygame.Surface]:
        """Get UI decorative assets."""
        return {
            "filigree_corner": self.get("filigree-corner"),
            "filigree_divider": self.get("filigree-divider"),
            "iri_overlay": self.get("iri-overlay"),
            "grain": self.get("grain"),
        }


# Singleton instance
_LOADER: Optional[FigmaAssetLoader] = None


def get_asset_loader() -> FigmaAssetLoader:
    global _LOADER
    if _LOADER is None:
        _LOADER = FigmaAssetLoader()
    return _LOADER


def preload_figma_assets():
    """Convenience function to preload all assets at startup."""
    get_asset_loader().preload_all()


if __name__ == "__main__":
    # Test loader
    pygame.init()
    loader = get_asset_loader()
    loader.preload_all()
    print(f"Loaded {len(loader._cache)} assets:")
    for k, v in loader._cache.items():
        print(f"  {k}: {v.get_size()}")