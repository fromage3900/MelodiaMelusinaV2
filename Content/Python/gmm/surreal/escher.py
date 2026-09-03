"""Escher impossible geometry generators — wraps build_escher_relativity_room + build_pcg_escher.

Provides MCP-callable wrappers for the 6 Escher PCG graphs (Relativity Room, Penrose Loop,
Recursive Room, Gravity Shift Corridor, Belvedere, Waterfall) and 3 Baroque PCG graphs
(Spiral Staircase, Vault Cluster, Rotunda Oculus).
"""
from __future__ import annotations

from typing import Optional

from gmm.core import GmmAudit

ESCHER_GRAPH_NAMES = (
    "relativity_room", "penrose_loop", "recursive_room",
    "gravity_shift", "belvedere", "waterfall",
)
BAROQUE_GRAPH_NAMES = ("spiral_staircase", "vault_cluster", "rotunda_oculus")

ESCHER_DEST = "/Game/EnvSandbox/PCG/Styles/Escher"
BAROQUE_DEST = "/Game/EnvSandbox/PCG/Styles/Baroque"


def _ensure_unreal() -> None:
    import unreal  # noqa: F401


def build_escher_graphs(force: bool = False, names: Optional[list[str]] = None) -> dict:
    """Build selected (or all) Escher PCG graphs via build_escher_relativity_room.

    Returns audit dict with per-graph status.
    """
    try:
        import build_escher_relativity_room as ber
    except ImportError:
        return {"ok": False, "error": "build_escher_relativity_room not available"}

    targets = [n for n in (names or list(ESCHER_GRAPH_NAMES)) if n in dir(ber)]
    results = {}
    for name in targets:
        builder = getattr(ber, f"build_{name}", None)
        if not builder:
            results[name] = {"ok": False, "error": f"no builder: build_{name}"}
            continue
        try:
            out = builder()
            results[name] = {"ok": True, "output": str(out) if out else "built"}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
    audit = GmmAudit(action="surreal.escher.build", subsystem_results=results,
                     graph_count=len(results), ok=all(r["ok"] for r in results.values()))
    audit.save("gmm_escher_build.json")
    return audit.to_dict()


def build_baroque_graphs(force: bool = False) -> dict:
    """Build Baroque PCG graphs (spiral staircase, vault cluster, rotunda oculus)."""
    try:
        import build_pcg_escher as bpe
    except ImportError:
        return {"ok": False, "error": "build_pcg_escher not available"}

    results = {}
    for name in BAROQUE_GRAPH_NAMES:
        mapper = {"spiral_staircase": bpe.build_spiral_staircase_graph,
                  "vault_cluster": bpe.build_vault_cluster_graph,
                  "rotunda_oculus": bpe.build_rotunda_oculus_graph}
        builder = mapper.get(name)
        if not builder:
            results[name] = {"ok": False, "error": "no builder"}
            continue
        try:
            out = builder()
            results[name] = {"ok": True, "output": str(out) if out else "built"}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
    audit = GmmAudit(action="surreal.baroque.build", subsystem_results=results,
                     graph_count=len(results), ok=all(r["ok"] for r in results.values()))
    audit.save("gmm_baroque_build.json")
    return audit.to_dict()


def deploy_escher_pcg(level: str = "", rebuild: bool = False, generate: bool = True) -> dict:
    """Deploy Escher PCG volumes into the specified level.

    Delegates to setup_pcg_escher.deploy_escher_pcg().
    """
    try:
        import setup_pcg_escher as spe
    except ImportError:
        return {"ok": False, "error": "setup_pcg_escher not available"}
    try:
        result = spe.deploy_escher_pcg(
            level=level or spe.DEFAULT_LEVEL,
            rebuild=rebuild, generate=generate, save_level=True,
        )
        return {"ok": result.get("passed", False), "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ESCHER_STATUS() -> dict:
    """Return status of all Escher graphs (exist check)."""
    try:
        import unreal
    except ImportError:
        return {"ok": False, "error": "unreal not available"}

    status = {}
    for name in ESCHER_GRAPH_NAMES:
        path = f"{ESCHER_DEST}/PCG_Escher{name.replace('_', ' ').title().replace(' ', '')}"
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        status[name] = {"path": path, "exists": exists}
    return {"graphs": status, "ok": all(s["exists"] for s in status.values())}
