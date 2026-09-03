---
name: unreal-gas
description: Use when working with Unreal Engine Gameplay Ability System (GAS) via Monolith MCP — creating and editing abilities, attribute sets, gameplay effects, ASC setup, gameplay tags, gameplay cues, targeting, input binding, runtime inspection, and project scaffolding. Triggers on GAS, ability, attribute, gameplay effect, gameplay tag, gameplay cue, ASC, ability system, cooldown, modifier, stacking, ability task.
---

# Unreal GAS Workflows

**130 GAS actions** across 10 categories via `gas_query()`. Discover first: `monolith_discover({ namespace: "gas" })`

## Key Parameters

- `asset_path` — Blueprint or asset path (NOT `asset`)
- `attribute_set` — attribute set asset path
- `effect_path` / `ability_path` — GE or GA asset path
- `tag` — gameplay tag string (e.g., `"Ability.Combat.Attack"`)
- `template` — template name from `list_templates`

## Action Reference

### Abilities (28)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_ability` | `save_path`, `parent_class`?, `ability_name`? | Create GA Blueprint |
| `get_ability_info` | `asset_path` | Read tags, costs, cooldowns, flags |
| `list_abilities` | `path_filter`?, `tag_filter`? | List all GA assets |
| `compile_ability` | `asset_path` | Compile GA Blueprint |
| `set_ability_tags` | `asset_path`, `tags` | Set cancel, block, owned, required tags |
| `get_ability_tags` | `asset_path` | Read all tag containers |
| `set_ability_policy` | `asset_path`, `instancing`?, `net_execution`? | Set instancing/net policies |
| `set_ability_cost` | `asset_path`, `effect_path` | Assign cost GE |
| `set_ability_cooldown` | `asset_path`, `effect_path` | Assign cooldown GE |
| `set_ability_triggers` | `asset_path`, `triggers` | Configure trigger events |
| `set_ability_flags` | `asset_path`, flags | Server-only, retry on fail, etc. |
| `add_ability_task_node` | `asset_path`, `task_class`, `graph_name`? | Add Ability Task node |
| `add_commit_and_end_flow` | `asset_path`, `graph_name`? | Scaffold CommitAbility->logic->EndAbility |
| `add_effect_application` | `asset_path`, `effect_class`, `target`? | Add ApplyGE node |
| `add_gameplay_cue_node` | `asset_path`, `cue_tag`, `type`? | Add ExecuteGameplayCue node |
| `create_ability_from_template` | `save_path`, `template` | Create from preset |
| `build_ability_from_spec` | `save_path`, `spec` | Declarative one-shot builder |
| `batch_create_abilities` | `abilities` | Create multiple at once |
| `duplicate_ability` | `asset_path`, `new_path` | Duplicate |
| `list_ability_tasks` | `class_filter`? | Available AT classes |
| `get_ability_task_pins` | `task_class` | AT input/output pins |
| `wire_ability_task_delegate` | `asset_path`, `task_node_id`, `delegate_name`, `target_node`? | Wire AT delegate |
| `get_ability_graph_flow` | `asset_path`, `graph_name`? | Trace execution flow |
| `validate_ability` | `asset_path` | Lint: missing cost, orphaned tasks, tag conflicts |
| `find_abilities_by_tag` | `tag`, `match_type`? | Find by tag |
| `get_ability_tag_matrix` | `path_filter`? | Cross-reference tag usage |
| `validate_ability_blueprint` | `asset_path` | Deep validation: graph, tasks, delegates |
| `scaffold_custom_ability_task` | `save_path`, `task_name`, `delegates`?, `params`? | Scaffold custom AT |

