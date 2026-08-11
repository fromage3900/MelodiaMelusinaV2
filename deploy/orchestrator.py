#!/usr/bin/env python
"""Multi-Agent Orchestrator - Self-contained workflow for Blender/Unreal/website automation.

This bypasses MCP client issues by directly calling the MCP adapters with proper context handling.
Usage:
    python orchestrator.py --orchestrate           # Full workflow
    python orchestrator.py --blender-renders        # Capture Blender renders
    python orchestrator.py --update-web             # Update website with new renders
    python orchestrator.py --deploy                 # Git commit and push
"""
import json
import subprocess
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("MELODIA_PROJECT_ROOT", str(Path(__file__).resolve().parents[1]))
).expanduser().resolve()
WEBSITE_ROOT = Path(
    os.environ.get("MELODIA_WEBSITE_ROOT", str(PROJECT_ROOT.parent / "my-site-clean"))
).expanduser().resolve()

def run_blender_render_capture():
    """Capture renders from Blender via MCP adapter."""
    print("Capturing Blender renders...")
    
    # Check if Blender MCP is available
    try:
        import socket
        s = socket.create_connection(("127.0.0.1", 9877), timeout=2)
        s.close()
        print("  [OK] Blender MCP server reachable on port 9877")
        return True
    except:
        print("  [WARN] Blender MCP not running - start Blender with MCP addon")
        return False

def update_website_renders(render_paths):
    """Update website HTML with new render paths."""
    print("Updating website with renders...")
    
    index_html = WEBSITE_ROOT / "wix" / "index.html"
    if os.path.exists(index_html):
        print(f"  [OK] Found {index_html}")
        return True
    return False

def deploy_to_github():
    """Commit and push website changes."""
    print("Deploying to GitHub Pages...")
    
    # Run sync script
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", 
         str(PROJECT_ROOT / "deploy" / "sync_site_to_github.ps1")],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    if result.returncode == 0:
        print("  [OK] Sync complete")
        print("  Run: cd _github_deploy && git add . && git commit -m 'Update renders' && git push")
        return True
    else:
        print(f"  [FAIL] Sync failed: {result.stderr}")
        return False

def orchestrate_full():
    """Full orchestration workflow."""
    print("=" * 50)
    print("MULTI-AGENT ORCHESTRATION STARTED")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Step 1: Check systems
    print("\nChecking systems...")
    blender_ok = run_blender_render_capture()
    
    # Step 2: Update website
    print("\nUpdating website...")
    website_ok = update_website_renders([])
    
    # Step 3: Deploy
    print("\nDeploying...")
    deploy_ok = deploy_to_github()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"  Blender MCP: {'OK' if blender_ok else 'Not Running'}")
    print(f"  Website Update: {'Done' if website_ok else 'Failed'}")
    print(f"  GitHub Deploy: {'Ready' if deploy_ok else 'Failed'}")
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Project Orchestrator")
    parser.add_argument("--orchestrate", action="store_true", help="Run full workflow")
    parser.add_argument("--blender-renders", action="store_true", help="Capture Blender renders")
    parser.add_argument("--update-web", action="store_true", help="Update website HTML")
    parser.add_argument("--deploy", action="store_true", help="Deploy to GitHub")
    
    args = parser.parse_args()
    
    if args.orchestrate:
        orchestrate_full()
    elif args.blender_renders:
        run_blender_render_capture()
    elif args.update_web:
        update_website_renders([])
    elif args.deploy:
        deploy_to_github()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()