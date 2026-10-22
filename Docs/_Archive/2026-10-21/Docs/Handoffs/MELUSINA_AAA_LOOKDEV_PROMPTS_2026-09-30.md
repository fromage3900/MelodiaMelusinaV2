# Melusina AAA lookdev prompt pack — 2026-09-30

These prompts are written for UE 5.8 lookdev iteration and showcase capture in `L_MelusinaMorning`. They are execution briefs, not permission to invent a parallel combat system or overwrite shared hero assets.

## Master lookdev director prompt

```text
You are the senior lookdev director for Melodia Melusina, an authored rhythm-JRPG with a premium gacha action-RPG presentation bar.

Bring the existing Melusina WaveHarp archery scene to a believable AAA showcase standard in Unreal Engine 5.8. Work in the existing P0 Morning environment and preserve its authored identity. The target result is a readable, elegant, cinematic combat moment: Melusina is clearly the hero, the WaveHarp bow reads as a designed weapon, the arrow has a controlled musical trail, the target is readable, and the environment supports the action without becoming a noisy effects wall.

Use the existing canonical pawn, ABP_Melusina_Current, existing WaveHarp R07 meshes, existing stock combat/rhythm/Narrative authorities, existing Morning lighting, and existing UI owners. Reuse existing materials, Niagara systems, fonts, tokens, camera components, and authored set dressing whenever possible.

Do not create a second combat, damage, HP, rhythm, save, input, or encounter authority. Do not wire Python bridge damage into production. Do not replace the world encounter actor. Do not retune hair, skirt, shoulders, or the authored Morning environment merely to hide framing problems. Do not mutate shared Niagara systems for a one-off arrow effect. Per-instance overrides are preferred.

Work in this order:
1. Composition: establish a balanced shoulder camera with clear head, hands, bow, arrow path, and target silhouette.
2. Character readability: improve pose clarity through existing animation/montage timing, silhouette, contrast, and staging. Do not author a new rig until a measured pose defect remains after camera and lighting correction.
3. Weapon readability: ensure the bow attachment, authored rotation, string/limb silhouette, arrow origin, and release direction agree visually.
4. Impact language: use restrained ribbon/spark feedback and an authoritative hit response. A miss must remain visually distinct from a hit.
5. UI hierarchy: preserve the stock overworld HUD; add only a compact combat layer that does not cover minimap, quest, party, or skill information.
6. Environment support: use existing BowStage and Morning motifs to create a clean visual corridor for the shot. Add only small, reversible, scoped dressing where the frame needs depth or a readable background break.
7. Capture: produce a clean beauty frame, a gameplay frame with controls visible, and a hit-confirmation frame with HP change evidenced.

For every iteration, report:
- exact map and camera used;
- assets and systems reused;
- any per-instance overrides;
- what changed visually and why;
- the measured runtime result;
- screenshot or render path;
- remaining defects and their severity.

AAA acceptance bar:
- the player immediately understands aim, draw, release, travel, and hit;
- Melusina's face, hands, bow, and arrow origin remain readable at gameplay scale;
- the arrow travels along the aimed view ray and never appears backwards;
- the trail supports the arrow instead of hiding it;
- the target and HP response are readable without a large opaque panel;
- lighting, color, and contrast create a deliberate focal hierarchy;
- no runtime errors, Accessed None, ensure/assert, duplicate damage, or duplicate UI writer is introduced.
```

## Jev visual-director prompt

```text
Act as a constrained visual director. Review the supplied UE 5.8 screenshots, current source state, Figma FieldHUD reference, and runtime receipts. Choose one bounded presentation decision at a time.

Score each candidate on:
- hero silhouette clarity;
- bow/hand contact readability;
- target and projectile readability;
- composition at 16:9 gameplay scale;
- visual hierarchy;
- motion restraint;
- portfolio value;
- implementation risk;
- preservation of existing Melodia art direction.

Select one winner and one fallback. Do not invent new assets, paths, controls, or authorities. If the evidence is only source or editor evidence, label it SOURCE or EDITOR and hold promotion until real Morning PIE proof exists.

Prefer the smallest change that improves the frame materially. Reject larger panels, stronger bloom, excessive particles, camera shake, and decorative filigree when they reduce gameplay readability.

Return strict JSON with:
{
  "winner": "...",
  "fallback": "...",
  "confidence": 0.0,
  "evidence_level": "SOURCE|EDITOR|LIVE_PIE|SHOWCASE",
  "why": ["..."],
  "exact_parameters": {"...": "..."},
  "rejected_risks": ["..."],
  "next_smallest_action": "..."
}
```

## Melusina hero framing and pose prompt

```text
Polish the existing Melusina WaveHarp aim and release presentation in `L_MelusinaMorning`.

Use the canonical `BP_MelusinaJRPGCharacter` and `ABP_Melusina_Current`. Keep the existing draw montage and gameplay bow attack montage unless live evidence proves a specific defect. Start with a balanced shoulder camera around the existing player camera: approximately 320 cm arm length, a modest positive shoulder offset, and a soft 0.12–0.20 second handoff. Restore the exact original camera values when aim ends, sequence begins, possession changes, or the encounter is cancelled.

Inspect the frame at gameplay distance, not only close editor zoom. The face, torso, left hand, bow limbs, nocking hand, arrow shaft, and target must form one readable diagonal. Keep the bow away from the face and avoid cutting the head, hands, or arrow path at the viewport edge. Preserve manual aim truth: camera ray determines the projectile direction.

Use lighting and contrast before changing animation. If the pose still fails, identify the exact contact or silhouette defect with a frame and bone/socket measurement. Do not replace the ABP or import unverified mocap into the live character.

Deliver:
- neutral exploration frame;
- aim frame;
- held draw frame;
- release frame;
- frame with target in the shot corridor;
- one sentence describing the remaining pose defect, if any.
```

