"""Melusina rig assessment — bones, materials, animations, retarget status.

Wraps assess_melusina_rig.build_full_report() with GMM audit envelope.
"""
from __future__ import annotations

from gmm.core.audit import GmmAudit


def assess_rig() -> dict:
    """Run full rig assessment and return audit report."""
    audit = GmmAudit(action="melusina.rig_assess")
    try:
        import assess_melusina_rig
        report = assess_melusina_rig.build_full_report()
        audit.ok(
            skeletal_mesh=report.get("skeletal_mesh", {}),
            animations=report.get("animations", {}),
            retarget_options=report.get("retarget_options", {}),
            blend_spaces=report.get("blend_spaces", {}),
        )
        path = audit.save("gmm_melusina_rig.json")
        audit.data["audit_path"] = path
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_rig.json")
        return audit.to_dict()
