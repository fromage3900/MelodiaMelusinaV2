# QuillScript Grief Hook Review — 2026-08-03

**Reviewer:** Narrative Systems Analysis
**Date:** 2026-08-03
**Scope:** QuillScript dialogue system + Melodia grief hook narrative integration
**Build:** 0 errors, editor running at :9316

---

## 1. QuillScript Current State

### 1.1 What Is Working

**Plugin Foundations (stable)**
- `UDialogBox` / `USelectionBox` native C++ base classes in `Plugins/QuillScript/Source/Quillscript/Public/Widgets/`
- `AQuillscriptInterpreter` owns runtime execution, statement queue, `OnScriptPlay` broadcast
- `UQuillscriptSubsystem` publishes `OnNotified` and manages runtime variables/serialization

**Melodia Adapter Widgets (4-Widget Stack)** - `/Game/Melodia/UI/Quill/`
| Widget | C++ Parent | Role |
|--------|-----------|------|
| WBP_MelodiaQuillDialog | UMelodiaQuillDialogWidget | Speaker name + body text + advance button |
| WBP_MelodiaQuillSelection | UMelodiaQuillSelectionWidget | Vertical choice list |
| WBP_MelodiaQuillChoiceEntry | UMelodiaQuillChoiceEntryWidget | Choice row (6 widgets) |
| WBP_MelodiaQuillBackground | UMelodiaQuillBackgroundWidget | Background image during dialogue |

**Input Context** - `PushContext(Dialogue)` / `PopContext` wired in both Dialog and Selection widgets.

**Narrative Subsystem** - All 6 intent verbs routed: battle, quest, flag, travel, reward, stat.

**Authored QuillScript (5 scripts, 4 with .qsc source)**
- PetalPriestess: tonal choice, Harmony+1, quest activation
- Smoke: Sir reunion, battle trigger, all 4 result branches, reward, resolve
- StarWeaver: quest-2 gating (requires quest 1)
- TwilightDancer: quest-3 gating (requires quest 2)
- MelodiaMorningIntro.uasset: **compiled only, no .qsc source**

### 1.2 What Is Missing / Needs PIE

1. MorningIntro .qsc source missing - only compiled .uasset exists
2. Grief hook opening beats not authored (late arrival, absent duet)
3. PIE verification of full loop not yet performed
4. Resonance invisible in battle UI
5. 3 rhythm skills unregistered with combat subsystem
6. Main Menu Continue/Load disabled pending save round-trip proof

---

## 2. Grief Hook Narrative Flow

### 2.1 Emotional Beat Map

| # | Beat | Authored? | Notes |
|---|------|-----------|-------|
| 1 | Melusina arrives late | **NO** | Not in any .qsc |
| 2 | Absent duet partner felt | **NO** | 3-5 fragments needed |
| 3 | Sir alive/snack-seeking | **PARTIAL** | MorningIntro has no source; Smoke.qsc has reunion |
| 4 | Catastrophic reading (dream) | **NO** | Key dramatic irony beat |
| 5 | Tonal choice at Petal Priestess | **YES** | 2 options converge to Harmony+1 |
| 6 | Dream traversal + echoes | **YES** | 3 quest-gated NPCs with branching |
| 7 | Battle | **YES** | melodia:battle notify, 4 branches |
| 8 | Result -> Quill resume | **YES** | melodia_battle_result variable + ResumeQuillOnce() |
| 9 | Sir reunion | **PARTIAL** | Functional beat, missing emotional weight |
| 10 | One named moment at reunion | **NO** | Design only |
| 11 | Post-festival resolution | **NO** | Arriving not-late texture |

### 2.2 Critical Gap
The dramatic premise exists only in design documents: Melusina arrives late, duet partner absent, Sir snack-seeking, dream renders benign absence as catastrophe. Authored QuillScript covers the middle loop but not the hook.

---

## 3. Dialogue UI Gaps

### 3.1 Figma DialogueOverlay (~30+ children)
- Parchment panel, speaker nameplate with SparkleDrift, body text with styled scroll
- NPC portrait frame, decorative choice rows, Corner Baroque x2, dividers, seal accents
- Advance indicator icon, sparkle ambient, background transition overlay

### 3.2 Current WBP (~8 children per widget)
- WBP_MelodiaQuillDialog: ~8 widgets (SpeakerText, BodyText, AdvanceButton, basic background)
- WBP_MelodiaQuillSelection: ~8 widgets (OptionsBox, basic background)
- WBP_MelodiaQuillChoiceEntry: 6 widgets (ChoiceButton, ChoiceText, 3x FiligreeDivider)
- WBP_MelodiaQuillBackground: ~3 widgets (BackgroundImage)