### Attributes (20)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_attribute_set` | `save_path`, `parent_class`?, `attributes`? | Create Attribute Set |
| `add_attribute` | `asset_path`, `attribute_name`, `type`?, `default`? | Add attribute |
| `get_attribute_set` | `asset_path` | Read attributes, defaults, clamping |
| `set_attribute_defaults` | `asset_path`, `defaults` | Set defaults |
| `list_attribute_sets` | `path_filter`? | List all |
| `configure_attribute_clamping` | `asset_path`, `attribute`, `min`?, `max`?, `clamp_source`? | Set clamping |
| `configure_meta_attributes` | `asset_path`, `meta_attribute`, `target_attribute`, `operation` | Meta attribute for damage/heal |
| `create_attribute_set_from_template` | `save_path`, `template` | From preset |
| `create_attribute_init_datatable` | `save_path`, `attribute_set`, `rows`? | DataTable for init |
| `duplicate_attribute_set` | `asset_path`, `new_path` | Duplicate |
| `configure_attribute_replication` | `asset_path`, `attribute`, `replicate`?, `condition`? | Set replication |
| `link_datatable_to_asc` | `asc_asset`, `datatable_path` | Link init DataTable to ASC |
| `bulk_edit_attributes` | `asset_path`, `edits` | Edit multiple |
| `validate_attribute_set` | `asset_path` | Lint: orphans, clamping, replication |
| `find_attribute_modifiers` | `attribute` | Find all GEs modifying attribute |
| `diff_attribute_sets` | `asset_path_a`, `asset_path_b` | Compare two sets |
| `get_attribute_dependency_graph` | `asset_path` | Map dependencies |
| `remove_attribute` | `asset_path`, `attribute_name` | Remove |
| `get_attribute_value` | `actor_path`, `attribute` | Read runtime value (PIE) |
| `set_attribute_value` | `actor_path`, `attribute`, `value` | Set runtime value (PIE) |

### Effects (26)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_gameplay_effect` | `save_path`, `duration_policy`?, `parent_class`? | Create GE |
| `get_gameplay_effect` | `asset_path` | Read modifiers, duration, stacking, components |
| `list_gameplay_effects` | `path_filter`?, `duration_filter`? | List all |
| `add_modifier` | `asset_path`, `attribute`, `operation`, `magnitude`? | Add modifier |
| `set_modifier` | `asset_path`, `index`, `attribute`?, `operation`?, `magnitude`? | Edit modifier |
| `remove_modifier` | `asset_path`, `index` | Remove modifier |
| `list_modifiers` | `asset_path` | List modifiers |
| `add_ge_component` | `asset_path`, `component_class`, `config`? | Add GE Component (5.3+) |
| `set_ge_component` | `asset_path`, `component_index`, `config` | Edit GE Component |
| `remove_ge_component` | `asset_path`, `component_index` | Remove GE Component |
| `set_effect_stacking` | `asset_path`, `type`, `limit`?, `duration_refresh`?, `period_reset`? | Configure stacking |
| `set_duration` | `asset_path`, `policy`, `duration`? | Set duration policy |
| `set_period` | `asset_path`, `period`, `execute_on_apply`? | Set periodic execution |
| `create_effect_from_template` | `save_path`, `template` | From preset |
| `build_effect_from_spec` | `save_path`, `spec` | Declarative one-shot builder |
| `batch_create_effects` | `effects` | Create multiple |
| `add_execution` | `asset_path`, `execution_class` | Add Execution Calculation |
| `duplicate_gameplay_effect` | `asset_path`, `new_path` | Duplicate |
| `delete_gameplay_effect` | `asset_path` | Delete |
| `validate_effect` | `asset_path` | Lint: missing attrs, stacking conflicts |
| `get_effect_interaction_matrix` | `path_filter`? | Cross-reference GE interactions |
| `get_active_effects` | `actor_path` | List active GEs (PIE) |
| `get_effect_modifiers_breakdown` | `asset_path` | Detailed modifier analysis |
| `apply_effect` | `actor_path`, `effect_path`, `level`? | Apply at runtime (PIE) |
| `remove_effect` | `actor_path`, `handle` | Remove active GE (PIE) |
| `simulate_effect_stack` | `effect_path`, `count`?, `base_value`? | Simulate stacking without PIE |

