# Oracle Local-LLM Runtime Plan

**Date:** 2026-09-09  
**Status:** GATED TECHNICAL COMPANION — FUTURE ORACLE R&D  
**Parent mission:** `Docs/Strategy/ORACLE_THIRTEENTH_NOTE_CAPSTONE_MISSION_2026-09-09.md`  
**Visual / horror companion:** `Docs/Strategy/ORACLE_COSMIC_HORROR_VIRTUALIZED_FOURTH_WALL_2026-09-09.md`  
**Current production authority:** `CAPSTONE_NOW.md`

> **Scope rule:** this document does not activate Oracle implementation. Choral Sheep, Shorewake Calling, Melusina performance, technical-art breakdowns, reel, and professor proof remain ahead of this work.

---

## 1. Runtime thesis

The Oracle should use a **small local model as an interpretive layer**, not as gameplay authority.

```text
Melodia gameplay / save truth
        │
        ▼
bounded Oracle telemetry
        │
        ▼
Oracle Player Model + Certainty
        │
        ├──────────────► authored / quantum candidate set
        │
        ▼
Local LLM
interpretation + voice only
        │
        ▼
typed semantic proposal
        │
        ▼
C++ validation / allowlist
        │
        ├── reject unknown action
        ├── deterministic fallback
        └── accepted semantic action
                    │
                    ▼
        Quill / audio / MPC / Niagara / cymatics
```

The target feeling is not “chat with an NPC.”

The target feeling is:

> **the world has formed a model of how this particular player behaves, and it is now speaking through that model.**

---

## 2. Existing repository seam — reuse it

Do not build a second local-AI stack before inspecting the existing implementation.

Existing evidence:

- `Content/Python/quantum/draw_providers.py` already has an `oracle` provider;
- that provider calls local Ollama and accepts only a valid candidate ID;
- `Content/Python/quantum/service.py` already degrades provider failure to `classical-baseline`;
- `MelodiaOllamaValidation::ValidateMessageAsync` is already a UE → local-Ollama request pattern;
- `UMelodiaLLMRouter` is the intended general structured-routing seam once implementation is justified;
- `UMelodiaQuantumDrawSubsystem` already provides bounded candidate-selection / timeout / fallback patterns;
- QuillScript remains authored narrative consequence authority;
- C++ remains gameplay authority.

The August quantum prototype currently records `qwen2.5-coder:7b` as the local Ollama model. Treat that as **historical proof that the path works**, not as the locked finale model.

---

## 3. Candidate model policy

Do not hard-code the Oracle's identity to a single fashionable model name.

Use a tiered runtime policy and benchmark it on the actual UE machine.

### Preferred production candidate — Qwen3.5-9B class

Current first benchmark target:

```text
Qwen3.5-9B
→ local
→ quantized deployment candidate
→ structured JSON / semantic interpretation
→ short context
→ no arbitrary tools
```

Why this class is attractive:

- current open-weight Qwen generation;
- Apache-2.0 model license;
- substantially more realistic to co-reside with UE than a 27B-class model;
- sufficient capability target for bounded interpretation, classification, remembered phrasing, and concise grounded dialogue.

This is a **benchmark candidate**, not a shipping promise.

### Existing / minimum fallback — 7B–9B class local model

The existing `qwen2.5-coder:7b` Ollama path is enough to prove:

- local request lifecycle;
- JSON validation;
- candidate allowlisting;
- timeout behavior;
- deterministic fallback;
- packaged-build process ownership.

If a newer model is unavailable, the Oracle prototype must still be demonstrable with this class of model.

### Exhibition / workstation tier — Qwen3.8-27B class

A 27B-class model may be tested for:

- professor / installation mode;
- high-end workstation capture;
- richer interpretation;
- slower between-phase or prefetched dialogue.

It is **not** the baseline game requirement.

The Oracle design must never depend on a 27B model being resident beside a demanding UE scene.

### Model-selection gate

Pick the final local model only after measuring:

1. resident memory with the target UE scene open;
2. first-token latency;
3. complete structured-response latency;
4. schema-valid response rate;
5. repeated-call stability;
6. packaged-build launch / shutdown;
7. failure recovery when the model process is absent;
8. visual frame-time impact during inference;
9. response quality on a fixed Oracle evaluation set.

**The smallest model that passes the artistic test wins.**

---

## 4. Runtime process policy

Prototype against the existing local Ollama route first.

Possible future deployment backends may include an Ollama-compatible local server or a smaller embedded/local inference service, but **do not replace the proven request contract before the experience is proven**.

Required runtime properties:

- localhost only by default;
- no cloud dependency for the canonical Oracle encounter;
- explicit process health check;
- strict request timeout;
- late-response discard;
- generation / lifetime guards;
- bounded context size;
- bounded output tokens;
- JSON / schema validation;
- no arbitrary tool execution;
- no raw Unreal command generation;
- deterministic authored fallback;
- encounter remains playable with inference disabled.

