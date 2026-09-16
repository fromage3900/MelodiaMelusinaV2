## Description

<!-- What does this PR do? Keep it scoped. -->

## Player / artist outcome

<!-- What visible, playable, presentable, safety, or concrete blocker outcome does this enable? Prefer the experienced result over implementation trivia. -->

## Content-first decision

<!-- Melodia now has a stable gameplay + procedural/art vocabulary. Start by composing with it. -->

- [ ] I checked `CURRENT_STATE.md` → Proven Creative Capability Surface / What To Reach For
- [ ] This request can be expressed using existing owners/tools, and this PR does that
- [ ] OR: architecture/tooling changes are required because of the concrete blocker written below
- [ ] This PR does not reopen a settled system merely because an older branch/doc contains another implementation

**Existing capability reused:**
<!-- e.g. Quill + Phoenix/JRPG + rhythm seam; Wardrobe; UE PCG/Python; Houdini/Hython/Copernicus; cymatics/materials; Niagara; melodia-ui-artist -->

**Architecture blocker (write `N/A — content-only` when none):**
<!-- Name the specific missing seam/invariant. “It would be cleaner” is not a blocker. -->

## Authority touched

- [ ] Authored gameplay/content only (preferred default)
- [ ] C++ / gameplay truth
- [ ] Blueprint / presentation wiring
- [ ] Unreal material / Niagara / art content
- [ ] UE PCG / Python world authoring
- [ ] Houdini / Hython / Copernicus / HDA
- [ ] Blender / Geometry Nodes / DCC
- [ ] UI via existing `melodia-ui-artist` workflow
- [ ] TouchDesigner / AE presentation
- [ ] Documentation / discovery only
- [ ] Tooling / CI / repository governance

## Evidence level

Highest level actually supported by this PR:

- [ ] SOURCE PRESENT
- [ ] SOURCE BUILT
- [ ] LIVE PROVEN
- [ ] RESTART PROVEN
- [ ] PACKAGED PROVEN
- [ ] PORTFOLIO APPROVED
- [ ] Not applicable / documentation-only

## Creative-system reuse

<!-- Check every existing production lane this work composes with. Empty here should be unusual for new player-facing work. -->

- [ ] QuillScript / chapter scaffold / stable IDs
- [ ] Phoenix / TurnBased JRPG authority
- [ ] Existing rhythm execution / skills
- [ ] Wardrobe / traversal / Convergence
- [ ] Music-as-key / world consequence
- [ ] UE PCG / Resonance Ecology / Python
- [ ] Houdini Engine / Hython / Copernicus
- [ ] Cymatics / Chladni / material-MPC stack
- [ ] Niagara / flipbook / audio-reactive presentation
- [ ] Existing UI tokens / `melodia-ui-artist`
- [ ] None — infrastructure-only; justification above

## Visual / reference impact

- [ ] No owner-approved visual target changed
- [ ] Choral Sheep work read `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`
- [ ] Any changed visual authority is explicitly documented and owner-directed
- [ ] LFS / binary impact has been checked

## Branch / provenance

- [ ] Branch purpose is understood
- [ ] This is not a wholesale WORKSTATION / RECOVERY merge
- [ ] Salvaged work identifies its source branch/path
- [ ] No intentional operational/workstation branch is being deleted for branch-count aesthetics

## Cleanup justification

<!-- Required for cleanup/refactor/hygiene PRs. Name the concrete blocker, integrity risk, or discoverability failure. Write "N/A" otherwise. -->

## Checklist

- [ ] Read `CURRENT_STATE.md`
- [ ] Chose content composition before architecture where the existing stack can express the experience
- [ ] Changes are focused and do not expand scope unnecessarily
- [ ] Required local/static validation was run where applicable
- [ ] If project status changed, `CURRENT_STATE.md` is updated in this PR — no new handoff, plan, receipt, or session-note files
- [ ] No unrequested cleanup was bundled into feature work
- [ ] No `.blend1`, `Intermediate/`, temp, secret, or accidental generated files are committed
