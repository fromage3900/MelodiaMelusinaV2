# Houdini Licensing — Indie → Core / FX Transition Research

**Date:** 2026-08-30  
**Status:** licensing / production-risk research  
**Scope:** Melodia Melusina Houdini adoption, multi-PC use, Indie eligibility, commercial transition, Core-vs-FX feature risk  
**Not legal advice:** this document records current public SideFX licensing/product information and project implications. Re-check the current SideFX EULA and obtain written clarification from SideFX before relying on edge-case interpretations.

---

# Executive finding

The important distinction is **not**:

```text
Houdini Indie = cheap Core
Houdini Core = Indie without the revenue cap
```

SideFX's current product comparison instead states that **Indie, Education and Apprentice work like Houdini FX**, but use different file formats and have usage restrictions.

Therefore the practical transition is closer to:

```text
HOUDINI INDIE
$299/year
limited commercial
FX-like feature set
.hiplc / .hdalc
        |
        | Indie eligibility ends
        v
   choose commercial tier
        |
        +--> HOUDINI CORE
        |    unrestricted commercial use
        |    lower feature ceiling than FX/Indie
        |
        `--> HOUDINI FX
             unrestricted commercial use
             preserves the deeper FX feature set
```

This matters for Melodia because a future transition from Indie to Core can be a **feature downgrade**, not merely a licensing upgrade.

Primary SideFX references:
- https://www.sidefx.com/products/compare/
- https://www.sidefx.com/products/houdini-indie/
- https://www.sidefx.com/faq/indie-new/
- https://www.sidefx.com/faq/question/who-may-use-indie/

---

# 1. Current Indie eligibility

SideFX currently describes Houdini Indie as a **Limited Commercial** license.

## Individual commercial use

SideFX's current FAQ says an individual may use Indie commercially where financial consideration received directly or indirectly from use of the software is **less than $100,000 USD per year**.

## Organization use

SideFX's current public rules say an organization qualifies when:

```text
annual revenue < $100,000 USD
AND
funding received during previous 24 months < $1,000,000 USD
```

SideFX explicitly clarifies that an organization with **$100,000 USD or more of annual revenue** may not use Houdini Indie regardless of whether that revenue comes from Houdini.

SideFX also states that an eligible organization may use up to:

```text
3 Houdini Indie licenses
3 Houdini Engine Indie licenses
```

When the eligibility criteria are no longer met, SideFX says full commercial licenses are required for continued qualifying Houdini use.

References:
- https://www.sidefx.com/faq/question/who-may-use-indie/
- https://www.sidefx.com/faq/indie-new/
- https://www.sidefx.com/products/houdini-indie/

---

# 2. Indie is FX-like, not Core-like

SideFX's current comparison page explicitly says:

> Indie, Education and Apprentice work like Houdini FX but use different file formats and have restrictions to their usage.

This is strategically important.

While Indie eligibility remains valid, a solo developer has access to a feature set much closer to **FX** than Core.

A later move to Core can therefore remove access to some workflows that were available during Indie development.

Reference:
- https://www.sidefx.com/products/compare/

---

# 3. Core vs FX — capabilities that matter to Melodia

The following is a project-oriented reading of SideFX's current comparison matrix.

## Strong Core-safe territory

These are the areas most relevant to the current Melodia world-authoring plan and are broadly within Core's intended workflow:

```text
procedural modeling
SOP-based geometry workflows
terrain / HeightField-style workflows
attributes and geometry processing
Houdini Digital Assets
character / animation tooling
Solaris / USD layout
Copernicus
Karma rendering
Houdini Engine integration
procedural architecture
curve processing
instancing
mesh generation / processing
```

Therefore systems such as the following should not be assumed to require FX:

```text
MIDI_WORLD_GRAMMAR
procedural architecture generation
terrain semantic masks
curve-driven paths / rivers / structure
attribute-driven world metadata
modular geometry generation
basic Monolith influence geometry
HDA-driven Unreal authoring
```

## Core simulation limitation

SideFX currently exposes several simulation families to Core through **Geometry/SOP-level tools**.

The comparison page specifically describes Core access at the Geometry/SOP level for areas including:

```text
Pyro FX
Fluids
Rigid Bodies
Crowds
Muscles / Vellum
Vellum Cloth
Hair / Fur / Feathers
Clouds
Wire Dynamics
```

These high-level tools can internally contain DOP networks.

However SideFX states that when those higher-level tools are insufficient and the artist wants to work with **DOP nodes directly**, **Houdini FX is required**.

That distinction matters for highly customized simulation-driven world generation.

Reference:
- https://www.sidefx.com/products/compare/

---

# 4. Clear FX-risk areas for Melodia

Do not assume the following can be reproduced with the same depth in Core without testing.

## Direct DOP authoring

Custom low-level Dynamics Operator networks require FX according to SideFX's comparison guidance.

Potential Melodia relevance:

```text
custom Faraway Mother cloth-landscape solvers
custom God That Molts destruction / shedding solvers
bespoke water-organism interactions
procedural physical processes that exceed packaged SOP solvers
custom simulation HDAs authored from low-level DOP networks
```

## MPM

The current SideFX comparison places MPM outside Core's full feature set and inside the FX-like tier.

Potential Melodia relevance:

```text
snow / sand / mud-like deformable materials
organic granular masses
material-state transformations
large-scale soft / granular Monolith interactions
```

Do not design a production-critical system around MPM until its commercial-license requirement is deliberately accepted.

## PDG / TOPs distribution

SideFX's current comparison lists:

```text
Core: PDG | Tasks — Local Only
```

This is especially significant for a future multi-PC solo production farm.

A system such as:

```text
                  PDG
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
terrain jobs   geometry jobs   cache jobs
PC A           PC B            PC C
```

must not be assumed to remain available with the same distributed-production capability under Core.

For Melodia, **PDG distribution is an FX-risk feature** and should be tracked as such.

Reference:
- https://www.sidefx.com/products/compare/

---

# 5. Proposed project classification: CORE_SAFE vs FX_REQUIRED / FX_RISK

Every Houdini production experiment should record a licensing portability field.

Recommended values:

```text
CORE_SAFE
FX_RISK
FX_REQUIRED
UNKNOWN_VERIFY
```

Example:

| System | Initial classification | Reason |
|---|---|---|
| MIDI_WORLD_GRAMMAR SOP/HDA | CORE_SAFE | procedural geometry / attributes / HDA |
| Monolith influence SDF geometry | CORE_SAFE | geometry / field processing unless advanced sim enters |
| Region-history geometry compiler | CORE_SAFE | primarily deterministic procedural construction |
| Unreal HDA integration | CORE_SAFE | commercial Core/FX Engine-compatible workflow |
| Basic Vellum SOP workflow | CORE_SAFE_WITH_LIMITS | higher-level SOP tools available; test exact needs |
| Custom low-level Vellum/DOP solver | FX_REQUIRED | direct DOP authoring |
| MPM-driven world system | FX_REQUIRED / VERIFY_CURRENT | current comparison places MPM in FX-like feature set |
| Local PDG orchestration | CORE_SAFE_WITH_LIMITS | Core currently lists PDG tasks as Local Only |
| Distributed PDG farm | FX_RISK | Core's Local Only limitation conflicts with intended use |

The classification must be based on an actual prototype and current SideFX documentation, not assumptions.

---

# 6. Current public pricing snapshot — 2026-08-30

**Pricing changes over time. Re-check before purchase.**

SideFX's current comparison page lists:

## Houdini Indie

```text
$299 USD / year
$449 USD / 2 years
```

Limited Commercial; Indie eligibility rules apply.

## Houdini Core — commercial

```text
Annual Workstation rental:       $1,475 USD
Perpetual Workstation:           $1,995 USD
Annual Upgrade Plan:             $1,095 USD
Annual Local Access rental:      $2,195 USD
Monthly Local Access rental:       $370 USD
```

## Houdini FX — commercial

```text
Annual Workstation rental:       $3,505 USD
Perpetual Workstation:           $4,495 USD
Annual Upgrade Plan:             $2,740 USD
Annual Local Access rental:      $5,480 USD
Monthly Local Access rental:       $910 USD
```

## Houdini Engine — commercial

```text
Annual Workstation:                $525 USD
Floating / GAL starts at:          $795 USD annually
```

Reference:
- https://www.sidefx.com/products/compare/

The commercial transition should therefore be understood as a feature/cost decision, not as a fixed "$100K means pay exactly X" rule.

---

# 7. Crossing the Indie threshold does not mean SideFX takes a revenue percentage

The public SideFX model is an **eligibility cutoff**, not a royalty.

The project should not describe the rule as:

```text
make $100K -> SideFX takes money from revenue
```

The more accurate production statement is:

```text
cease satisfying Indie eligibility
        |
        v
