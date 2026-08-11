"""Melodia Rhythm Battle — main CLI game runner.

Wires together:
    - MelodiaDataRegistry   (enemies, skills)
    - MelodiaPlayerState    (stats, inventory, XP)
    - MelodiaBattleManager  (full battle state machine)
    - SaveManager           (save/load persistence)
    - GameConfig            (tunable constants)

Usage:
    python -m gmm            ← interactive CLI loop
    python -m gmm.main       ← same
    python -m gmm.main --battle CrystalShard   ← quick battle
"""
from __future__ import annotations

import random
import sys
import time
from typing import Optional

from gmm.game.config import GAME_CFG
from gmm.game.data_registry import MelodiaDataRegistry, EnemyStats, SkillData
from gmm.game.player_state import MelodiaPlayerState
from gmm.game.battle_manager import MelodiaBattleManager, element_multiplier, ELEMENT_CYCLE
from gmm.game.save_manager import SaveManager
from gmm.game.audio_engine import AudioEngine
from gmm.game.equipment_catalog import get_equipment, list_equipment, starter_kit, catalog_summary
from gmm.melodia.skills import DEMO_SKILLS, list_skills
from gmm.melodia.enemies import DEMO_ENEMIES, list_enemies


# ---------------------------------------------------------------------------
# ANSI helpers for colored terminal output
# ---------------------------------------------------------------------------

class Style:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    CLEAR = "\033[2J\033[H"


def c(text: str, color: str = "") -> str:
    if color and sys.stdout.isatty():
        return f"{color}{text}{Style.RESET}"
    return text


GRADE_COLORS = {
    "perfect": Style.GREEN,
    "great": Style.CYAN,
    "good": Style.YELLOW,
    "miss": Style.RED,
}

BAR_FULL = "#"
BAR_EMPTY = "-"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def bar(value: float, max_val: float, width: int = 20) -> str:
    filled = int(clamp(value / max_val if max_val > 0 else 0) * width)
    return f"[{BAR_FULL * filled}{BAR_EMPTY * (width - filled)}]"


def enemy_card(enemy: EnemyStats, current_hp: float) -> str:
    pct = current_hp / enemy.max_hp if enemy.max_hp > 0 else 0
    color = Style.RED if pct < 0.3 else (Style.YELLOW if pct < 0.6 else Style.WHITE)
    elem = enemy.element.capitalize()
    return (
        f"{c(enemy.display_name, Style.MAGENTA)} [{c(elem, Style.CYAN)}] "
        f"HP: {c(f'{current_hp:.0f}/{enemy.max_hp:.0f}', color)} "
        f"{bar(current_hp, enemy.max_hp, 12)}"
    )


def player_card(ps: MelodiaPlayerState, battle_hp: float, battle_sp: float, ult: float) -> str:
    return (
        f"Lv.{ps.level}  "
        f"HP: {c(f'{battle_hp:.0f}/{ps.max_hp:.0f}', Style.GREEN)} {bar(battle_hp, ps.max_hp)}  "
        f"SP: {c(f'{battle_sp:.0f}/{ps.max_sp:.0f}', Style.CYAN)} {bar(battle_sp, ps.max_sp)}  "
        f"Ult: {c(f'{ult:.0f}/100', Style.MAGENTA)} {bar(ult, 100)}"
    )


def grade_ascii(grade: str) -> str:
    art = {
        "perfect": "*** PERFECT",
        "great": "** GREAT",
        "good": "* GOOD",
        "miss": "x MISS",
    }
    color = GRADE_COLORS.get(grade, Style.WHITE)
    return c(art.get(grade, grade.upper()), color)


def combo_display(combo: int) -> str:
    if combo >= 10:
        return c(f"{combo}x COMBO!", Style.MAGENTA + Style.BOLD)
    if combo >= 5:
        return c(f"{combo}x Combo", Style.CYAN)
    if combo >= 3:
        return c(f"{combo}x combo", Style.GREEN)
    return ""


# ---------------------------------------------------------------------------
# Input simulation (rhythm prompt)
# ---------------------------------------------------------------------------

def prompt_rhythm_input(bpm: float) -> float:
    """Prompt the player to press Enter for a rhythm input, then return ms offset from beat."""
    ms_per_beat = 60000.0 / bpm if bpm > 0 else 500.0
    target_ms = ms_per_beat * 0.25  # aim for the first quarter-beat
    input(f"{c('Press ENTER on the beat...', Style.DIM)} ")
    return abs(random.gauss(target_ms, target_ms * 0.3))


# ---------------------------------------------------------------------------
# Battle loop
# ---------------------------------------------------------------------------

