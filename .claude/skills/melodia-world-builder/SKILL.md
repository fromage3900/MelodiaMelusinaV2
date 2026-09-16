---
name: melodia-world-builder
description: Build, arrange, inspect, or polish Melodia Unreal worlds with live 3D scene awareness. Use for environment art, Sea Above, PCG biomes, worldbuilding, level composition, traversal readability, landmarks, cameras, scatter, procedural ecology, or any task that moves/adds/removes spatial content in UE5.8.
---

# Melodia world builder

Operational runbook for world / level / environment work. The goal is to make agents **spatially aware, art-directed, measurable, and fast**, not to add another planning layer.

## 0. Read only what the task needs

Always start with:

1. `CURRENT_STATE.md` — current truth / blockers / owner queue.
2. `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md` — world ownership.
3. `Docs/Production/PCG/README.md` when PCG/procedural ecology is involved.
4. the owner-named task / level / asset.

Do **not** begin with repo archaeology, old handoffs, or a broad documentation sweep.

If the experience can be authored through existing systems, author it. New architecture requires a demonstrated blocker.

## 1. 3D preflight — mandatory when the editor is available

Before the first spatial mutation, establish a before state:

```python
exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_cycle.py").read()); begin()
```

This calls the canonical snapshot tool and writes machine-local context under:

```text
Saved/Audit/SceneContext/<LevelName>/
  scene_context_before.json
  viewport_before.png
  top_before.png
  scene_context_latest.json
  viewport_latest.png
  top_latest.png
```

Canonical tools:

- `Content/Python/scene_context_snapshot.py` — one compact live 3D awareness packet.
- `Content/Python/scene_context_cycle.py` — before/after packet + spatial diff.

These files are **ephemeral spatial evidence**, not project authority.

Inspect them immediately, then start work. A successful snapshot is not permission for another audit phase.

## 2. What the agent must understand before moving anything

From the packet and live editor, identify:

- current level and world bounds;
- current viewport / owner framing;
- selected actors;
- player-scale baseline;
- primary traversal route;
- protected negative space / landmark-clear areas;
- hero landmarks and major silhouettes;
- relevant PCG actors, graph paths, bounds and generated instance counts;
- route/exclusion tags: `WP_PrimaryRoute`, `WP_NoScatter`, `PCG_Exclude`, `WP_LandmarkClear`;
- the actual mesh/actor being changed, not merely a similarly named asset.

Never judge composition from actor names, graph names, or source code alone.

## 3. Measured art-direction build card — required for substantial 3D work

Before the first spatial mutation, convert the owner's intent into a **small measured build card** using the live scene data. Keep it in the active task/tool context or PR body; do **not** create a new plan Markdown file.

Use centimetres, metres, degrees, percentages, screen occupancy, instance counts, or explicit transform deltas instead of vague prose wherever a measurement is meaningful.

A good card contains only the dimensions relevant to the task:

```text
ART DIRECTION INTENT
- one sentence: what the player should feel/read

TARGET VIEW
- camera / viewport: named camera or live viewport transform
- FOV or focal length
- focal subject
- camera-to-subject distance
- desired subject screen occupancy / silhouette relationship

PLAYER ROUTE
- current clear width -> target clear width
- vertical clearance if relevant
- reveal / approach distance to the landmark
- intended turn, rise, drop, bridge, or path dimensions

COMPOSITION
- hero / support / background hierarchy
- protected negative-space zone or clearance radius
- foreground / midground / background separation distances
- intended overlap or silhouette separation in degrees / screen percentage where useful

PCG / ECOLOGY
- current volume bounds / graph owner
- current instance count -> target range or maximum delta
- exclusion margin from route / landmark
- density zones or falloff distances
- semantic response being emphasized

DIRECT EDITS
- actor/volume A: translate/rotate/scale by measured amount
- actor/volume B: bounds/density/seed/parameter target
- assets/graphs that must remain untouched

DONE WHEN
- same camera before/after proves the intended hierarchy
- route measurements remain valid
- PCG count/bounds change is intentional
- no protected clear zone is invaded
```

### Measurement rules

- **Measure first; do not invent precision.** Read current transforms/bounds/counts before stating them.
- If the owner gives art direction without numbers, choose **provisional working targets**, label them as such, and execute rather than asking for unnecessary clarification.
- The existing human-scale anchors (`300 cm` corridor width, `240 cm` clear height, `1200 cm` hall width) are useful baselines, not universal laws. Override them when the actual gameplay/camera requires it.
- Prefer deltas that can be falsified: `+850 cm Z`, `rotate 18° toward cathedral`, `shrink PCG X extent 12,000 -> 7,500 cm`, `instances 4,200 -> <=2,800`, not “move it up a bit” or “reduce density.”
- For hero composition, record the actual comparison camera. A beautiful change from a different camera is not proof of an improved composition.
- For PCG, always pair aesthetic intent with a spatial/instance budget. “More lush” without bounds/count guidance is incomplete.
- For negative space, define **what must remain empty and how much clearance it needs**.