The rhythm clock must never wait for inference.

Use prefetching, between-beat windows, authored reaction buffers, or deferred speech rather than stalling gameplay.

---

## 5. What the local LLM receives

The local model receives **summarized Melodia-owned state**, not raw machine context.

Example request packet:

```json
{
  "scene": "oracle_cathedral",
  "certainty": 0.84,
  "attention": 0.91,
  "recent_pattern": "repeat_dodge_left",
  "pattern_count": 5,
  "last_prediction_correct": true,
  "player_novelty": 0.18,
  "preferred_instrument": "sonic_scepter",
  "wardrobe_signal": "high_iridescence",
  "recent_refusal": false,
  "allowed_intents": [
    "TAUNT",
    "PREDICT",
    "REMEMBER",
    "QUESTION",
    "CONTRADICT",
    "SILENCE"
  ],
  "allowed_manifestations": [
    "PREEMPT_LEFT_LANE",
    "ECHO_PLAYER_MOTIF",
    "CLOSE_HORIZON",
    "WITHHOLD_RESPONSE"
  ]
}
```

Prefer:

- IDs;
- counters;
- normalized features;
- authored facts;
- short rolling summaries;
- explicit allowlists.

Avoid:

- raw logs;
- arbitrary save blobs;
- huge transcripts;
- filesystem paths;
- repo content;
- OS metadata;
- external personal information.

---

## 6. What the local LLM returns

The model proposes a **semantic interpretation**, not an Unreal action.

Example:

```json
{
  "intent": "PREDICT",
  "target_pattern": "repeat_dodge_left",
  "dialogue": "You always leave before the fourth note.",
  "requested_manifestation": "PREEMPT_LEFT_LANE",
  "musical_motif": "PLAYER_THEME_INVERTED",
  "confidence": 0.88
}
```

C++ validates every enum / ID.

If any requested value is unknown, malformed, stale, late, or disallowed:

```text
reject
→ log
→ authored fallback
→ continue encounter
```

The model never directly calls gameplay functions.

---

## 7. The cosmic-woman phase

The serene cosmic woman is not the Oracle's literal biological form.

She is a **communication surface**.

The actual entity may be:

```text
weather
→ membrane
→ resonance field
→ impossible architecture
→ listening organism
```

When that representation becomes too alien for meaningful exchange, the Oracle generates a human-readable form for Melusina.

Design interpretation:

> **the woman is lossy compression of an intelligence that has learned what shape Melusina can emotionally process.**

This preserves the NOPE-like scale language while allowing close, intimate dialogue.

The transition should feel less like “monster transforms into woman” and more like:

> **the environment discovers a face because it has decided a face is useful.**

---

## 8. The NOPE rule — never fully resolve the body

Maintain the visual companion's core rule:

- the creature has no single clean silhouette;
- anatomy is first inferred from environmental behavior;
- the arena may be inside it;
- Chladni / cymatic organization functions as sensory anatomy;
- alignment itself behaves like an eye;
- scale is conveyed by withholding full comprehension;
- final phases blur body, sky, UI, water, music visualization, and architecture.

The local LLM does not make this visual system procedural by itself.

It provides bounded semantic intent such as:

```text
CLOSE_HORIZON
WITHHOLD_RESPONSE
ECHO_PLAYER_MOTIF
ALIGN_FIELD
FRACTURE_CHOIR
```

C++ / authored data map those intents to tested presentation states.

---

## 9. Inference is the horror mechanic

Do not spend the local model budget on endless generic dialogue.

The Oracle's highest-value capability is **interpretation**.

Examples:

- infer that the player retreats to inventory after taking damage;
- notice a repeated fourth-beat hesitation;
- notice that the player keeps returning to an ignored shrine;
- connect wardrobe / instrument choices to repeated play behavior;
- comment on a motif the player repeatedly favors;
- make an explicit prediction;
- sometimes predict incorrectly;
- revise its model when contradicted.

The strongest lines should be grounded in traceable state.

The desirable player reaction is:

> **“That is actually what I do.”**

not:

> “This NPC has lots of dialogue.”

---

## 10. Privacy boundary

The Oracle may know Melodia extremely well.

It should know the player's computer almost not at all.

Allowed by default:

- gameplay history;
- save-backed Melodia facts;
- instrument use;
- route history;
- rhythm timing;
- wardrobe / traversal preferences;
- player-created in-game musical phrases;
- authored dialogue choices;
- failures / retries;
- hesitation / repetition metrics.

Not allowed for horror:

