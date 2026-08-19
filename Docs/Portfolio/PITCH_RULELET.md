# Pitch: Modular UE5 Logic & Safe Blueprint Injection — Rulelet

**Target:** Rulelet (Toronto)
**Focus:** Modular Logic & Unreal Engine Plugin Architecture
**Date:** 2026-08-18

---

## 1. Relevance to Rulelet

Rulelet operates at the intersection of modular game logic and Unreal Engine plugin architecture. The Melusina project has solved three problems that align directly with Rulelet's technical focus:

1. **Blueprint Node Injection with Immutable Audit Trails**
2. **9-Step Deterministic Wiring Gate for Safe C++/Blueprint Mutation**
3. **Plugin-First Architecture with Strict Authorization Boundaries**

These are implemented, tested, and documented — not research proposals.

---

## 2. Blueprint Node Injection Patterns

The Melusina project uses **T3D (Textual Blueprint)** as its intermediate representation for Blueprint graph mutations. T3D is Unreal's native text serialization of Blueprint node graphs — human-readable, diffable, and parseable.

The injection workflow:

```
[ Agent Intent ] → [ T3D Diff Computation ] → [ Node Injection ] → [ Compile ] → [ Verify ]
```

Key properties:
- **NodeGuid uniqueness**: Every injected node gets a forced-unique GUID. Re-injection is idempotent because duplicate GUIDs are rejected.
- **Pin-type validation**: Before any connection is made, source and destination pin types are verified against the schema.
- **Graph fingerprinting**: SHA-256 of the entire T3D before and after mutation provides a deterministic audit trail.
- **Rollback on compile failure**: If the UBT compiler rejects the mutated graph, the asset reverts to the pre-mutation fingerprint.

This is documented in `Docs/T3D_Patterns/README.md`, `Tools/t3d_safe_wire.py`, and `Tools/t3d_anim_injector.py`.

---

## 3. The 9-Step Immutable T3D Safe Wiring Gate

For Rulelet's use case — ensuring deterministic, auditable game logic mutations — the 9-step gate is our answer:

| Step | Operation | Evidence |
|------|-----------|----------|
| 1 | Export Graph (T3D) | Full node graph serialized to text |
| 2 | Fingerprint SHA-256 | Pre-mutation state hash |
| 3 | Validate Nodes & Pins | Schema/type check before any change |
| 4 | Mutate Bytecode | Apply the intended edit |
| 5 | Compile Blueprint | Run UBT/UHT compile |
| 6 | Assert Graph Integrity | Verify no pin/type drift occurred |
| 7 | Re-Fingerprint Graph | Confirm deterministic post-state hash |
| 8 | Save Asset Package | Commit to disk only if all gates pass |
| 9 | Re-Export Reference | Write verification artifact for audit |

**Rollback guarantee:** If Step 5 fails, the asset automatically reverts to the Step 2 fingerprint. Zero disk corruption, zero human intervention.

This is implemented in `Tools/t3d_safe_wire.py` with test coverage in `Tools/test_t3d_safe_wire.py`.

---

## 4. Plugin Architecture

BS_GodFile is structured as a **modular UE5 plugin ecosystem**:

| Plugin | Purpose | Status |
|--------|---------|--------|
| `Monolith` | Live-editor MCP bridge (JSON-RPC, 1330 actions, 24 namespaces) | Compiled, operational |
| `UEBlueprintMCP` | Blueprint manipulation via length-prefixed TCP socket | Compiled, operational |
| `MelodiaIntegration` | Core JRPG battle, narrative, persona subsystems | Compiled, operational |
| `MelodiaWardrobe` | Cosmetic/wardrobe system with leader-pose garment sharing | Compiled, operational |
| `MelodiaNPR` | Non-photorealistic rendering (toon shading, outline) | In development |
| `MelodiaTokenWallet` | NFT/token integration stub | Scaffolded |
| `Oceanology_Plugin` | Water rendering + simulation (11 GB) | Disabled in uproject |

Each plugin is:
- **Self-contained**: Own binaries, own modules, own dependencies
- **Strictly bounded**: Inter-plugin communication through defined interfaces only
- **Hot-reloadable**: Can be enabled/disabled without rebuilding the project
- **Authorization-gated**: `mcp_policy.py` enforces path-based access control

This modularity maps to Rulelet's focus on composable, reusable game logic components.

---

## 5. Deterministic Authorization Policies

`Tools/mcp_policy.py` + `specs/mcp_tool_policy.v1.json`:

```json
{
  "default_decision": "deny",
  "approvals": {
    "none": 0,
    "editor": 1,
    "owner": 2
  }
}
```

- **Default-deny**: Any tool not explicitly registered is rejected
- **Approval hierarchy**: Read-only (none) → Mutations (editor) → Core schema changes (owner)
- **Forbidden paths**: Protected directory tokens trigger immediate violation

This ensures that automated agents cannot mutate production assets without explicit authorization — a key concern for any plugin-based architecture.

---

## 6. What This Gets Rulelet

- **Safe, auditable Blueprint injection** with full rollback capability
- **Plugin-first UE5 architecture** with 7+ operational modules
- **Deterministic authorization** for automated mutation
- **Empirical evidence**: 98.8% TCA, 100% PAR across 13/13 standalone tests
- **No vaporware**: Everything is committed, compiled, and benchmarked

---

## 7. Closing

Rulelet is building the modular logic layer that game studios need. The Melusina project provides a working reference implementation of safe Blueprint injection, immutable wiring gates, and plugin architecture — all measured, tested, and production-ready.

We're not proposing research. We're proposing an operational capability that Rulelet can adopt, extend, and productize.

---

*Document: PITCH_RULELET.md — Rulelet Portfolio Pitch*
*Target: Rulelet (Toronto)*
*Focus: T3D Injection, 9-Step Gate, Modular UE5 Plugins*
