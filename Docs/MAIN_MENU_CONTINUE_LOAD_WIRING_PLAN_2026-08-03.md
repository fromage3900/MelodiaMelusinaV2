# Main Menu Continue/Load → Melusina Wiring Plan — 2026-08-03

**Purpose:** Capture the "uncallable in main UI" items for the 20-min slice — the path from Main Menu to Melusina's exploration is gated by Continue/Load being disabled.
**Status:** Plan only. No editor changes made. Execute after the PIE gates in `PIE_VERIFICATION_CHECKLIST_2026-08-03.md` §4 pass.

---

## The Problem

The Main Menu can reach Melusina's exploration via **New Game**, but **Continue** and **Load Game** are disabled until the canonical save slot + process-restart save/load gates pass. This is the single biggest blocker for a "seamless loop."

## Current State (verified 2026-07-31 via Monolith)

- `WBP_MainMenu` has real graph chains for New Game, Continue, and opening Save/Load.
- `Background` image is set to `T_Melodia_SoftMG_Parchment`.
- **Buttons are NOT yet styled** across all 4 states (Normal/Hover/Pressed/Disabled).
- Continue and Load Game remain **disabled** until canonical slot + Save/Load-screen PIE gates pass.

## Wiring Order

### Step 1 — Canonical slot proof (PIE gate §4)
- [ ] 4.1 Create canonical `BP_JRPGSaveGame` slot
- [ ] 4.2 Full process exit → relaunch → load → state equivalent
- [ ] 4.3 One narrative flag restores without duplication
- [ ] 4.4 One reward restores without duplication
- [ ] 4.5 Load canonical slot with Quill unavailable → JRPG state preserved
- [ ] 4.6 Missing/unknown script → authored safe location
- [ ] 4.7 Wallet restart-idempotence: repeat grant rejected

**Exit:** Continue/Load can be safely enabled.

### Step 2 — Button styling (editor-side)
- [ ] 5.1 Style all 4 button states (Normal/Hover/Pressed/Disabled) using the SoftMG brush treatment
- [ ] 5.2 Verify focus ring + keyboard/gamepad navigation

### Step 3 — Wire Continue/Load to canonical JRPG GameInstance
- [ ] 5.3 Continue → loads canonical slot → resumes at last checkpoint
- [ ] 5.4 Load Game → opens Save/Load screen → select slot → load
- [ ] 5.5 Continue disabled with no canonical slot + explains why

### Step 4 — Route to Melusina
- [ ] 5.2 New Game → canonical JRPG GameInstance → exploration → Melusina
- [ ] 7.1 Morning → KaleidoNave (021b arrival fallout) — diagnose before routing playtest

## Dependencies

- **Blocked by:** PIE §4 (save/load/restart) — the canonical slot must be proven before Continue/Load is enabled.
- **Parallel:** PIE §1 (Quill guards), §2 (traversal), §3 (battle matrix) can run independently.
- **After:** PIE §6 (rhythm), §7 (route), §8 (packaged launch).

## Owner

- **Cline/Claude** — native save/load proof + wiring plan execution
- **Kiro** — button styling + focus/navigation (editor-side)
- **User** — PIE walk of §4 + §5

---

**End of Plan**