The purpose is not bureaucracy. The build card should make the edit faster because the agent knows exactly what spatial result it is trying to produce.

## 4. Work promptly

Preferred rhythm:

```text
owner intent
  -> scene_context_cycle.begin()
  -> inspect 3D relationships
  -> write measured build card
  -> make the bounded change
  -> play / inspect
  -> scene_context_cycle.end()
  -> falsify measurements + captures
  -> stop
```

If you are three tool calls into a normal environment-art task and have not touched the requested scene/content, you are probably drifting.

Do not invent a framework because the level is messy. Use the existing pieces and improve the actual place.

## 5. Composition rules

PCG is an assembly tool, not the art director.

Prioritize:

1. traversal readability;
2. player scale;
3. focal hierarchy;
4. landmark silhouette;
5. negative space;
6. foreground / midground / background separation;
7. controlled procedural richness;
8. musical/world response.

Translate subjective direction into measurable constraints when possible. Examples: route width, camera distance/FOV, landmark reveal distance, clear-zone radius, angular separation, PCG bounds, instance-count budget, density falloff, and transform deltas.

If procedural output damages the frame, constrain the PCG bounds/density or remove the offending output rather than compensating with more effects.

Empty space is allowed and often desirable.

## 6. PCG / Resonance Ecology

Use the validated pipeline in `Docs/Production/PCG/README.md`:

```text
existing authored PCG points
  -> editor-only Python semantic enrichment
  -> native PCG assembly
  -> per-instance custom data
  -> material / Niagara presentation
```

For Sea Above and other chapters, prefer chapter-specific derivatives/wrappers. Do not destructively rewrite shared musical hero graphs.

Gameplay/music truth remains with existing runtime owners. Python is editor authoring infrastructure, not runtime authority.

Do not repurpose PCG density as semantic Resonance. Preserve upstream tags/transforms and use the proven metadata contract.

For every substantial PCG art pass, record before/after **graph owner, bounds, generated instance count, route/landmark exclusion distance, and the visual reason for the change**.

## 7. Builder → falsifier, not permanent departments

For substantial 3D work, use two temporary roles:

**BUILDER**
- makes the requested bounded world change against the measured build card;
- preserves existing ownership;
- captures the result.

**FALSIFIER / REVIEWER**
- reads `scene_context_diff.json` and before/after captures;
- checks each measurable target from the build card;
- checks route clearance;
- player scale;
- landmark silhouette;
- negative space;
- PCG bounds/count regressions;
- duplicate ownership;
- saved/tracked asset provenance.

The reviewer fixes clear P0 defects but does not start a redesign campaign.

The owner decides whether the result actually looks or feels better.

## 8. Before / after spatial proof

After the bounded edit, run:

```python
exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_cycle.py").read()); end()
```

This writes:

```text
scene_context_after.json
viewport_after.png
top_after.png
scene_context_diff.json
```

The diff records prioritized actors added/removed/moved, PCG graph or instance-count changes, world-bounds changes, viewport changes, and route/exclusion membership changes.

At minimum verify:

- the measured build-card targets were actually met or consciously revised;
- route still reads and remains traversable;
- hero silhouettes are not buried;
- PCG did not invade exclusion/clear zones;
- scale still reads from a player camera;
- selected focal area improved from the same or comparable view;
- instance/bounds growth is intentional;
- no duplicate actor/PCG owner was accidentally created.

A technically valid graph mutation that worsens composition is a failed worldbuilding change.

## 9. World Partition / Git provenance

Unreal editor Save does not prove Git persistence.

For World Partition / ignored environment paths, finish by enumerating the intended changed `.uasset` and external-actor packages and verify that each is either:

- tracked/promoted deliberately; or
- intentionally machine-local.

Do not force-add an entire ignored content tree. Promote the exact intended packages.

## 10. Editor discipline

- Prefer the already-open target level. Do not load away from the owner's current level just to inspect another map.
- One editor-mutating surface at a time. Prefer Monolith when available.
- Do not run competing MCP/editor drivers on the same graph.
- PCG generation may be asynchronous; do not read counts immediately after `generate()` and call that evidence.
- Do not infer LIVE/PACKAGED success from source state.

## 11. Final response

Keep it production-facing and measurable:

- what changed in the world;
- the measured art-direction targets used;
- actual before/after measurements and transform deltas;
- which existing systems/graphs were reused;
- before/after spatial proof / captures;
- PCG count/bounds impact if relevant;
- exact assets/external actors changed;
- evidence level actually achieved;
- one thing the owner should personally look at/play.

Do not create a new handoff/status/plan Markdown file.
