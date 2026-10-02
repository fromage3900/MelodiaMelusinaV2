---
name: music-manager
description: Play adaptive music that reacts to combat vs exploration battle states, plus area-based music overrides, with the ACF Music Manager module.
globs: []
alwaysApply: false
---

# Music Manager — ACF Ultimate

The **Music Manager** plays **adaptive music** that switches automatically with the game's `EBattleState` (`EExploration` ↔ `EBattle`). `UACFMusicComponent` lives on the **Player Controller**, maps each battle state to a `USoundCue`, and listens to `UACFAIManagerComponent::OnBattleStateChanged` (on the GameState) to crossfade between exploration and combat tracks. It also supports **music overrides** (story moments) and `AACFMusicVolume` trigger spheres for **area-based** music swaps.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Music component | `UACFMusicComponent` | Added on your Player Controller Blueprint | Maps battle states → cues, handles fades/overrides |
| AI manager (state source) | `UACFAIManagerComponent` | On the GameState (sample GameState) | Drives `EBattleState` + `OnBattleStateChanged` |
| Music cues | `USoundCue` | `/Game/.../Audio/Music/` | Exploration / combat tracks |
| Music volume | `AACFMusicVolume` | Place in level | Sphere trigger that overrides music while the player is inside |

> **Never edit sample assets.** Duplicate any sample SoundCues / Player Controller into `Content/YourGame/Audio/` and customize your copies.

### Key types

| Type | Role |
|---|---|
| `UACFMusicComponent` | `UActorComponent` on the Player Controller; only acts when locally controlled |
| `EBattleState` | `EExploration` / `EBattle` (defined in `ACFAITypes.h`) |
| `AACFMusicVolume` | `ATriggerSphere` with a `MusicOverride` cue applied on overlap |

---

## 2 — Setup / Configuration

1. Open your **Player Controller** Blueprint (duplicate the sample one into `Content/YourGame/` first if customizing).
2. **Add Component → ACF Music Component** (it's a `BlueprintSpawnableComponent`).
3. In the component's **Class Defaults**, fill **`MusicCueByState`** (TMap `EBattleState → USoundCue*`):
   - `EExploration` → your ambient/exploration cue.
   - `EBattle` → your combat cue.
4. Tune the other defaults:
   - **`bAutoStart`** (default true) — start music on `BeginPlay` for the local player.
   - **`FadeTime`** (default 2.0) — crossfade duration when the state changes.
   - **`VolumeMult`** — playback volume multiplier.
   - **`concurrencySettings`** — optional `USoundConcurrency` for the music channel.
5. Ensure your **GameState** has a `UACFAIManagerComponent` (the ACF sample GameState does). The music component finds it via `GetGameState` and binds to `OnBattleStateChanged`. If it's missing, you'll see a `Missing ACFGameState!` warning and music won't follow combat.

---

## 3 — Core Workflow / Runtime API

The component reacts automatically once started, but you can drive it manually (category **ACF**):

| Function | Signature | Notes |
|---|---|---|
| `StartMusic` | `()` | Binds to `OnBattleStateChanged` and plays the cue for the current state (local player only) |
| `StopMusic` | `()` | Stops current playback |
| `PlayMusicCueByState` | `(EBattleState)` | Plays the cue mapped to a specific state |
| `SetMusicCueByState` | `(USoundCue*, EBattleState)` | Reassigns a cue for a state at runtime |
| `GetMusicCueByState` | `(EBattleState) → USoundCue*` | Returns the mapped cue |
| `StartMusicOverride` | `(USoundCue*)` | Plays an override cue, ignoring battle state (story moments) |
| `StopMusicOverride` | `()` | Ends override and resumes state-based music |
| `GetCurrntlyPlayingMusic` | `() → USoundCue*` | BlueprintPure; the active cue |
| `GetIsStarted` | `() → bool` | BlueprintPure; whether the system is running |

### Adaptive flow (automatic)

```
Player enters combat → UACFAIManagerComponent sets EBattleState::EBattle
  → OnBattleStateChanged broadcast
  → UACFMusicComponent::HandleStateChanged → crossfade to the EBattle cue
Combat ends → EExploration → crossfade back to exploration cue
```

### Manual override (boss intro / cutscene)

```
// Force a one-off track regardless of combat state:
MusicComp->StartMusicOverride(BossThemeCue);

// Return to normal adaptive music:
MusicComp->StopMusicOverride();
```

### Area-based music (`AACFMusicVolume`)

1. Drag `AACFMusicVolume` into the level (it's an `ATriggerSphere`).
2. Set its **`MusicOverride`** cue and size the sphere.
3. While a player is inside, the volume applies its override cue; leaving restores adaptive music — no code required.

---

## 4 — Wire to Characters / Blueprints

- **Player Controller:** the component belongs here so it can detect the **locally controlled** player (it no-ops on remote/non-local owners).
- **GameState:** must have `UACFAIManagerComponent` so battle state changes propagate. This is the single source of truth for exploration/combat.
- **Story beats:** from a cutscene or quest Blueprint, get the local player controller → `Get Component By Class (ACF Music Component)` → `Start Music Override` / `Stop Music Override`.
- **Zones:** use `AACFMusicVolume` actors for town/dungeon/safe-zone music without scripting.
- **Runtime track swaps:** call `SetMusicCueByState` to switch the whole palette (e.g. when entering a new biome) and `PlayMusicCueByState` to re-evaluate immediately.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `UACFMusicComponent` added to the **Player Controller** (not the pawn or GameState).
- [ ] `MusicCueByState` has entries for both `EExploration` and `EBattle`.
- [ ] GameState has a `UACFAIManagerComponent` (use the ACF sample GameState or add it).
- [ ] `bAutoStart` is true (or you call `StartMusic` yourself).
- [ ] `FadeTime` / `VolumeMult` tuned; concurrency set if you need ducking.

**Common failures:**

| Symptom | Fix |
|---|---|
| No music at all | `bAutoStart` false and `StartMusic` never called; or component not on the local Player Controller |
| `Missing ACFGameState!` warning | GameState lacks `UACFAIManagerComponent` — music can't bind to battle state |
| Music doesn't switch in combat | State map missing an entry, or `OnBattleStateChanged` never fires (AI manager not driving state) |
| Override never ends | `StopMusicOverride` not called |
| Plays on dedicated server / wrong client | Expected — the component only plays for the locally controlled player |
| Harsh cut between tracks | Increase `FadeTime` for a smoother crossfade |
| Volume music doesn't restore on exit | Overlapping volumes, or the volume's `MusicOverride` cue is null |