### ASC Setup (14)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `add_asc_to_actor` | `asset_path`, `component_class`? | Add ASC to Blueprint |
| `configure_asc` | `asset_path`, `replication_mode`?, `avatar_actor`? | Configure ASC |
| `setup_asc_init` | `asset_path`, `init_location`? | Scaffold InitAbilityActorInfo |
| `setup_ability_system_interface` | `asset_path` | IAbilitySystemInterface (C++ only) |
| `apply_asc_template` | `asset_path`, `template` | Apply ASC template (player/AI/boss) |
| `set_default_abilities` | `asset_path`, `abilities` | Abilities granted on init |
| `set_default_effects` | `asset_path`, `effects` | Effects applied on init |
| `set_default_attribute_sets` | `asset_path`, `attribute_sets` | Attribute sets created on init |
| `set_asc_replication_mode` | `asset_path`, `mode` | Full/Minimal/Mixed |
| `validate_asc_setup` | `asset_path` | Lint: missing interface, init, avatar |
| `grant_ability` | `actor_path`, `ability_class`, `level`? | Grant at runtime (PIE) |
| `revoke_ability` | `actor_path`, `ability_class` | Revoke at runtime (PIE) |
| `get_asc_snapshot` | `actor_path` | Full ASC state dump (PIE) |
| `get_all_ascs` | — | List all actors with ASCs |

### Tags (10)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `add_gameplay_tags` | `tags`, `source`? | Register tags (INI or DataTable) |
| `get_tag_hierarchy` | `root_tag`? | Display tag tree |
| `search_tag_usage` | `tag`, `search_scope`? | Find all assets using tag |
| `scaffold_tag_hierarchy` | `template`? | Generate tag hierarchy from preset |
| `rename_tag` | `old_tag`, `new_tag` | Rename across all assets |
| `remove_gameplay_tags` | `tags` | Remove from registry |
| `validate_tag_consistency` | — | Find orphan tags, naming violations |
| `audit_tag_naming` | `path_filter`? | Audit naming conventions |
| `export_tag_hierarchy` | `format`? | Export as JSON/CSV |
| `import_tag_hierarchy` | `source_path`, `format`? | Import from file |

### Cues (10)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_gameplay_cue_notify` | `save_path`, `cue_tag`, `type`? | Create GCN (Static or Actor) |
| `link_cue_to_effect` | `effect_path`, `cue_tag` | Add cue to GE |
| `unlink_cue_from_effect` | `effect_path`, `cue_tag` | Remove cue from GE |
| `get_cue_info` | `asset_path` | Read cue details |
| `list_gameplay_cues` | `path_filter`? | List all cues |
| `set_cue_parameters` | `asset_path`, `params` | Configure cue params |
| `find_cue_triggers` | `cue_tag` | Find GEs/abilities triggering cue |
| `validate_cue_coverage` | `path_filter`? | Check for GEs missing GCN assets |
| `batch_create_cues` | `cues` | Create multiple |
| `scaffold_cue_library` | `template`?, `save_path`? | Generate starter cue set |

### Targeting (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_target_actor` | `save_path`, `type`?, `parent_class`? | Create TargetActor BP |
| `configure_target_actor` | `asset_path`, `config` | Set range, radius, shape |
| `add_targeting_to_ability` | `ability_path`, `target_actor_class` | Wire WaitTargetData task |
| `scaffold_fps_targeting` | `save_path`, `config`? | FPS line trace targeting |
| `validate_targeting` | `asset_path` | Lint targeting setup |

### Input Binding (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `setup_ability_input_binding` | `asset_path`, `method`? | Configure binding approach |
| `bind_ability_to_input` | `asset_path`, `ability_class`, `input_action` | Bind to Enhanced Input |
| `batch_bind_abilities` | `asset_path`, `bindings` | Bind multiple |
| `get_ability_input_bindings` | `asset_path` | List bindings |
| `scaffold_input_binding_component` | `save_path` | Scaffold binding component |

### Inspect / Debug (6)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `snapshot_gas_state` | `actor_path` | Full runtime state (PIE) |
| `get_tag_state` | `actor_path` | Current tag container (PIE) |
| `get_cooldown_state` | `actor_path`, `ability_class`? | Active cooldowns (PIE) |
| `trace_ability_activation` | `actor_path`, `ability_class` | Activation trace (can/cannot + why) |
| `compare_gas_states` | `actor_a`, `actor_b` | Diff between two actors |
| `export_gas_manifest` | `path_filter`?, `format`? | Full project GAS manifest |

