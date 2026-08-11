"""MPC (Material Parameter Collection) bridge — parameter catalog, wire suggestions.

Wraps bridge_melusina_to_mpc and setup_melusina_exploration.get_mpc_parameters().
"""
from __future__ import annotations

from gmm.core.audit import GmmAudit


def get_mpc_params() -> dict:
    """Read MPC_SakuraDream parameters for bridge planning."""
    audit = GmmAudit(action="melusina.mpc_params")
    try:
        import setup_melusina_exploration
        info = setup_melusina_exploration.get_mpc_parameters()
        audit.ok(
            exists=info.get("exists", False),
            scalar_params=info.get("scalar_params", []),
            vector_params=info.get("vector_params", []),
        )
        audit.save("gmm_melusina_mpc.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_mpc.json")
        return audit.to_dict()


def bridge_catalog() -> dict:
    """Build material slot → MPC parameter mapping."""
    audit = GmmAudit(action="melusina.bridge_catalog")
    try:
        import bridge_melusina_to_mpc
        result = bridge_melusina_to_mpc.build_mpc_bridge()
        audit.ok(**result)
        audit.save("gmm_melusina_bridge.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_bridge.json")
        return audit.to_dict()
