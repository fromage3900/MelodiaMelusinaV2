"""GitHub Deployment for Portfolio Web Components

Automated deployment of generated web components to GitHub repository
for Wix iframe integration.

Usage:
  python Content/Python/github_deployer.py
  py Content/Python/github_deployer.py (in-editor)
"""

from __future__ import annotations

import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_COMPONENTS_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "WebComponents"
DEPLOYMENT_CONFIG = WEB_COMPONENTS_DIR / "deployment_config.json"
GITHUB_REPO_DIR = Path("G:/EnvironmentPortfolio/_github_deploy")  # Worktree of my-site repo

# Default deployment configuration
DEFAULT_CONFIG = {
    "github": {
        "repository": "username/wix-portfolio-assets",
        "branch": "main",
        "auto_deploy": True,
        "commit_message_prefix": "Auto-deploy from Unreal Pipeline"
    },
    "wix": {
        "site_url": "https://username.wixsite.com/portfolio",
        "update_strategy": "iframe",
        "cache_duration": 3600
    },
    "components": {
        "source_dir": "_staging/design-system",
        "target_components": "components",
        "target_projects": "projects",
        "target_generated": "generated"
    }
}


def _log(message: str) -> None:
    line = f"[GitHubDeployer] {message}"
    try:
        import unreal
        unreal.log(line)
    except ImportError:
        print(line)


def load_deployment_config() -> dict:
    """Load deployment configuration."""
    if not DEPLOYMENT_CONFIG.is_file():
        _log("No deployment config found, using defaults")
        return DEFAULT_CONFIG
    
    try:
        with open(DEPLOYMENT_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Merge with defaults
        return {**DEFAULT_CONFIG, **config}
    except Exception as exc:
        _log(f"Error loading deployment config: {exc}")
        return DEFAULT_CONFIG


def ensure_github_repo(config: dict) -> Path:
    """Ensure GitHub repository worktree exists and is up to date."""
    repo_path = GITHUB_REPO_DIR
    github_config = config.get('github', {})
    branch = github_config.get('branch', 'main')
    
    if repo_path.exists():
        _log(f"GitHub worktree already exists at {repo_path}")
        # Pull latest changes
        try:
            subprocess.run(['git', 'fetch', 'origin'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'checkout', branch], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'pull', 'origin', branch], cwd=repo_path, check=True, capture_output=True)
            _log("Updated GitHub worktree with latest changes")
        except Exception as exc:
            _log(f"Error updating GitHub worktree: {exc}")
    else:
        _log(f"GitHub worktree not found at {repo_path}. Expected worktree at G:/EnvironmentPortfolio/_github_deploy")
        raise RuntimeError("GitHub worktree not found. Run 'git worktree add _github_deploy main' from G:/EnvironmentPortfolio")
    
    return repo_path


def sync_components_to_github(repo_path: Path, config: dict) -> None:
    """Sync modular components to GitHub repository."""
    components_config = config.get('components', {})
    source_dir = PROJECT_ROOT / components_config.get('source_dir', '_staging/design-system')
    
    if not source_dir.exists():
        _log(f"Source directory not found: {source_dir}")
        return
    
    # Target directories in GitHub repo
    target_components = repo_path / components_config.get('target_components', 'components')
    target_projects = repo_path / components_config.get('target_projects', 'projects')
    target_generated = repo_path / components_config.get('target_generated', 'generated')
    
    # Create target directories
    for target_dir in [target_components, target_projects, target_generated]:
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy component files
    components_source = source_dir / 'components'
    if components_source.exists():
        _log(f"Copying components from {components_source} to {target_components}")
        for file in components_source.glob('*'):
            if file.is_file():
                shutil.copy2(file, target_components / file.name)
                _log(f"Copied {file.name}")
    
    # Copy example files as project templates
    examples_source = source_dir / 'examples'
    if examples_source.exists():
        _log(f"Copying examples from {examples_source} to {target_projects}")
        for file in examples_source.glob('*.html'):
            if file.is_file():
                shutil.copy2(file, target_projects / file.name)
                _log(f"Copied {file.name}")
    
    # Copy generated configs
    if WEB_COMPONENTS_DIR.exists():
        _log(f"Copying generated configs from {WEB_COMPONENTS_DIR} to {target_generated}")
        for file in WEB_COMPONENTS_DIR.glob('*.json'):
            if file.is_file():
                shutil.copy2(file, target_generated / file.name)
                _log(f"Copied {file.name}")
    
    _log("Component sync complete")