def run_battle(mgr: MelodiaBattleManager, enemy_id: str) -> str:
    """Run a single encounter. Returns 'victory', 'defeat', 'fled', or 'error'."""
    result = mgr.start_encounter(enemy_id)
    if not result.get("ok"):
        print(f"  {c(result.get('error', 'Unknown error'), Style.RED)}")
        return "error"

    enemy = mgr.enemy
    print(f"\n{c('=== ENCOUNTER! ===', Style.MAGENTA + Style.BOLD)}")
    print(f"  {c(enemy.display_name, Style.MAGENTA)} — {c(enemy.element, Style.CYAN)} element")
    if GAME_CFG.show_bpm_on_start:
        print(f"  BPM: {c(str(enemy.bpm), Style.YELLOW)} | "
              f"HP: {enemy.max_hp:.0f} | "
              f"Toughness: {enemy.toughness:.0f}")

    # Show available skills for player level
    player_skills = mgr.player.skills_for_level()
    if player_skills:
        print(f"  Skills: {', '.join(player_skills)}")
    print()

    while mgr.phase in ("AwaitingPlayerCommand", "RhythmExecution", "EnemyTurn"):
        # --- Player Command Phase ---
        print(enemy_card(enemy, mgr.enemy_hp))
        print(player_card(mgr.player, mgr.battle_hp, mgr.battle_sp, mgr.battle_ult))
        if mgr.combo > 1:
            print(f"  {combo_display(mgr.combo)}")
        print()

        cmd_lines = [
            f"  [{c('1', Style.YELLOW)}] Basic Attack",
            f"  [{c('2', Style.YELLOW)}] Skill",
            f"  [{c('3', Style.YELLOW)}] Ultimate ({mgr.battle_ult:.0f}/100)",
            f"  [{c('4', Style.YELLOW)}] Defend",
            f"  [{c('5', Style.YELLOW)}] Flee",
        ]
        if mgr.turn_count == 0:
            print("\n".join(cmd_lines))
        choice = input(f"\n{c('Command', Style.BOLD)} [1-5]: ").strip()

        if choice == "1":
            result = mgr.player_command("basic_attack")
        elif choice == "2":
            skills = mgr.registry.list_skills_available(mgr.player.level)
            if not skills:
                print(f"  {c('No skills available at your level.', Style.RED)}")
                continue
            print(f"\n{c('Available Skills:', Style.CYAN)}")
            for i, sk in enumerate(skills, 1):
                cost = f"SP:{sk.sp_cost}" if sk.sp_cost > 0 else "Free"
                elem = sk.element.capitalize() if sk.element else "Neutral"
                print(f"  [{i}] {c(sk.display_name, Style.MAGENTA)} ({elem}) "
                      f"dmg:{sk.base_damage:.0f} {c(cost, Style.CYAN)}")
            sk_choice = input(f"Select skill [1-{len(skills)}]: ").strip()
            if not sk_choice.isdigit() or not (1 <= int(sk_choice) <= len(skills)):
                print(f"  {c('Invalid skill choice.', Style.RED)}")
                continue
            sk = skills[int(sk_choice) - 1]
            result = mgr.player_command("skill", skill_id=sk.skill_id)
        elif choice == "3":
            result = mgr.player_command("ultimate")
        elif choice == "4":
            result = mgr.player_command("defend")
        elif choice == "5":
            result = mgr.player_command("flee")
            if result.get("fled"):
                print(f"\n{c('You fled successfully!', Style.YELLOW)}")
                return "fled"
            print(f"\n{c('Flee failed!', Style.RED)}")
        else:
            print(f"  {c('Invalid choice.', Style.RED)}")
            continue

        if not result.get("ok"):
            print(f"  {c(result.get('error', 'Command failed'), Style.RED)}")
            continue

        # --- Rhythm Phase ---
        print(f"\n{c('~ Rhythm input! ~', Style.CYAN)}")
        bpm = mgr.clock.bpm
        input_ms = prompt_rhythm_input(bpm)
        result = mgr.resolve_rhythm(input_ms)

        grade = result.get("grade", "miss")
        dmg = result.get("damage", 0)
        elem_mult = result.get("element_mult", 1.0)
        enemy_hp = result.get("enemy_hp", 0)
        combo = result.get("combo", 0)

        # Show result
        grade_str = grade_ascii(grade)
        combo_str = combo_display(combo)
        dmg_color = Style.GREEN if dmg > 0 else Style.DIM
        elem_str = c(f"x{elem_mult:.1f}", Style.CYAN) if elem_mult != 1.0 else ""
        print(f"  {grade_str}  {c(f'{dmg:.1f} dmg', dmg_color)} {elem_str} {combo_str}")

        if mgr.phase == "Victory":
            print(f"\n{c('=== VICTORY! ===', Style.GREEN + Style.BOLD)}")
            print(f"  Combo: {c(str(combo), Style.CYAN)} | "
                  f"Max: {c(str(mgr.max_combo), Style.YELLOW)}")
            print(f"  Grades: P:{mgr.grades['perfect']} G:{mgr.grades['great']} "
                  f"g:{mgr.grades['good']} M:{mgr.grades['miss']}")
            return "victory"

        # --- Enemy Turn ---
        if mgr.phase == "EnemyTurn":
            print(f"\n{c('~ Enemy turn ~', Style.RED)}")
            result = mgr.enemy_turn()
            dmg_taken = result.get("damage", 0)
            player_hp = result.get("player_hp", 0)
            print(f"  Enemy deals {c(f'{dmg_taken:.1f}', Style.RED)} damage! "
                  f"HP: {c(f'{player_hp:.0f}', Style.GREEN)}")

            if mgr.phase == "Defeat":
                print(f"\n{c('=== DEFEAT ===', Style.RED + Style.BOLD)}")
                return "defeat"

    return "error"


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def run_game_loop():
    """Full interactive game session with multiple encounters."""
    registry = MelodiaDataRegistry()
    player = MelodiaPlayerState()
    save_mgr = SaveManager()

    # Try loading existing save
    loaded = save_mgr.load(player)
    if loaded:
        print(f"{c('Loaded save:', Style.DIM)} Lv.{player.level} HP:{player.hp:.0f} "
              f"Gold:{player.gold} Encounters:{len(player.completed_encounters)}")
    else:
        # Give starter equipment to new players
        for eq in starter_kit():
            if eq:
                player.equip_item(eq)
        player.unlock_skill("StarlitPing")
        player.unlock_skill("MoonStep")
        print(f"{c('New game — starter equipment equipped!', Style.DIM)}")

    print(f"\n{c('MELODIA RHYTHM BATTLE', Style.MAGENTA + Style.BOLD)}")
    print(f"{c('====================', Style.DIM)}")
    print(f"  {c('Player:', Style.BOLD)} Lv.{player.level} | "
          f"{c('HP:', Style.GREEN)}{player.hp:.0f}/{player.max_hp:.0f} | "
          f"{c('SP:', Style.CYAN)}{player.sp:.0f}/{player.max_sp:.0f} | "
          f"{c('Gold:', Style.YELLOW)}{player.gold}")
    print(f"  {c('Skills:', Style.DIM)} {len(player.unlocked_skills)} unlocked | "
          f"{c('Encounters:', Style.DIM)} {len(player.completed_encounters)} completed")
    print()

    audio = AudioEngine()
    enemies = list_enemies()
    while True:
        print(f"{c('=== GRANDMASTER HUB ===', Style.CYAN + Style.BOLD)}")
        audio_status = c("ON" if audio.enabled else "OFF", Style.GREEN if audio.enabled else Style.RED)
        print(f"  [{c('1', Style.YELLOW)}] Battle — pick an enemy")
        print(f"  [{c('2', Style.YELLOW)}] Status — view player stats")
        print(f"  [{c('3', Style.YELLOW)}] Skills — view unlocked skills")
        print(f"  [{c('4', Style.YELLOW)}] Inventory — view items/equipment")
        print(f"  [{c('5', Style.YELLOW)}] Save — save progress")
        print(f"  [{c('6', Style.YELLOW)}] Audio — toggle ({audio_status})")
        print(f"  [{c('7', Style.YELLOW)}] Quit")

        hub_choice = input(f"\n{c('Choice', Style.BOLD)} [1-7]: ").strip()

        if hub_choice == "1":
            # Pick enemy
            print(f"\n{c('Enemies:', Style.MAGENTA)}")
            for i, e in enumerate(enemies, 1):
                completed = c("[CLEAR]", Style.GREEN) if e["enemy_id"] in player.completed_encounters else ""
                print(f"  [{i}] {c(e['display_name'], Style.MAGENTA)} ({e['element']}) "
                      f"HP:{e['max_hp']} BPM:{e['bpm']} {completed}")
            print(f"  [0] {c('Back', Style.DIM)}")
            e_choice = input(f"Select enemy [0-{len(enemies)}]: ").strip()
            if not e_choice.isdigit():
                continue
            idx = int(e_choice)
            if idx == 0:
                continue
            if idx < 1 or idx > len(enemies):
                print(f"  {c('Invalid choice.', Style.RED)}")
                continue
            enemy_id = enemies[idx - 1]["enemy_id"]

            # Run battle
            mgr = MelodiaBattleManager(registry=registry, player=player, audio=audio)
            outcome = run_battle(mgr, enemy_id)

            if outcome == "victory":
                summary = mgr.end_encounter()
                s = summary["summary"]
                xp_gain = s["xp_earned"]
                gold_gain = s["gold_earned"]
                print(f"\n  {c('Rewards:', Style.YELLOW)} "
                      f"XP:{c(f'+{xp_gain}', Style.CYAN)} "
                      f"Gold:{c(f'+{gold_gain}', Style.YELLOW)}")
                if GAME_CFG.auto_save_on_victory:
                    path = save_mgr.save(player)
                    print(f"  {c('Auto-saved.', Style.DIM)}")
            elif outcome == "defeat":
                summary = mgr.end_encounter()
                print(f"\n  {c('Half HP/SP recovered.', Style.DIM)}")
                if GAME_CFG.auto_save_on_defeat:
                    save_mgr.save(player)
            elif outcome == "fled":
                mgr.end_encounter()

        elif hub_choice == "2":
            desc = player.describe()
            print(f"\n{c('PLAYER STATUS', Style.CYAN + Style.BOLD)}")
            for k, v in desc.items():
                print(f"  {c(k.replace('_', ' ').title() + ':', Style.BOLD)} {v}")

        elif hub_choice == "3":
            skills = player.unlocked_skills
            if not skills:
                print(f"\n  {c('No skills unlocked. Battle more!', Style.DIM)}")
            else:
                print(f"\n{c('UNLOCKED SKILLS', Style.CYAN + Style.BOLD)}")
                for sk_id in skills:
                    sk = registry.get_skill(sk_id)
                    if sk:
                        print(f"  {c(sk.display_name, Style.MAGENTA)} "
                              f"({sk.element}) dmg:{sk.base_damage} SP:{sk.sp_cost}")

        elif hub_choice == "4":
            print(f"\n{c('INVENTORY', Style.CYAN + Style.BOLD)}")
            inv = player.inventory
            if inv:
                for item_id, item in inv.items():
                    print(f"  {c(item.display_name, Style.YELLOW)} x{item.quantity}")
            else:
                print(f"  {c('(empty)', Style.DIM)}")
            eq = player.equipment
            print(f"\n{c('EQUIPMENT', Style.CYAN + Style.BOLD)}")
            for slot in ("weapon", "armor", "shield", "helm", "boots"):
                item = eq.get(slot)
                name = item.display_name if item else "(empty)"
                print(f"  {c(slot.title() + ':', Style.BOLD)} {c(name, Style.MAGENTA if item else Style.DIM)}")

        elif hub_choice == "5":
            path = save_mgr.save(player)
            print(f"\n  {c(f'Saved to {path}', Style.GREEN)}")

        elif hub_choice == "6":
            audio.toggle()
            print(f"\n  Audio {c('ON' if audio.enabled else 'OFF', Style.GREEN if audio.enabled else Style.RED)}")

        elif hub_choice == "7":
            path = save_mgr.save(player)
            print(f"\n  {c(f'Auto-saved to {path}', Style.DIM)}")
            print(f"{c('Goodbye!', Style.MAGENTA)}")
            break

        print()

    return 0