### 3.3 Gap: ~20+ missing elements
- No parchment panel on Quill widgets (present in Main Menu)
- No speaker nameplate frame or sparkle drift
- No NPC portrait slot in dialog widget
- No Corner Baroque ornaments on dialog/selection
- No advance indicator icon
- No data-mg tier support for sparkle density
- No styled scroll frame for body text

---

## 4. Input Context Status

**PushContext(Dialogue) - WIRED in C++**
- UMelodiaQuillDialogWidget::Play_Implementation() calls PushContext(Dialogue)
- UMelodiaQuillSelectionWidget::Play_Implementation() calls PushContext(Dialogue)
- Handle stored as FMelodiaInputContextHandle member, released in NativeDestruct()
- ApplyActiveContext() sets FInputModeGameAndUI + cursor visible, suppresses movement
- IsMovementAllowed() returns false for Dialogue; IsSavingAllowed() returns true

**PopContext(Dialogue) - WIRED in C++**
- Released in NativeDestruct() and TryAdvance()/SelectOption() completion paths
- Removes by handle ID (not stack pop) so nested contexts release cleanly
- ClearAllContexts() logs leaked contexts for diagnostics

**Needs PIE Verification**
- Dialogue blocks movement, restores on close
- Selection blocks advance correctly
- Battle context push/pop transitions cleanly
- Travel force-clears stack without leaks
- Nested context ordering (menu+dialogue) works

**Risk: Low.** C++ wiring complete and correct. Only runtime testing needed.

---

## 5. Ready-for-Next-Phase Assessment

### 5.1 P0 Quill Work - Author the Grief Hook Opening
1. Create MelodiaMorningIntro.qsc source from the compiled asset
2. Write past-person fragments (3-5 beats): half-melody, place-that-listens, silence
3. Draft the one human-language sentence at reunion
4. Author the empty-perch seam beat (benign snack-run as dream catastrophe)

### 5.2 P1 - PIE Verification
1. Full loop: Morning -> Priestess -> Battle -> Reunion -> Save -> Load
2. Input context push/pop
3. All 4 battle result branches to correct labels
4. Idempotence across save/load (Harmony 1/5, no duplicate rewards)

### 5.3 P1 - Dialogue UI Polish
1. Parchment background on Quill dialog/selection widgets
2. Speaker portrait slot
3. Advance indicator (arrow/sparkle)
4. data-mg tier wiring for sparkle density

### 5.4 P2 - Author Texture
1. UMelodiaPacingProfile for morning (held-beat) / dream (stutter) registers
2. Post-festival arrival dialogue (each new area feels slightly late)
3. "Place changed" return beat (Layers of Fear style)

### 5.5 Current Blockers
1. Save round-trip unproven - blocks Continue/Load, wallet, multi-session arc
2. MorningIntro .qsc missing - foundational grief hook beat not editable
3. 3 rhythm skills unregistered - battle-as-dialogue layer untestable
4. Resonance invisible in battle UI - core metaphor unproven in combat

### 5.6 Risk Summary
- **Green:** Input context, narrative routing, adapter widgets, stat/quest gating all correct
- **Yellow:** Morning Intro has no source; 20+ Figma elements missing but not phase-blocking
- **Red:** Save round-trip is the single unproven gate; narrative persistence is theoretical until it passes

---

## Appendix: Key File Paths

| Component | Path |
|-----------|------|
| Quill DialogBox | `Plugins/QuillScript/Source/Quillscript/Public/Widgets/DialogBox.h` |
| Quill SelectionBox | `Plugins/QuillScript/Source/Quillscript/Public/Widgets/SelectionBox.h` |
| Melodia Adapter Widgets | `Source/BS_GodFile/MelodiaIntegration/MelodiaQuillPresentationWidgets.h/.cpp` |
| Narrative Subsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h/.cpp` |
| Narrative Types | `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h` |
| Input Context | `Source/BS_GodFile/MelodiaIntegration/MelodiaInputContextSubsystem.h/.cpp` |
| PetalPriestess .qsc | `Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc` |
| Smoke/Reunion .qsc | `Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc` |
| MorningIntro (compiled) | `Content/MelodiaIntegration/Narrative/MelodiaMorningIntro.uasset` |
| Moonolith | `http://localhost:9316` |
| Grief Hook Design | `Docs/Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md` |
| Playtest Script | `Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md` |
| Review Output | `Docs/Reviews/QUILLSCRIPT_GRIEF_HOOK_REVIEW_2026-08-03.md` |
