"""Daemon Task Registry — Vertical Slice Priority Queue with Dependencies.

Inspired by Infinity Nikki's progression systems: CRITICAL → HIGH → MEDIUM → LOW
with topological sort ensuring dependencies complete before dependents.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Optional


class TaskPriority(IntEnum):
    """Task priority levels (lower = higher priority)."""
    CRITICAL = 0   # Vertical slice blockers — must complete first
    HIGH = 1       # Core content systems
    MEDIUM = 2     # Polish, content expansion
    LOW = 3        # Maintenance, notifications, self-tests


@dataclass(frozen=True)
class DaemonTask:
    """A single daemon task with priority and dependencies."""
    id: str
    priority: TaskPriority
    depends_on: tuple[str, ...]
    generator: str          # Dotted path to callable: "module.function"
    desc: str
    file: str               # Output file for staging area
    daemon: str             # Which daemon owns this task


# ──────────────────────────────────────────────────────────────────────
# VERTICAL SLICE TASK REGISTRY
# Ordered by priority, then dependency depth
# ──────────────────────────────────────────────────────────────────────

VERTICAL_SLICE_TASKS: tuple[DaemonTask, ...] = (
    # ═══ PHASE 1: SCALE + NPC PIPELINE (CRITICAL) ═══
    DaemonTask(
        id="scale_fix",
        priority=TaskPriority.CRITICAL,
        depends_on=(),
        generator="gmm.daemon.generators.apply_scale_fix",
        desc="Apply ×100 scale fix to all PCG configs and document",
        file="pcg_scale_fix_applied.json",
        daemon="pcg",
    ),

    DaemonTask(
        id="npc_vrm_import",
        priority=TaskPriority.CRITICAL,
        depends_on=("scale_fix",),
        generator="gmm.npc.vrm4u_import.import_all_vrms",
        desc="Import 10 VRMs via VRM4U with bone reduction audit",
        file="gmm_npc_vrm_import.json",
        daemon="npc",
    ),

    DaemonTask(
        id="npc_materials",
        priority=TaskPriority.CRITICAL,
        depends_on=("npc_vrm_import",),
        generator="gmm.npc.material_factory.setup_all_materials",
        desc="Create MToon master + 3 archetype MPCs + Material Instances",
        file="gmm_npc_materials.json",
        daemon="npc",
    ),

    DaemonTask(
        id="npc_cloth",
        priority=TaskPriority.CRITICAL,
        depends_on=("npc_materials",),
        generator="gmm.npc.cloth_setup.apply_all_cloth",
        desc="Configure DistanceConstraint/VRMSpringBone cloth per outfit piece",
        file="gmm_npc_cloth.json",
        daemon="npc",
    ),

    DaemonTask(
        id="npc_lods",
        priority=TaskPriority.CRITICAL,
        depends_on=("npc_cloth",),
        generator="gmm.npc.lod_generator.generate_all_lods",
        desc="Generate 3 LODs with bone culling (60→40→28 bones)",
        file="gmm_npc_lods.json",
        daemon="npc",
    ),

    DaemonTask(
        id="npc_battle",
        priority=TaskPriority.CRITICAL,
        depends_on=("npc_lods",),
        generator="gmm.npc.battle_integration.export_enemy_defs",
        desc="Export 14 enemy defs (3 archetype + 11 NPC variants) JSON + C++",
        file="battle_enemy_defs.json",
        daemon="npc",
    ),

    DaemonTask(
        id="npc_populate",
        priority=TaskPriority.CRITICAL,
        depends_on=("npc_battle",),
        generator="gmm.npc.level_populator.populate_test_forest",
        desc="Spawn 10 NPCs in L_PCGTest_Forest with AI/interaction",
        file="gmm_npc_populate.json",
        daemon="npc",
    ),

    # ═══ PHASE 2: ROGUELIKE CORE (HIGH) ═══

    DaemonTask(
        id="procedural_dungeon_build",
        priority=TaskPriority.CRITICAL,
        depends_on=("scale_fix",),
        generator="gmm.daemon.generators.build_report",
        desc="Verify ProceduralDungeon v3.8.3 plugin compiled + loaded for UE 5.8",
        file="procedural_dungeon_build_report.json",
        daemon="roguelike",
    ),

    DaemonTask(
        id="roguelike_contract",
        priority=TaskPriority.HIGH,
        depends_on=("procedural_dungeon_build",),
        generator="gmm.daemon.generators.create_roguelike_contract",
        desc="Emit fixtures and golden traces for native UMelodiaRoguelikeRunSubsystem",
        file="melodia_roguelike_contract.json",
        daemon="roguelike",
    ),

    DaemonTask(
        id="dungeon_translator",
        priority=TaskPriority.HIGH,
        depends_on=("roguelike_contract",),
        generator="gmm.daemon.generators.create_dungeon_translator",
        desc="Floor graph → ProceduralDungeon RoomData translator (ProceduralDungeon v3.8.3)",
        file="dungeon_translator.json",
        daemon="roguelike",
    ),

    DaemonTask(
        id="blessings_system",
        priority=TaskPriority.HIGH,
        depends_on=("roguelike_contract",),
        generator="gmm.daemon.generators.create_blessings_system",
        desc="7-element blessings + 3-tier songcraft resonance system",
        file="blessings_system.json",
        daemon="roguelike",
    ),

    DaemonTask(
        id="artifacts_relics",
        priority=TaskPriority.HIGH,
        depends_on=("blessings_system",),
        generator="gmm.daemon.generators.create_artifacts_relics",
        desc="11 artifacts (4 base + 7 elemental) + 5 meta-progression relics",
        file="artifacts_relics.json",
        daemon="roguelike",
    ),

    # ═══ PHASE 3: DUNGEON GENERATION (HIGH) ═══

    DaemonTask(
        id="dungeon_generator",
        priority=TaskPriority.HIGH,
        depends_on=("dungeon_translator", "artifacts_relics"),
        generator="gmm.daemon.generators.create_dungeon_generator",
        desc="ProceduralDungeon-based dungeon gen (22 RoomData specs, 8 room levels, Nikki themes)",
        file="dungeon_generator.json",
        daemon="roguelike",
    ),

    DaemonTask(
        id="dungeon_room_levels",
        priority=TaskPriority.HIGH,
        depends_on=("dungeon_generator",),
        generator="gmm.daemon.generators.build_roguelike_report",
        desc="Room levels with EncounterTriggers, Nikki PPV, PCG, NPCs (runs in UE Editor)",
        file="roguelike_dungeon_setup.json",
        daemon="roguelike",
    ),

    # ═══ PHASE 4: MELODIA CONTENT EXPANSION (MEDIUM) ═══
    DaemonTask(
        id="melodia_enemies",
        priority=TaskPriority.MEDIUM,
        depends_on=(),
        generator="gmm.daemon.generators.extend_melodia_enemies",
        desc="Add 14+ enemies across 7 elements + boss tiers (TitanPrime, HarmonyVoid)",
        file="melodia_enemies.py",
        daemon="melodia",
    ),

    DaemonTask(
        id="melodia_skills",
        priority=TaskPriority.MEDIUM,
        depends_on=("melodia_enemies",),
        generator="gmm.daemon.generators.extend_melodia_skills",
        desc="Add skills for all 7 elements + ultimate/crescendo mechanics",
        file="melodia_skills.py",
        daemon="melodia",
    ),

    DaemonTask(
        id="melodia_equipment",
        priority=TaskPriority.MEDIUM,
        depends_on=("melodia_skills",),
        generator="gmm.daemon.generators.extend_melodia_equipment",
        desc="Weapons/armor/accessories per element + relic sets (Planar Ornament equiv)",
        file="melodia_equipment.py",
        daemon="melodia",
    ),

    DaemonTask(
        id="fabric_materials",
        priority=TaskPriority.MEDIUM,
        depends_on=("npc_materials",),
        generator="gmm.daemon.generators.create_fabric_materials",
        desc="Fabric profiles (silk/cotton/velvet/pearl/chiffon/organza) for outfit pieces",
        file="fabric_profiles.json",
        daemon="npc",
    ),

    # ═══ NIKKI-SPECIFIC SYSTEMS (MEDIUM) ═══
    DaemonTask(
        id="photo_mode_poses",
        priority=TaskPriority.MEDIUM,
        depends_on=("npc_populate",),
        generator="gmm.daemon.generators.create_photo_mode_poses",
        desc="Photo mode pose sets per archetype + affinity rewards",
        file="photo_mode_poses.json",
        daemon="npc",
    ),

    DaemonTask(
        id="affinity_progression",
        priority=TaskPriority.MEDIUM,
        depends_on=("npc_populate", "blessings_system"),
        generator="gmm.daemon.generators.create_affinity_progression",
        desc="Whimstar-style affinity tiers → outfit variants + exclusive poses",
        file="affinity_progression.py",
        daemon="npc",
    ),

    DaemonTask(
        id="styling_challenges",
        priority=TaskPriority.MEDIUM,
        depends_on=("npc_populate", "melodia_equipment"),
        generator="gmm.daemon.generators.create_styling_challenges",
        desc="Battle NPCs rate player outfit element match → style rating rewards",
        file="styling_challenges.py",
        daemon="npc",
    ),

    # ═══ MAINTENANCE (LOW) ═══
    DaemonTask(
        id="audit_logging",
        priority=TaskPriority.LOW,
        depends_on=(),
        generator="gmm.daemon.generators.add_audit_logging",
        desc="Daemon audit logging + circuit breaker + notification webhooks",
        file="daemon_audit.py",
        daemon="daemon",
    ),

    DaemonTask(
        id="webhook_notifications",
        priority=TaskPriority.LOW,
        depends_on=("audit_logging",),
        generator="gmm.daemon.generators.add_webhook_notifications",
        desc="Discord/console webhook notifications for daemon events",
        file="webhook_notifications.py",
        daemon="daemon",
    ),

    DaemonTask(
        id="self_test",
        priority=TaskPriority.LOW,
        depends_on=("audit_logging",),
        generator="gmm.daemon.generators.add_self_test",
        desc="Daemon self-test module + smoke test integration",
        file="test_daemon.py",
        daemon="daemon",
    ),
)


# ──────────────────────────────────────────────────────────────────────
# TASK SELECTION LOGIC
# ──────────────────────────────────────────────────────────────────────

def pick_next_task(state: dict) -> Optional[DaemonTask]:
    """
    Topological sort + priority queue.
    Returns None when all tasks done or blocked.
    """
    completed = set(state.get("completed", []))
    failed = set(state.get("failed", []))

    # Tasks ready to run: not done, not failed, all dependencies met
    ready = [
        t for t in VERTICAL_SLICE_TASKS
        if t.id not in completed and t.id not in failed
        and all(d in completed for d in t.depends_on)
    ]

    if not ready:
        return None

    # Sort by priority (ascending), then by dependency depth (descending)
    ready.sort(key=lambda t: (t.priority, -len(t.depends_on)))
    return ready[0]


def get_task_by_id(task_id: str) -> Optional[DaemonTask]:
    """Look up task by ID."""
    for t in VERTICAL_SLICE_TASKS:
        if t.id == task_id:
            return t
    return None


def get_tasks_by_daemon(daemon_name: str) -> list[DaemonTask]:
    """Filter tasks by owning daemon."""
    return [t for t in VERTICAL_SLICE_TASKS if t.daemon == daemon_name]


def get_tasks_by_priority(priority: TaskPriority) -> list[DaemonTask]:
    """Filter tasks by priority level."""
    return [t for t in VERTICAL_SLICE_TASKS if t.priority == priority]


def get_task_summary() -> dict:
    """Return summary statistics for the task registry."""
    return {
        "total_tasks": len(VERTICAL_SLICE_TASKS),
        "by_priority": {
            p.name: len([t for t in VERTICAL_SLICE_TASKS if t.priority == p])
            for p in TaskPriority
        },
        "by_daemon": {
            d: len(get_tasks_by_daemon(d))
            for d in {"pcg", "npc", "roguelike", "melodia", "daemon"}
        },
        "critical_path_length": _calculate_critical_path_length(),
    }


def _calculate_critical_path_length() -> int:
    """Calculate length of longest dependency chain."""
    # Simple DP on DAG
    memo = {}

    def dfs(task_id: str) -> int:
        if task_id in memo:
            return memo[task_id]
        task = get_task_by_id(task_id)
        if not task or not task.depends_on:
            memo[task_id] = 1
            return 1
        max_len = max(dfs(dep) for dep in task.depends_on)
        memo[task_id] = max_len + 1
        return memo[task_id]

    return max(dfs(t.id) for t in VERTICAL_SLICE_TASKS)


# ──────────────────────────────────────────────────────────────────────
# EXPORTS
# ──────────────────────────────────────────────────────────────────────

__all__ = [
    "TaskPriority",
    "DaemonTask",
    "VERTICAL_SLICE_TASKS",
    "pick_next_task",
    "get_task_by_id",
    "get_tasks_by_daemon",
    "get_tasks_by_priority",
    "get_task_summary",
]