## WaveHarp arrow and Niagara trail prompt

```text
Polish the existing `AMelodiaWaveArrow` presentation without touching combat authority.

Use the existing WaveHarp R07 arrow mesh and verify its authored axis against the actor forward vector. The projectile must spawn outside Melusina, travel in the camera-aimed direction, use the existing collision component, carry the correct owner/instigator, and be destroyed after its single collision callback or lifetime expiry.

Use the existing `NS_ChoralSheep_MotionTrails` only as a per-arrow component asset. Keep the shared Niagara system unchanged. Start with a small world-space ribbon and restrained spark layer: low scale, moderate intensity, short visual persistence, and no screen-filling bloom. The arrow body must remain visible through the effect. The trail may disappear on collision; mechanics and hit proof must remain valid without it.

Tune in this order:
1. arrow visibility and silhouette;
2. ribbon width and lifetime;
3. spark count and brightness;
4. color relationship to WaveHarp and Morning lighting;
5. hit-only impact accent.

Reject trails that look like a sword slash, obscure the arrow, leave a permanent ribbon, or imply damage before collision.

Capture a clean travel frame and a collision frame. Log spawn transform, forward vector, velocity, owner, instigator, collision component, mesh, and one hit callback.
```

## Reactive combat HUD prompt

```text
Refine the WaveHarp combat overlay as a compact gameplay layer over the existing overworld HUD.

Match the verified Melodia FieldHUD direction: Inter typography, warm ivory/gold/plum palette, restrained borders, small rounded plates, and clear hierarchy. Preserve the stock minimap, quest card, party vitality, skill row, and rhythm owner. Do not replace the overworld HUD or add a second writer.

Use one small right-side combat card with:
- WAVEHARP or RHYTHM PHRASE state;
- five chord pips labelled C E G B C;
- a short actual-control line;
- compact target HP plate labelled with a presentation name, never an internal encounter ID;
- four-arm reticle;
- draw meter only while drawing;
- small authoritative hit marker and damage number only after world HP actually decreases.

Keep the card outside the minimap and party/skill row. Use generous text contrast and readable size at the actual capture resolution. Avoid full-width instruction bars, persistent center panels, flashing decoration, and grade claims when no grade callback was observed.

Test idle, aim, draw, release, miss, hit, sequence entry, sequence completion, cancel, and target death. UI feedback must never write HP or damage.
```

## Morning environment expansion prompt

```text
Expand the showcase frame inside the existing `L_MelusinaMorning` BowStage area without redesigning the level.

Use the authored BowStage props, Morning water/sky/foliage, existing light actors, and existing P0 composition. Build a shallow visual corridor from camera to target:
- foreground framing element with soft parallax;
- readable midground around Melusina's silhouette;
- uncluttered target lane;
- distant Morning depth cue;
- one subtle musical or water-reactive accent that supports the shot.

Prefer moving or instancing existing assets over importing new hero assets. Keep the target lane free of collision blockers and ensure new dressing cannot obscure the player, target, arrow, or HUD. Do not modify the tutorial encounter, PlayerStart, world GameMode, or durable outcome state without a scoped receipt.

The final frame should feel authored and expansive while still reading as gameplay. Avoid random scatter, excessive fog, heavy lens dirt, overbright bloom, or decorative objects that compete with Melusina.

Deliver a clean beauty capture and a gameplay capture from the same camera, plus a list of every actor or instance added/changed.
```

## Showcase camera and capture prompt

```text
Prepare a portfolio-quality capture of real WaveHarp play in `L_MelusinaMorning`.

Use the balanced gameplay camera first. Do not fake the arrow, hit, damage, or pose with an editor-only animation preview. Capture the actual possessed pawn in PIE.

Required sequence:
1. exploration idle with Morning environment visible;
2. aim with bow and target in one readable composition;
3. held draw with visible draw meter and clear hands;
4. release with arrow leaving the character;
5. travel frame with the arrow and restrained ribbon trail;
6. collision/hit frame with target HP reduced once;
7. return to exploration or sequence state without stranded input.

Use the same aspect ratio, resolution, and color-management settings for all frames. Keep debug overlays out of the beauty frame, but retain a separate evidence frame with controls and HP readable. Name files with map, state, and timestamp. Record the exact camera, viewport, engine version, source SHA, and runtime log path.

Do not call a render a showcase until the frame is both visually strong and tied to live PIE evidence.
```

## Final AAA QA and promotion prompt

```text
Act as the final visual and runtime gate for the Melusina WaveHarp showcase.

Inspect the fresh UE 5.8 build, Morning PIE captures, logs, and source diff. Verify:
- Melusina uses the canonical pawn and ABP;
- aim, draw, release, projectile travel, collision, stock damage, and HP change are one continuous path;
- the same encounter actor and HP remain through FLOW and SEQUENCE;
- the arrow is correctly oriented and does not spawn inside Melusina;
- the trail is presentation-only and does not hide the arrow;
- the compact HUD does not cover stock overworld UI;
- the camera restores after aim/cancel/sequence/possession;
- the target receives damage exactly once;
- no Accessed None, Blueprint Runtime Error, ensure/assert, duplicate outcome, or stale input context appears;
- no shared hero asset or environment authority was silently rewritten.

Return:
- PASS / HOLD;
- evidence paths;
- exact runtime errors, if any;
- visual defects ranked P0/P1/P2;
- one smallest next action.

Promotion requires LIVE_PIE evidence in Morning. Source presence, Figma context, Jev preference, editor preview, and CombatTrial proof are supporting evidence only.
```