# ---------------------------------------------------------------------------
# Quick battle mode
# ---------------------------------------------------------------------------

def run_quick_battle(enemy_id: str = "CrystalShard"):
    """Single battle with a fresh player, no persistence."""
    registry = MelodiaDataRegistry()
    player = MelodiaPlayerState()
    mgr = MelodiaBattleManager(registry=registry, player=player)
    outcome = run_battle(mgr, enemy_id)
    if outcome == "victory":
        summary = mgr.end_encounter()
        s = summary["summary"]
        print(f"\nRewards: XP +{s['xp_earned']} Gold +{s['gold_earned']}")
    else:
        mgr.end_encounter()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if "--gui" in sys.argv:
        # Launch PyGame GUI (requires pygame, Python 3.12+)
        try:
            from gmm.ui.pygame_battle import launch_pygame_battle
            launch_pygame_battle()
        except ImportError as e:
            print(f"Error: {e}")
            print("PyGame not available. Install with: pip install pygame")
            sys.exit(1)
        sys.exit(0)

    if "--battle" in sys.argv:
        idx = sys.argv.index("--battle")
        enemy_id = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "CrystalShard"
        sys.exit(run_quick_battle(enemy_id))
    sys.exit(run_game_loop())


if __name__ == "__main__":
    main()