### Scaffold / Bootstrap (6)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `bootstrap_gas_foundation` | `save_path`, `config`? | Full bootstrap: ASC, attrs, GEs, tags |
| `validate_gas_setup` | `path_filter`? | Project-wide validation |
| `scaffold_gas_project` | `save_path`, `template`? | Scaffold complete project structure |
| `scaffold_damage_pipeline` | `save_path`, `config`? | Damage pipeline: meta attrs, exec calc |
| `scaffold_status_effect` | `save_path`, `effect_name`, `config`? | Status effect (DOT, buff, debuff) |
| `scaffold_weapon_ability` | `save_path`, `weapon_type`, `config`? | Weapon ability with targeting + cues |

## Templates

### Survival Horror (this project)
- `horror_attributes` — Health, Stamina, Sanity, Horror, PainThreshold
- `horror_effects` — Bleeding, Infection, Exhaustion, Panic, Adrenaline
- `horror_abilities` — Sprint, HeavyAttack, Heal, BarricadeDoor, Flashlight
- `horror_asc_player` — Full player ASC with accessibility GEs
- `horror_asc_ai` — AI ASC: minimal attributes, aggro abilities
- `horror_tags` — Full tag hierarchy (State, Ability, Effect, Damage, Status)

### Generic
- `basic_attributes` — Health, MaxHealth, Mana, MaxMana, AttackPower, Defense
- `basic_damage_effect` / `basic_heal_effect` / `basic_dot_effect` / `basic_buff_effect`
- `basic_melee_ability` / `basic_projectile_ability`
- `basic_asc_player` (on PlayerState) / `basic_asc_ai` (on Actor)

## Technical Notes

1. **UK2Node_LatentAbilityCall** — AT nodes use this, NOT UK2Node_CallFunction. `add_ability_task_node` handles it; if using `blueprint_query("add_node")` directly, specify correct type.
2. **GE Component Model (5.3+)** — Use `add_ge_component`/`set_ge_component`/`remove_ge_component` instead of legacy field setters.
3. **IAbilitySystemInterface is C++ only** — `setup_ability_system_interface` guides to C++ implementation.
4. **ComboGraph globals** — Check `DefaultGame.ini` for `GlobalAbilityList` entries that auto-grant abilities.
5. **GBA plugin** — Allows Blueprint-only attribute sets. Check before recommending C++-only workflows.
6. **Hospice accessibility** — Scaffold infinite-duration GEs for accessibility modes. Horror templates include these by default.

## Common Workflows

### Full Bootstrap
```
gas_query({ action: "bootstrap_gas_foundation", params: {
  save_path: "/Game/GAS",
  config: { template: "horror_asc_player", include_damage_pipeline: true }
}})
```

### Create GE with Modifiers
```
gas_query({ action: "create_gameplay_effect", params: {
  save_path: "/Game/GAS/Effects/GE_Damage_Bleed", duration_policy: "duration"
}})
gas_query({ action: "add_modifier", params: {
  asset_path: "/Game/GAS/Effects/GE_Damage_Bleed",
  attribute: "Health", operation: "Additive", magnitude: { type: "ScalableFloat", value: -5.0 }
}})
gas_query({ action: "set_period", params: {
  asset_path: "/Game/GAS/Effects/GE_Damage_Bleed", period: 1.0, execute_on_apply: true
}})
```

## Validation Catches

- Missing InitAbilityActorInfo → `validate_asc_setup`
- Cost GE with wrong duration (must be Instant) → `validate_effect`
- Cooldown GE without duration → `validate_effect`
- Infinite stacking without limit → `validate_effect`
- Meta attribute without execution calc → `validate_attribute_set`
- Orphaned cue tags (no GCN asset) → `validate_cue_coverage`
- Tag typos (used but not registered) → `validate_tag_consistency`
- Unbound abilities → `validate_gas_setup`
- Runtime actions (`get/set_attribute_value`, `apply/remove_effect`, `grant/revoke_ability`) only work during PIE
