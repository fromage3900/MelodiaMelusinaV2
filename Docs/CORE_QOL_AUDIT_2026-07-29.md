# Core QoL Audit — 2026-07-29

## Authority map

| System | Current authority | Status |
|---|---|---|
| Campaign save/load | Stock `BP_JRPGSaveGame` / GameInstance `LoadThisGame` | Canonical; do not replace |
| Narrative persistence | `UMelodiaNarrativeSubsystem`, embedded in stock save | Canonical Melodia extension |
| Player preferences | `UMelodiaGameUserSettings` | Staged; separate from campaign save |
| Quests | `UMelodiaPersonaSubsystem` + narrative record | Canonical for new content |
| Legacy quest actor | `AMelodiaQuestManagerBase` | Do not author new quest state here |
| Dialogue | QuillScript | Canonical presentation/dialogue route |
| Turn/damage/exit | Stock JRPG controller | Canonical |

## Verified front-end state

- New Game creates the canonical `MelusinaSlot0` save and begins the opening sequence route.
- Continue is disabled when no canonical slot exists.
- The main-menu load route now opens `WBP_SaveLoadPanel`, whose existing action owns the canonical slot load.
- Save feedback now reads the stock save's `currentMap` and `saveDate` fields; it does not introduce duplicate metadata.
- Main menu has explicit directional navigation: New Game → Continue → Load Game → Settings.
- `WBP_MainMenu` and `WBP_MelodiaSettings` compiled cleanly in the current Editor session.

## Staged settings contract

- `UMelodiaGameUserSettings` persists Master/Music/SFX volume, reduced motion, high-contrast text, minimal HUD, and UI scale in user config.
- `SM_MelodiaUserPreferences` is the dedicated SoundMix for Master/Music/SFX overrides.
- `WBP_MelodiaSettings` exposes named controls for the preferences. Native build and post-build binding are still required before live use.
- Settings must never read or write the JRPG campaign slot.

## Exploration UI

- Active `BP_ExploreUI` contains the minimal reactive HUD, resonance journal, and quest-gated minimap markers.
- `UMelodiaPersonaSubsystem::RefreshMinimapWidgets` manages the Echo and Forest Exit marker visibility from quest state.
- Journal text should bind to the canonical Persona/Narrative quest state before adding a separate quest-log data path.

## Orrery / fast travel readiness

`WBP_ComicOrrery` currently has button click routes directly calling **Open Level (by Name)** for Sakura, Stage, Celestial, and Village. It is not safe to expose as fast travel yet because it lacks:

1. registry-driven unlock evaluation;
2. map-asset validation;
3. confirm/cancel and input restoration;
4. canonical save before travel and return/spawn context after travel;
5. locked-state messaging and focus behavior.

### Safe implementation order

1. Use `UMelodiaOrreryRegistry` as the one destination/unlock data source.
2. Add a `RequestTravel` adapter that verifies `IsSphereUnlocked` against narrative opening phase.
3. Save via the existing stock save transaction before any accepted travel.
4. Travel only to registry-approved map assets; preserve a destination spawn tag in the existing narrative record.
5. Add confirmation, locked feedback, and a Back path to the widget.
6. Live-test one unlocked and one locked destination before exposing any other sphere.

## Next closed-editor gate

1. Build `BS_GodFile` and `MelodiaCore` after staging menu/settings changes.
2. Bind settings controls to `UMelodiaGameUserSettings`; reopen and verify persistence across restart.
3. Live-test menu focus, New Game, no-save feedback, saved location/time feedback, Load panel, Settings Back, and audio slider response.
4. Only then begin the registry-based Orrery travel adapter and dynamic journal text.
