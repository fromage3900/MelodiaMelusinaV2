# Agent Build Contract — Melodia TouchDesigner

**THIS FILE IS AUTHORITATIVE FOR TD PERFORMANCE WORK.**

Before editing the show lane, read:
1. `MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md`
2. `MELODIA_SHOW_SYSTEM_ARCHITECTURE_2026-09-08.md`
3. `ACTUAL_LIVE_SHOW_PIPELINES_RESEARCH_2026-09-08.md`
4. `PIPELINE_RECIPES_CHORAL_SHEEP_2026-09-08.md`

Also read:
`../../Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md`

## MUST

- extend `grandmaster_melodia`;
- reuse existing audio/OSC semantic signals;
- build scenes as modular COMPs;
- expose stable named outputs;
- use Null CHOP/TOP hubs at module boundaries;
- provide reset and bypass;
- provide QUIET/rest state;
- keep live and replay modes semantically identical;
- externalize important networks to TDN after verified edits;
- capture evidence;
- test Perform Mode;
- report implemented vs planned honestly.

## MUST NOT

- create another global music clock;
- create another canonical chord/gameplay detector;
- open another OSC port because it is convenient;
- replace Unreal's gameplay/world authority;
- rewrite `/project1/audio` or `/project1/osc` wholesale;
- create a replacement grandmaster project;
- make generic rainbow/cyberpunk aesthetics;
- leave feedback permanently running without reset;
- leave bloom/glitch at full intensity globally;
- use raw audio as art direction;
- copy Ninajirachi/BABYMETAL/2hollis/PC Music branding;
- mark Spout/TouchEngine integration complete without project evidence;
- build the twelve-note flock before the C proof photographs well.

## First flagship scene

`/project1/performance/scenes/chladni_fleece`

Minimum proof:

```text
QUIET
→ pitch C
→ ROOT HIT
→ visible Chladni fleece field
→ decay
→ AFTERIMAGE
→ QUIET
```

## Visual acceptance

Reject if:
- sheep silhouette becomes unreadable;
- effect reads as generic VJ loop;
- full-spectrum rainbow dominates;
- there is no negative space;
- all layers pulse together;
- the image is more impressive paused on the node graph than on the final output.

## Technical acceptance

A scene is not complete until:
- input names documented;
- output names documented;
- reset tested;
- bypass tested;
- missing-input behavior tested;
- replay tested;
- performance checked;
- screenshot/video evidence recorded;
- TDN/source change committed.

## Scope

Capstone 01 priority:
1. C-note Chladni Fleece;
2. C/E/G shared field;
3. one world response;
4. final capture layers.

Everything else is backlog.
