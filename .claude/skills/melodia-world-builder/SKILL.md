---
name: melodia-world-builder
description: Build, arrange, inspect, or polish Melodia Unreal worlds with live 3D scene awareness. Use for environment art, Sea Above, PCG biomes, worldbuilding, level composition, traversal readability, landmarks, cameras, scatter, procedural ecology, or any task that moves/adds/removes spatial content in UE5.8.
---

# Melodia world builder

Operational runbook for world / level / environment work. The goal is to make agents **spatially aware and fast**, not to add another planning layer.

## 0. Read only what the task needs

Always start with:

1. `CURRENT_STATE.md` — current truth / blockers / owner queue.
2. `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md` — world ownership.
3. `Docs/Production/PCG/README.md` when PCG/procedural ecology is involved.
4. the owner-named task / level / asset.

Do **not** begin with repo archaeology, old handoffs, or a broad documentation sweep.

If the experience can be authored through existing systems, author it. New architecture requires a demonstrated blocker.

## 1. 3D preflight — mandatory when the editor is available

Before the first spatial mutation, run:

```python
exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_snapshot.py").read())
```

Canonical tool:

`Content/Python/scene_context_snapshot.py`

It writes machine-local context under:

```text
Saved/Audit/SceneContext/<LevelName>/
  scene_context_latest.json
  viewport_latest.png
  top_latest.png
```

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

## 3. Work promptly

Preferred rhythm:

```text
owner intent
  -> scene snapshot
  -> inspect 3D relationships
  -> make the bounded change
  -> play / inspect / capture
  -> resnapshot
  -> compare
  -> stop
```

If you are three tool calls into a normal environment-art task and have not touched the requested scene/content, you are probably drifting.

Do not invent a framework because the level is messy. Use the existing pieces and improve the actual place.

## 4. Composition rules

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

If procedural output damages the frame, constrain the PCG bounds/density or remove the offending output rather than compensating with more effects.

Empty space is allowed and often desirable.

## 5. PCG / Resonance Ecology

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

## 6. Builder → falsifier, not permanent departments

For substantial 3D work, use two temporary roles:

**BUILDER**
- makes the requested bounded world change;
- preserves existing ownership;
- captures the result.

**FALSIFIER / REVIEWER**
- checks route clearance;
- player scale;
- landmark silhouette;
- negative space;
- PCG bounds/count regressions;
- duplicate ownership;
- saved/tracked asset provenance.

The reviewer fixes clear P0 defects but does not start a redesign campaign.

The owner decides whether the result actually looks or feels better.

## 7. Before / after spatial proof

After an edit, rerun `scene_context_snapshot.py` and compare the same anchors.

At minimum verify:

- route still reads and remains traversable;
- hero silhouettes are not buried;
- PCG did not invade exclusion/clear zones;
- scale still reads from a player camera;
- selected focal area improved from the same or comparable view;
- instance/bounds growth is intentional;
- no duplicate actor/PCG owner was accidentally created.

A technically valid graph mutation that worsens composition is a failed worldbuilding change.

## 8. World Partition / Git provenance

Unreal editor Save does not prove Git persistence.

For World Partition / ignored environment paths, finish by enumerating the intended changed `.uasset` and external-actor packages and verify that each is either:

- tracked/promoted deliberately; or
- intentionally machine-local.

Do not force-add an entire ignored content tree. Promote the exact intended packages.

## 9. Editor discipline

- Prefer the already-open target level. Do not load away from the owner's current level just to inspect another map.
- One editor-mutating surface at a time. Prefer Monolith when available.
- Do not run competing MCP/editor drivers on the same graph.
- PCG generation may be asynchronous; do not read counts immediately after `generate()` and call that evidence.
- Do not infer LIVE/PACKAGED success from source state.

## 10. Final response

Keep it production-facing:

- what changed in the world;
- which existing systems/graphs were reused;
- spatial proof / captures;
- PCG count/bounds impact if relevant;
- exact assets/external actors changed;
- evidence level actually achieved;
- one thing the owner should personally look at/play.

Do not create a new handoff/status/plan Markdown file.