Indie may no longer be used for qualifying commercial work
        |
        v
continued Houdini commercial authoring requires an appropriate commercial license
```

The exact transition timing and treatment of existing projects should be checked against the then-current EULA and confirmed in writing with SideFX before a threshold-crossing event.

---

# 8. Indie file-format boundary

SideFX currently documents separate Indie formats:

```text
scene: .hiplc
asset: .hdalc
```

Commercial Core/FX use normal commercial formats such as:

```text
scene: .hip
asset: .hda
```

SideFX also states that Indie cannot be used in the same pipeline as commercial versions of Houdini.

References:
- https://www.sidefx.com/products/compare/
- https://www.sidefx.com/products/houdini-indie/
- https://www.sidefx.com/faq/question/indie-restrictions/

## Project implication

Do not assume that purchasing Core/FX later automatically converts all Indie source artifacts or removes every pipeline restriction.

Before a commercial transition:

```text
1. inventory .hiplc / .hdalc source assets
2. identify which generators still require editing
3. identify what has already been baked/exported
4. contact SideFX with the exact project situation
5. obtain written transition/conversion guidance
6. test the transition on copies before changing production
```

Do not build a migration strategy from forum anecdotes.

---

# 9. Multi-PC Indie use — important distinction

There are **two different concepts** that must not be conflated.

## Supplementary second Indie license

SideFX says an Indie purchase includes a supplementary license for a second computer / laptop or dual boot, but use of the two licenses is restricted to a **single artist**, who may use Houdini Indie on only one of those computers at a time.

Reference:
- https://www.sidefx.com/products/houdini-indie/

That supplementary entitlement is **not** permission to run two interactive Indie sessions concurrently for one artist.

## Engine Indie farm nodes

Separately, SideFX says eligible Indie users may obtain up to **3 Houdini Engine Indie licenses**.

SideFX explicitly documents Engine Indie as able to:

```text
run command-line renders on remote machines
run simulations on remote machines
load HDAs through supported host integrations
```

and states that the maximum three Engine Indie licenses means Engine Indie may run on **3 farm machines**.

References:
- https://www.sidefx.com/faq/question/houdini-engine-indie/
- https://www.sidefx.com/faq/question/indie-renderfarm-setup/
- https://www.sidefx.com/products/houdini-engine/

Therefore a legitimate Indie-era solo setup can conceptually be:

```text
MAIN AUTHORING PC
Houdini Indie GUI
        |
        +--> FARM PC 1 — Engine Indie
        +--> FARM PC 2 — Engine Indie
        `--> FARM PC 3 — Engine Indie
```

