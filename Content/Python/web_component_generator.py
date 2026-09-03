"""Web Component Generator for Portfolio Pipeline

Generates modular web component configurations from Unreal portfolio data.
Creates themed configurations for hero banners, asset passports, and effects.

Usage:
  python Content/Python/web_component_generator.py
  py Content/Python/web_component_generator.py (in-editor)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_PACKAGE = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
WEB_COMPONENTS_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "WebComponents"
DEPLOYMENT_MANIFEST = WEB_COMPONENTS_DIR / "deployment_manifest.json"

# Theme detection thresholds
CHARACTER_ASSET_THRESHOLD = 5
ENVIRONMENT_SCENE_THRESHOLD = 3
PROP_ASSET_THRESHOLD = 8


def _log(message: str) -> None:
    line = f"[WebComponentGenerator] {message}"
    try:
        import unreal
        unreal.log(line)
    except ImportError:
        print(line)


def load_portfolio_package() -> dict:
    """Load the portfolio package JSON."""
    if not PORTFOLIO_PACKAGE.is_file():
        _log(f"Portfolio package not found at {PORTFOLIO_PACKAGE}")
        return {}
    
    try:
        with open(PORTFOLIO_PACKAGE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        _log(f"Error loading portfolio package: {exc}")
        return {}


def detect_content_theme(package: dict) -> str:
    """Detect content theme based on portfolio data."""
    assets = package.get('assets', [])
    materials = package.get('materials', [])
    scene = package.get('scene', {})
    
    # Count asset types
    character_count = sum(1 for asset in assets if 'character' in str(asset.get('asset_type', '')).lower())
    prop_count = sum(1 for asset in assets if 'prop' in str(asset.get('asset_type', '')).lower())
    environment_count = sum(1 for asset in assets if 'environment' in str(asset.get('asset_type', '')).lower())
    
    # Analyze scene data
    scene_name = scene.get('scene_name', '').lower()
    has_environment_keywords = any(kw in scene_name for kw in ['environment', 'landscape', 'scene', 'level'])
    has_character_keywords = any(kw in scene_name for kw in ['character', 'hero', 'player', 'npc'])
    
    # Determine theme
    if character_count >= CHARACTER_ASSET_THRESHOLD or has_character_keywords:
        return 'character'
    elif prop_count >= PROP_ASSET_THRESHOLD:
        return 'prop'
    elif environment_count >= ENVIRONMENT_SCENE_THRESHOLD or has_environment_keywords:
        return 'environment'
    else:
        return 'abstract'


def select_performance_level(package: dict) -> str:
    """Select performance level based on asset complexity."""
    stats = package.get('stats', {})
    triangle_count = stats.get('triangle_count', 0)
    draw_calls = stats.get('draw_calls', 0)
    
    # Performance thresholds
    if triangle_count > 1000000 or draw_calls > 5000:
        return 'high'  # Minimal effects
    elif triangle_count > 500000 or draw_calls > 2000:
        return 'balanced'  # Default
    else:
        return 'highQuality'  # Maximum effects


def generate_hero_config(package: dict, theme: str) -> dict:
    """Generate hero banner configuration."""
    scene = package.get('scene', {})
    stats = package.get('stats', {})
    
    performance = select_performance_level(package)
    star_count = 70 if performance == 'highQuality' else 50 if performance == 'balanced' else 30
    
    return {
        "theme": "dark",
        "contentTheme": theme,
        "kicker": scene.get('category', '3D Environment & Technical Art'),
        "title": scene.get('scene_name', 'Project Name'),
        "sub": generate_subtitle(scene, theme),
        "starCount": star_count,
        "gstarCount": max(3, star_count // 10),
        "enableParallax": performance != 'high',
        "parallaxStrength": 0.03 if performance == 'balanced' else 0.05,
        "performance": performance
    }


def generate_passport_config(package: dict, theme: str) -> dict:
    """Generate asset passport configuration."""
    scene = package.get('scene', {})
    stats = package.get('stats', {})
    metadata = package.get('metadata', {})
    
    def format_number(num):
        if num is None:
            return "N/A"
        return f"{num:,}" if num >= 1000 else str(num)
    
    # Determine texture resolution
    materials = package.get('materials', [])
    texture_res = "4K"  # Default
    if materials:
        # Simple heuristic based on material count
        if len(materials) > 20:
            texture_res = "8K"
        elif len(materials) < 5:
            texture_res = "2K"
    
    return {
        "theme": "dark",
        "highlight": theme,
        "project": scene.get('scene_name', 'Project Name'),
        "category": scene.get('category', 'Environment'),
        "version": metadata.get('version', 'v1.0'),
        "animations": True,
        "hoverEffects": True,
        "decorativeStars": True,
        "rows": [
            ["Triangles", format_number(stats.get('triangle_count'))],
            ["Textures", texture_res],
            ["Materials", str(len(materials))],
            ["Engine", scene.get('engine', 'Unreal Engine 5.8')],
            ["Date", format_date(metadata.get('timestamp'))]
        ]
    }


def generate_subtitle(scene: dict, theme: str) -> str:
    """Generate subtitle based on scene and theme."""
    scene_name = scene.get('scene_name', '')
    
    subtitles = {
        'environment': [
            "crafted with precision",
            "where nature meets technology",
            "immersive digital worlds",
            "environmental storytelling"
        ],
        'character': [
            "brought to life",
            "digital character art",
            "where personality shines",
            "character-driven narratives"
        ],
        'prop': [
            "detailed craftsmanship",
            "object-focused storytelling",
            "where details matter",
            "prop artistry"
        ],
        'abstract': [
            "beyond imagination",
            "abstract digital art",
            "where creativity flows",
            "experimental expressions"
        ]
    }
    
    theme_subtitles = subtitles.get(theme, subtitles['environment'])
    import random
    return random.choice(theme_subtitles)


def format_date(timestamp: str | None) -> str:
    """Format timestamp to YYYY-MM."""
    if not timestamp:
        return datetime.now(timezone.utc).strftime("%Y-%m")
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m")


def generate_effect_config(package: dict, theme: str) -> dict:
    """Generate special effect configuration (aurora/cosmic)."""
    performance = select_performance_level(package)
    
    effects = {
        'environment': {
            'type': 'aurora',
            'config': {
                'auroraCount': 3 if performance != 'high' else 1,
                'auroraIntensity': 0.7 if performance == 'highQuality' else 0.5,
                'particleCount': 60 if performance == 'highQuality' else 30,
                'auroraColors': [
                    'rgba(110,90,166,0.4)',
                    'rgba(60,92,158,0.3)',
                    'rgba(156,148,198,0.3)'
                ]
            }
        },
        'character': {
            'type': 'aurora',
            'config': {
                'auroraCount': 3 if performance != 'high' else 1,
                'auroraIntensity': 0.7 if performance == 'highQuality' else 0.5,
                'particleCount': 50 if performance == 'highQuality' else 25,
                'auroraColors': [
                    'rgba(156,148,198,0.5)',
                    'rgba(110,90,166,0.4)',
                    'rgba(169,154,198,0.3)'
                ]
            }
        },
        'prop': {
            'type': 'cosmic',
            'config': {
                'enableGalaxy': performance == 'highQuality',
                'nebulaCount': 3 if performance != 'high' else 1,
                'shootingStarCount': 2 if performance == 'highQuality' else 0,
                'dustCount': 40 if performance == 'highQuality' else 20
            }
        },
        'abstract': {
            'type': 'cosmic',
            'config': {
                'enableGalaxy': True,
                'nebulaCount': 4 if performance == 'highQuality' else 2,
                'shootingStarCount': 3 if performance == 'highQuality' else 1,
                'dustCount': 50 if performance == 'highQuality' else 25
            }
        }
    }
    
    return effects.get(theme, effects['environment'])


def write_component_configs(hero_config: dict, passport_config: dict, effect_config: dict) -> None:
    """Write component configuration files."""
    WEB_COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write individual configs
    configs = {
        'hero_config.json': hero_config,
        'passport_config.json': passport_config,
        'effect_config.json': effect_config
    }
    
    for filename, config in configs.items():
        config_path = WEB_COMPONENTS_DIR / filename
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        _log(f"Written {filename}")


def write_deployment_manifest(package: dict, hero_config: dict, passport_config: dict) -> None:
    """Write deployment manifest for Wix integration."""
    scene = package.get('scene', {})
    project_name = scene.get('scene_name', 'project').lower().replace(' ', '-')
    
    manifest = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "name": scene.get('scene_name', 'Project'),
            "theme": detect_content_theme(package),
            "performance": select_performance_level(package)
        },
        "assets": {
            "hero": {
                "url": f"https://username.github.io/wix-portfolio-assets/generated/{project_name}-hero.html",
                "theme": hero_config.get('theme'),
                "contentTheme": hero_config.get('contentTheme'),
                "dimensions": {
                    "width": "100%",
                    "height": "520px"
                },
                "config": hero_config
            },
            "passport": {
                "url": f"https://username.github.io/wix-portfolio-assets/generated/{project_name}-passport.html",
                "theme": passport_config.get('theme'),
                "highlight": passport_config.get('highlight'),
                "dimensions": {
                    "width": "360px",
                    "height": "560px"
                },
                "config": passport_config
            },
            "effect": {
                "type": effect_config.get('type'),
                "url": f"https://username.github.io/wix-portfolio-assets/effects/{project_name}-effect.html",
                "config": effect_config.get('config')
            }
        },
        "fallback_urls": {
            "static_hero": "https://username.github.io/wix-portfolio-assets/projects/hero-static.html",
            "static_passport": "https://username.github.io/wix-portfolio-assets/projects/passport-static.html"
        }
    }
    
    with open(DEPLOYMENT_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    _log(f"Written deployment manifest to {DEPLOYMENT_MANIFEST}")


def generate_all_components() -> dict:
    """Main generation function."""
    _log("Starting web component generation")
    
    # Load portfolio package
    package = load_portfolio_package()
    if not package:
        _log("No portfolio package available, using defaults")
        package = {
            "scene": {
                "scene_name": "Default Project",
                "category": "Environment",
                "engine": "Unreal Engine 5.8"
            },
            "assets": [],
            "materials": [],
            "stats": {
                "triangle_count": 100000,
                "draw_calls": 500
            },
            "metadata": {
                "version": "v1.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    # Detect theme and performance
    theme = detect_content_theme(package)
    performance = select_performance_level(package)
    
    _log(f"Detected theme: {theme}, performance level: {performance}")
    
    # Generate configurations
    hero_config = generate_hero_config(package, theme)
    passport_config = generate_passport_config(package, theme)
    effect_config = generate_effect_config(package, theme)
    
    # Write configuration files
    write_component_configs(hero_config, passport_config, effect_config)
    
    # Write deployment manifest
    write_deployment_manifest(package, hero_config, passport_config)
    
    result = {
        "ok": True,
        "theme": theme,
        "performance": performance,
        "hero_config": hero_config,
        "passport_config": passport_config,
        "effect_config": effect_config,
        "deployment_manifest": str(DEPLOYMENT_MANIFEST)
    }
    
    _log(f"Web component generation complete: {theme} theme, {performance} performance")
    return result


def main() -> int:
    try:
        result = generate_all_components()
        print(f"WEB_COMPONENT_GENERATION ok={result['ok']} theme={result['theme']} perf={result['performance']}")
        return 0
    except Exception as exc:
        print(f"WEB_COMPONENT_GENERATION failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())