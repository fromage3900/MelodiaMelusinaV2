# Agent / CLI — Melodia stage save policy

**Do not save over the live portfolio stage.**

- Canonical live file: whatever highest `KitbashExport/Melodia_Portfolio_Stage_vN.blend` the artist has open (as of 2026-07-14: **v14** / open sessions may still show **v13**).
- Tools may **read** / inventory / print audits.
- Tools must **not** call `bpy.ops.wm.save_mainfile()` on `Melodia_Portfolio_Stage_*.blend` unless:
  - `MELODIA_ALLOW_STAGE_SAVE=1` is set **and**
  - the operator explicitly asked for `--save`
- Prefer writing sidecars under `Saved/Audit/*.blend` if a modified copy is needed.
- Prefer the user opening the stage in GUI and running scripts via Text Editor without save; they own Save.

Shader / lookdev work lives in the .blend the artist has open — agents do not reclaim or overwrite that session.

## Hard stop (active — recreate if missing)

If `Saved/Audit/MELUSINA_SHADER_AGENT_STOP` exists:

- **Zero** material / world node edits on Melusina or stage lighting
- **Zero** stage saves
- Recovery freeze: `Saved/Audit/melusina_shader_recovery/Melodia_Portfolio_Stage_v14_PRE_225030_from_blend1.blend`
- See `Docs/MELUSINA_SHADER_REVERT_STOP_2026-07-14.md`

Also check `Saved/Audit/sheet_hud_loop_STOP` — no agent wake loops on Melusina/stage/HUD.

## Soft stage visibility (Melodia Studio)

Viewport isolate via Outliner-friendly `LayerCollection.hide_viewport` only.
Render isolate via `Collection.hide_render`. Never hard-lock with `Collection.hide_viewport`.
Review Queue: N-panel Prev / Solo / Next (`surreal_arch.review_queue_cycle`) or Shift+G pie Review Prev/Next.
2026-07-16 review helpers: Solo Object (`surreal_arch.solo_object`) is local-view isolate only; Ivy (Bagapie) (`surreal_arch.ivy_scatter`) is available for soft review/marketing prep. These do not change the no-agent-save policy.