Exact job orchestration and solver/license requirements must still be tested against the specific workload.

---

# 10. Commercial Unreal/Unity Engine licenses are a separate advantage

For commercial Core/FX customers, SideFX currently offers a free **Houdini Engine for Unity/Unreal** license specifically for those plugins.

SideFX states that this free commercial license:

```text
works with commercial .HDA assets
supports the UE5 plugin
supports the Unity plugin
does not provide the Houdini GUI
does not provide general farm batch processing
```

SideFX says up to 10 can be obtained per studio through the website, with additional licenses available by contacting an account manager.

References:
- https://www.sidefx.com/faq/question/houdini-engine-plugin-free-for-unity-and-unreal/
- https://www.sidefx.com/faq/question/what-houdini-engine-license-do-i-need/
- https://www.sidefx.com/products/houdini-engine/

## Melodia implication

A future commercial workflow does **not** necessarily require purchasing a full Core/FX GUI license for every Unreal workstation.

Possible architecture:

```text
AUTHORING PC
Core or FX commercial
        |
        | commercial .HDA
        v
repository / shared storage
        |
  +-----+-----+
  |           |
  v           v
UE PC 2      UE PC 3
free         free
commercial   commercial
Engine UE    Engine UE
```

However paid Houdini Engine remains relevant for general batch processing, farm processing, Maya/Max integrations, custom HAPI use, and similar non-free-plugin workloads.

---

# 11. Why Core cannot automatically be treated as the future answer

For Melodia, Core is attractive because it removes Indie eligibility restrictions while retaining a large procedural modeling / environment toolset.

But choosing Core purely because it is cheaper can create a future capability mismatch.

Before committing to Core, answer:

```text
Does the production pipeline require direct DOP authoring?
Does it require MPM?
Does it require distributed PDG rather than local TOP work?
Does it depend on any other FX-only solver/control path?
```

If **no**, Core may be sufficient and substantially cheaper.

If **yes**, FX may be the actual commercial continuation of the Indie workflow.

This must be measured from real Melodia production, not predicted from feature names.

---

# 12. What to learn while Indie-eligible

Do **not** artificially restrict learning to Core-compatible features.

Indie currently exposes the FX-like feature set. Use that period to discover which capabilities actually matter.

Recommended learning / prototype order:

```text
SOPs
attributes
VEX
curves / surfaces
HeightFields / terrain
HDAs
Houdini Engine + Unreal
TOPs / PDG
Vellum
DOP fundamentals
MPM only if a Melodia-shaped use case appears
```

For every prototype, record:

```text
feature used
Core-safe? yes/no/unknown
FX-only dependency?
distributed Engine requirement?
can result be baked?
can UE/Blender reproduce the final operation if needed?
```

The goal is not to avoid FX features. The goal is to know the future cost of every production-critical dependency.

---

# 13. Melodia Houdini adoption policy after this research

The correct project decision is **not** "avoid Houdini because licensing is annoying" and not "adopt Houdini everywhere because Indie is cheap."