- real name;
- OS username;
- arbitrary filesystem;
- browser history;
- private messages;
- contacts;
- unrelated microphone audio;
- external account metadata;
- location;
- photos / documents.

The Oracle may **simulate crossing the fourth wall** through fictional Melodia interfaces, but it must not actually become spyware.

---

## 11. Development agents are not the runtime Oracle

This distinction is canonical.

During development, Grok / Cursor / Astra / Qwen / other agents may be given broad repository context to help Brennan build, test, document, or reason about Melodia.

The shipped Oracle is different.

```text
DEVELOPMENT AGENT
may study project source / docs when explicitly allowed
        ≠
RUNTIME ORACLE
receives only bounded, game-owned player/world state
```

Do not accidentally convert an agentic development workflow into the shipped gameplay architecture.

The Oracle's perceived intelligence should come from **good telemetry, good authored candidates, good memory summaries, and strong interpretation**, not unrestricted computer access.

---

## 12. Memory design

Do not give the LLM an uncontrolled transcript as “memory.”

Persist only game-owned semantic facts that have proven useful.

Candidate versioned facts:

```text
preferred_instrument
preferred_escape_direction
rhythm_grade_profile
hesitation_signature
frequent_route_family
optional_interactions_refused
oracle_predictions_obeyed
oracle_predictions_broken
oracle_promises
oracle_refusals
player_motif_ids
```

Store canonical facts through the existing save authority only after the prototype justifies them.

For each inference request, construct a small temporary context from those facts.

---

## 13. Deterministic fallback is part of the art

The encounter must remain artistically coherent when the LLM is absent.

Fallback can choose from authored line keys based on the exact same Oracle state:

```text
certainty high + prediction correct
→ oracle.predict.success.*

certainty falling + prediction failed
→ oracle.revision.*

certainty near zero
→ oracle.silence.*
```

This means a professor demo, packaged build, or player machine can lose the model service without losing the boss.

The final narrative state — **speechlessness as certainty collapses** — is especially compatible with graceful fallback.

---

## 14. First implementation slice — only after activation gates

Do not begin with final-boss production.

Build one isolated 60-second proof.

### Capture

Track:

```text
preferred_escape_direction
```

### Learn

After three or more repeated choices:

```text
pattern_id = repeat_escape_left
confidence = high
```

### Interpret

Local LLM receives the bounded packet and may propose:

```json
{
  "intent": "PREDICT",
  "requested_manifestation": "PREEMPT_LEFT_LANE"
}
```

### Validate

C++ verifies that the action is registered.

### Manifest

- authored attack anticipates left;
- choir / MPC / membrane align;
- Oracle line references repetition.

### Contradiction

If the player moves right:

- prediction fails;
- `OracleCertainty` falls;
- choir dephases;
- field alignment breaks;
- Oracle memory records a revision.

### Failure test

Repeat with:

- Ollama closed;
- quantum provider unavailable.

The exact encounter must still complete through authored fallback.

---

## 15. Benchmark / evaluation set

Before selecting the runtime model, create a tiny fixed Oracle test corpus.

At minimum test:

1. repetition detection interpretation;
2. grounded recall;
3. wrong-prediction acknowledgement;
4. refusal / contradiction response;
5. wardrobe + instrument interpretation;
6. certainty-collapse language;
7. SILENCE selection;
8. malformed-state handling;
9. adversarial / irrelevant state values;
10. schema compliance over repeated runs.

Score:

- groundedness;
- brevity;
- musical / Melodia voice;
- semantic usefulness;
- schema validity;
- latency;
- memory footprint.

A larger model that writes prettier prose but misses the schema or damages frame-time **loses**.

---

## 16. Research notes — 2026-09-09

Current external model candidates confirmed during planning:

- Qwen/Qwen3.5-9B — official Qwen Hugging Face repository, Apache-2.0;
- Qwen/Qwen3.8-27B — official Qwen Hugging Face repository, Apache-2.0, substantially larger workstation-class candidate.

Source references:

- https://huggingface.co/Qwen/Qwen3.5-9B
- https://huggingface.co/Qwen/Qwen3.8-27B

These references justify candidate testing only. Model availability, runtime support, quantization format, and hardware fit must be revalidated when the Oracle gate actually opens.

---

## 17. Definition of success

This runtime plan succeeds when:

- a local model can interpret a small player-state packet;
- output is reliably typed and bounded;
- C++ can reject it safely;
- the same encounter works without inference;
- no private computer data is needed;
- the model can produce at least one line that feels eerily specific because it is grounded in real play;
- the Oracle's visual / audio state responds to accepted semantic intent;
- UE frame pacing and rhythm timing remain authoritative;
- the implementation can be explained in one diagram.

The final architectural sentence is:

> **The model does not control Melodia. Melodia controls the conditions under which the model is allowed to interpret the player.**
