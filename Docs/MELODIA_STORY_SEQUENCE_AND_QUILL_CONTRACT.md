# Melodia story sequence and Quill contract

## Ownership

- The stock JRPG GameInstance and `BP_JRPGSaveGame` own the single canonical save slot, map restoration, party state, and gameplay load transaction.
- `UMelodiaNarrativeSubsystem` owns the versioned `melodiaNarrativeRecord` embedded in that stock save.
- QuillScript owns dialogue presentation, choices, script flow, and its own variables/history payload.
- `UMelodiaStorySequenceWidget` is presentation only. It never creates saves, changes quests, starts battles, or travels on its own.

## Reusable story sequence workflow

1. Create a `UMelodiaStorySequenceData` asset under `/Game/Melodia/Narrative/Sequences`.
2. Add ordered cards with optional artwork/stinger, kicker, title, body, and auto-advance duration. A duration of zero requires user advance.
3. Use `/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow`, parented to `UMelodiaStorySequenceWidget`, with these exact optional binding names:
   - `SlideArtwork`
   - `KickerText`
   - `TitleText`
   - `BodyText`
   - `AdvanceButton`
   - `SkipButton`
4. A caller owns what completion means. Main Menu completion opens the existing Morning map; future quest vignettes may resume their own interaction instead.
5. Keep slides editable data. Do not put map names, save-slot names, battle IDs, or quest completion logic in slideshow data.

For an authored destination or pre-encounter vignette, place
`/Game/Melodia/Blueprints/BP_StorySequenceTrigger`, assign its `Sequence`, and
bind `OnSequenceFinished` in that level's existing Blueprint logic. The trigger
only plays presentation and restores player input; its completion event is the
sole handoff point for any existing encounter, door, or destination behavior.

## Quill and canonical persistence

- Stock save invokes `SyncNarrativeRecordToSave` before serialization and `RestoreNarrativeRecordFromSave` in its existing load transaction.
- The narrative record serializes Quill's public variables/history payload into the canonical save, with `melodia_*` variables retained as a compatibility-readable map.
- New Game resets the narrative record before assigning the fresh canonical save. It must never inherit flags or dialogue state from Continue.
- Quill may restart from an authored interaction label after load. Do not attempt to restore a transient dialogue widget, a pressed choice, or a mid-line interpreter state across map travel.
- Stable narrative state uses the `melodia_` prefix. Do not initialize persistent variables at the top of a replayable `.qsc`; that would overwrite loaded state.

## First-dream scene rules

- `/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke` is compiled from `Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc`.
- It routes `melodia:battle:melodia_smoke_encounter` through the narrative subsystem and battle adapter.
- Only the adapter maps the stock battle result to Quill and resumes the interpreter exactly once.
- Priestess dialogue and future enemy pre/post-battle scenes use the same `melodia:` intent route; no direct encounter trigger bypasses the narrative subsystem.

## Verification

1. Closed-editor native build after C++ changes.
2. Reparent/compile `WBP_MelodiaOpeningSlideshow`; create and fill `DA_Opening_MelusinaMorning`.
3. Compile the Quill asset from the checked-in `.qsc` source.
4. Live test New Game, Skip/Advance, a canonical save/load, Priestess interaction, and one smoke encounter.
