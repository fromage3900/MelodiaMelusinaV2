import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
audit = root / "Saved/Audit/MelusinaLegSkirt_20261023"
source_manifest = json.loads((audit / "session_package_manifest.json").read_text(encoding="utf-8"))
files = {
    entry["path"]
    for entry in source_manifest["files"]
    if entry["path"].startswith("Content/Staging/AnimationDoctor/LegSkirt_20261023/")
}
files.update({
    "Content/Python/audit_melusina_water_hair.py",
    "Saved/Audit/MelusinaLegSkirt_20261023/probe_locomotion_contact.py",
    "Saved/Audit/MelusinaLegSkirt_20261023/summarize_p0_closeout.py",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_waist_pinned_closeout.json",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_waist_pinned_summary.json",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_restart_ground_readback.json",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_ground_collision_before.json",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_ground_collision_fix.json",
    "Saved/Audit/MelusinaLegSkirt_20261023/p0_ground_collision_after.json",
})
for phase in ("idle", "walk", "turn", "stop"):
    files.add(f"Saved/Audit/MelusinaLegSkirt_20261023/p0_waist_pinned_closeout_move_{phase}.png")
for relative in sorted(files):
    assert (root / relative).is_file(), relative
entries = []
for relative in sorted(files):
    payload = (root / relative).read_bytes()
    entries.append({"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
manifest = {
    "schema": "melodia.melusina_p0_runtime_closeout.v1",
    "ground": "PASS: fresh House P0 spawn, injected movement, stop and fresh PIE restart; spawn Z=79.2125 cm, Walking.",
    "waist": "PASS for staging candidate only: maximum first-ring deviation 0.0000287 cm with Kawaii enabled across idle/walk/turn/stop.",
    "boots": "FAIL / OPEN: idle boot clearance 10.9375..11.6767 cm above traced P0 floor; no production AnimBP or wardrobe promotion.",
    "input_proof": "Injected AddMovementInput, not physical keyboard input.",
    "visual_boundary": "Four P0 captures inspected; overexposure and initial white-card VFX prevent final beauty acceptance. No run/sprint, bend, packaged, physical-input, or final FluidNinja droplet acceptance.",
    "files": entries,
}
package = root / "Saved/Packages/Melusina_P0_RuntimeCloseout_20261024.zip"
package.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for relative in sorted(files):
        archive.write(root / relative, relative)
    archive.writestr("p0_runtime_closeout_manifest.json", json.dumps(manifest, indent=2))
digest = hashlib.sha256(package.read_bytes()).hexdigest()
package.with_suffix(package.suffix + ".sha256").write_text(f"{digest}  {package.name}\n", encoding="utf-8")
receipt = {key: value for key, value in manifest.items() if key != "files"}
receipt.update({"package": str(package.relative_to(root)), "sha256": digest, "file_count": len(entries)})
(audit / "p0_runtime_package_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