def generate_project_html(config: dict, hero_config: dict, passport_config: dict) -> None:
    """Generate project-specific HTML files from configurations."""
    generated_dir = GITHUB_REPO_DIR / config['components']['target_generated']
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    scene_name = hero_config.get('title', 'Project').lower().replace(' ', '-')
    
    # Generate hero HTML
    hero_html = generate_hero_html_from_config(hero_config)
    hero_path = generated_dir / f"{scene_name}-hero.html"
    with open(hero_path, 'w', encoding='utf-8') as f:
        f.write(hero_html)
    _log(f"Generated hero HTML: {hero_path}")
    
    # Generate passport HTML
    passport_html = generate_passport_html_from_config(passport_config)
    passport_path = generated_dir / f"{scene_name}-passport.html"
    with open(passport_path, 'w', encoding='utf-8') as f:
        f.write(passport_html)
    _log(f"Generated passport HTML: {passport_path}")


def generate_hero_html_from_config(config: dict) -> str:
    """Generate hero HTML from configuration."""
    # This would use the modular components to build the HTML
    # For now, return a template that references the modular system
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{config.get('title', 'Project')}</title>
<link rel="stylesheet" href="components/melodia-animations.css">
</head>
<body>
<div id="hero-container"></div>
<script src="components/melodia-utils.js"></script>
<script src="components/melodia-star-system.js"></script>
<script src="components/melodia-aurora.js"></script>
<script>
// Configuration from Unreal pipeline
const CONFIG = {json.dumps(config)};

// Initialize components
const aurora = new MelodiaAurora('#hero-container', CONFIG.auroraConfig).init();
const stars = new MelodiaStarSystem('#hero-container', CONFIG.starConfig).init();
</script>
</body>
</html>"""


def generate_passport_html_from_config(config: dict) -> str:
    """Generate passport HTML from configuration."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{config.get('project', 'Project')} - Asset Passport</title>
<link rel="stylesheet" href="components/melodia-animations.css">
</head>
<body>
<div id="passport-container"></div>
<script src="components/melodia-utils.js"></script>
<script src="components/melodia-star-system.js"></script>
<script>
// Configuration from Unreal pipeline
const CONFIG = {json.dumps(config)};

// Initialize passport with subtle effects
const stars = new MelodiaStarSystem('#passport-container', {{
  starCount: 8,
  enableParallax: false
}}).init();
</script>
</body>
</html>"""


def git_commit_and_push(repo_path: Path, config: dict) -> bool:
    """Commit and push changes to GitHub."""
    github_config = config.get('github', {})
    branch = github_config.get('branch', 'main')
    message_prefix = github_config.get('commit_message_prefix', 'Auto-deploy from Unreal Pipeline')
    
    try:
        # Check for changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=repo_path, capture_output=True, text=True)
        
        if not result.stdout.strip():
            _log("No changes to commit")
            return True
        
        # Add all changes
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True, capture_output=True)
        
        # Commit
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix} - {timestamp}"
        subprocess.run(['git', 'commit', '-m', commit_message], 
                      cwd=repo_path, check=True, capture_output=True)
        
        # Push
        subprocess.run(['git', 'push', 'origin', branch], 
                      cwd=repo_path, check=True, capture_output=True)
        
        _log(f"Successfully committed and pushed to {branch}")
        return True
        
    except Exception as exc:
        _log(f"Error during git commit/push: {exc}")
        return False


def deploy_to_github() -> dict:
    """Main deployment function."""
    _log("Starting GitHub deployment")
    
    # Load configuration
    config = load_deployment_config()
    
    # Check if auto-deploy is enabled
    if not config.get('github', {}).get('auto_deploy', True):
        _log("Auto-deploy disabled in configuration")
        return {"ok": False, "reason": "auto_deploy_disabled"}
    
    try:
        # Ensure GitHub repo
        repo_path = ensure_github_repo(config)
        
        # Sync components
        sync_components_to_github(repo_path, config)
        
        # Load latest configs
        hero_config_path = WEB_COMPONENTS_DIR / 'hero_config.json'
        passport_config_path = WEB_COMPONENTS_DIR / 'passport_config.json'
        
        hero_config = {}
        passport_config = {}
        
        if hero_config_path.exists():
            with open(hero_config_path, 'r', encoding='utf-8') as f:
                hero_config = json.load(f)
        
        if passport_config_path.exists():
            with open(passport_config_path, 'r', encoding='utf-8') as f:
                passport_config = json.load(f)
        
        # Generate project HTML files
        if hero_config and passport_config:
            generate_project_html(config, hero_config, passport_config)
        
        # Commit and push
        success = git_commit_and_push(repo_path, config)
        
        result = {
            "ok": success,
            "repo_path": str(repo_path),
            "branch": config['github']['branch'],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if success:
            _log("GitHub deployment successful")
        else:
            _log("GitHub deployment failed")
        
        return result
        
    except Exception as exc:
        _log(f"GitHub deployment error: {exc}")
        return {"ok": False, "error": str(exc)}


def main() -> int:
    try:
        result = deploy_to_github()
        print(f"GITHUB_DEPLOY ok={result['ok']}")
        return 0 if result['ok'] else 1
    except Exception as exc:
        print(f"GITHUB_DEPLOY failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())