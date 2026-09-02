# Melodia — Test Readiness & Verification Record

**Last Updated:** 2026-09-02  
**Purpose:** distinguish historical P0 evidence from the proof required for future Chapters/Voyages.

---

## 1. P0 baseline

The 2026-09-01 closeout record reports a green automated baseline across the existing GMM, P0 integration, ECHO/contract, MCP, daemon, and release-hygiene suites, including the recorded **524 / 524** aggregate in the prior certification snapshot.

Treat that number as **bounded evidence for the captured revision and suite composition**. It is not a permanent statement that every later branch, Chapter, or Voyage is certified simply because the old count once passed.

Re-run the relevant suites after changing their subject.

---

## 2. What P0 proves

P0 testing provides evidence that the project can integrate:

- Quill/narrative progression;
- turn-based JRPG/Phoenix action flow;
- Melodia rhythm execution;
- wardrobe gameplay/traversal;
- music-as-key world interaction;
- single-writer UI;
- idempotent reward/narrative consumption;
- canonical save/load infrastructure.

The next quality bar is deeper **restart and repeat-load closure**, especially across Wardrobe, Convergence, Starskiff/world state, and future schema growth.

---

## 3. Verification tiers for the long-lived game

Every new content unit should be explicit about which tiers it requires.

### Tier A — source/content presence
Files, assets, specs, IDs, and references exist.

**Not runtime proof.**

### Tier B — offline contract proof
Schemas, allowlists, progression contracts, static ownership constraints, and deterministic content rules pass without Unreal runtime mutation.

### Tier C — live/PIE proof
Real runtime behavior executes through the intended owner path with no duplicate UI/authority or stale state.

### Tier D — restart/idempotency proof
Durable facts survive full process restart; repeated load/consume does not duplicate rewards, modifiers, quest flags, world consequences, or registrations.

### Tier E — packaged proof
The exact promoted content runs in a packaged build with the claimed route/assets/state.

A major Chapter, Monolith Event, or Voyage is not release-ready until the tiers relevant to its durable behavior pass.

---

## 4. Current commands

```powershell
# Primary suite
.\run_tests.ps1

# Offline P0/static preflight
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/verify_p0_offline.py

# Melodia MCP regression
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_melodia_mcp.py

# End-to-end release/hygiene
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_e2e_melusina_release.py
```

Use the specific Chapter/content contract suites registered for the files being changed rather than relying only on a global aggregate.

---

## 5. Runtime persistence acceptance

Current high-priority test sequence:

```text
construct valid durable state
      ↓
save
      ↓
end process / PIE
      ↓
start fresh process / PIE
      ↓
load
      ↓
validate complete state vector
      ↓
load same save again
      ↓
validate identical state / zero duplication
```

Test invalid candidates separately:

- inconsistent equipped-vs-owned wardrobe state;
- unsupported/migration-failed record;
- intentionally empty equipment/inventory state;
- missing/corrupt referenced content where fail-safe behavior is expected.

Validation should occur before destructive mutation whenever ownership/dependency boundaries permit it.

---

## 6. Chapter-package acceptance

For a future Chapter/Reverie/Voyage, retain evidence for:

- exact progression/content spec revision;
- stable IDs and prerequisites;
- authoring source refs;
- offline validation result;
- live route/result proof if applicable;
- save/restart proof for any durable fact;
- packaged content manifest/build hash before release promotion.

A quiet non-combat Reverie does not need a battle test. A combat Chapter does. A Monolith Event may need world-state/traversal proof instead of enemy-HP proof.

**Testing follows the content's actual systems; content no longer has to imitate P0's pacing to be considered valid.**

---

## 7. Evergreen content boundary

Future Gifts/Reveries/Voyages must use the same verification philosophy:

- stable globally unique IDs;
- idempotent claims;
- forward-compatible save migration;
- optional network failure must not break core gameplay;
- claimed/installed content must remain legible to future saves.

Remote-manifest/backend tests are intentionally future work and are not a P0 requirement.

---

## 8. Verdict language

Prefer precise claims:

- **source present**;
- **offline contract pass**;
- **live PIE pass**;
- **restart/idempotency pass**;
- **packaged pass**.

Avoid saying “the game is certified” when only one tier was measured.

This evidence discipline is what lets Melodia grow for years without old confidence claims silently becoming false.