Use a value test:

> **A Houdini dependency is justified when the development time it saves or the capability it unlocks is worth its current and plausible future licensing cost.**

For each major Houdini system, track:

```text
TIME_SAVED_ESTIMATE
CORE_SAFE / FX_RISK / FX_REQUIRED
BAKEABLE_OUTPUT
REGENERATION_FREQUENCY
UNREAL_RUNTIME_DEPENDENCY
MULTI_PC_VALUE
MIGRATION_COST
```

A generator that saves hundreds of hours may rationally justify a commercial FX seat later.

A generator that saves a few hours but creates a permanent FX-only dependency probably does not.

---

# 14. Recommended immediate experiment labels

## MIDI_WORLD_GRAMMAR

```text
Licensing target: CORE_SAFE
Reason: SOP/attribute/HDA procedural geometry
FX escalation: none expected for v1
```

## MONOLITH_INFLUENCE

```text
Licensing target: CORE_SAFE
Reason: geometry fields, attributes, curves, terrain masks
FX escalation: if simulation becomes authoritative rather than generated geometry
```

## REGION_HISTORY

```text
Licensing target: CORE_SAFE initially
Reason: deterministic procedural transformation / task graph
FX escalation: distributed PDG farm or simulation-heavy historical layers
```

## FARAWAY_MOTHER_CLOTH_WORLD

```text
Licensing target: UNKNOWN_VERIFY
Core path: high-level Vellum SOP tools may be sufficient
FX escalation: custom direct DOP network / bespoke solver construction
```

## GOD_THAT_MOLTS_MATERIAL_SIM

```text
Licensing target: FX_RISK
Core path: authored geometry + packaged SOP simulations
FX escalation: custom destruction / material dynamics / MPM
```

## MULTI_PC_WORLD_COOK_FARM

```text
Indie phase: Engine Indie can support up to 3 remote farm machines
Commercial Core: do not assume distributed PDG parity; Core currently lists PDG as Local Only
Commercial FX: evaluate if distributed PDG is the critical value
```

---

# 15. Threshold-transition checklist

If Melodia or the relevant organization approaches Indie ineligibility, do not improvise.

At approximately 70–80% of the applicable threshold, perform a formal licensing review.

Prepare this exact inventory:

```text
legal operating structure
current annual revenue
current funding during previous 24 months
Houdini Indie seat count
Engine Indie node count
.hiplc files in active production
.hdalc files in active production
baked/exported Houdini outputs
Unreal Engine plugin usage
PDG / TOP usage
farm/batch usage
Core-only compatibility tests
FX-only dependency list
```

Send SideFX a concise description and request written clarification on:

```text
exact eligibility transition date
required commercial tier for the described workflow
Indie-source conversion / migration procedure
existing baked-output treatment
Engine licensing for Unreal workstations
Engine licensing for farm/batch nodes
PDG distributed-processing requirements
```

Archive SideFX's written response in project operations documentation.

---

# 16. Sources — official SideFX only

Primary sources checked 2026-08-30:

- Product comparison / features / current pricing  
  https://www.sidefx.com/products/compare/

- Houdini Indie product page  
  https://www.sidefx.com/products/houdini-indie/

- Indie FAQ  
  https://www.sidefx.com/faq/indie-new/

- Who may use Houdini Indie?  
  https://www.sidefx.com/faq/question/who-may-use-indie/

- Indie restrictions  
  https://www.sidefx.com/faq/question/indie-restrictions/

- Houdini Engine Indie  
  https://www.sidefx.com/faq/question/houdini-engine-indie/

- Indie render farm setup  
  https://www.sidefx.com/faq/question/indie-renderfarm-setup/

- Houdini Engine product page  
  https://www.sidefx.com/products/houdini-engine/

- Houdini Engine licensing  
  https://www.sidefx.com/faq/question/how-does-houdini-engine-licensing-work/

- Which Houdini Engine license is needed?  
  https://www.sidefx.com/faq/question/what-houdini-engine-license-do-i-need/

- Free commercial Engine plugin for Unreal / Unity  
  https://www.sidefx.com/faq/question/houdini-engine-plugin-free-for-unity-and-unreal/

---

# Bottom line

For Melodia, the licensing risk is specific and measurable:

```text
Indie gives FX-like capability cheaply
        |
        v
successful commercial use may end Indie eligibility
        |
        +--> Core is cheaper but can remove deep FX / distributed capabilities
        |
        `--> FX preserves the deeper feature ceiling at much higher cost
```

The correct engineering response is therefore:

> **Prototype freely while eligible, but label every production-critical Houdini dependency as CORE_SAFE, FX_RISK, FX_REQUIRED, or UNKNOWN_VERIFY before it becomes expensive to replace.**

This preserves the actual advantage of Houdini while preventing a future license-tier transition from becoming an unexpected production surprise.
