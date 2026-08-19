"""Emit the two generated rule modules from Plugins/MelodiaCore/Rules/melodia_rules.json.

Outputs (DO NOT EDIT those files by hand):
  - Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRulesGenerated.h  (constexpr, C++ runtime truth)
  - Content/Python/gmm/game/rules_generated.py                      (gmm sandbox truth)
  - my-site-clean/generated/melodia_rhythm_web_config.json          (Melusina web demo)

Run after every edit to melodia_rules.json, then rebuild MelodiaCore and run
the Melodia.CoreRules.* automation tests. Web config is also refreshable via
Tools/export_melodia_rhythm_web_config.py alone.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Plugins/MelodiaCore/Rules/melodia_rules.json"
OUT_H = ROOT / "Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRulesGenerated.h"
OUT_PY = ROOT / "Content/Python/gmm/game/rules_generated.py"

# Authored skill ids map onto canonical songcraft ids. Both spellings resolve.
SKILL_ID_ALIASES = [
    ("Skill_Lv01_StarlitPing", "StarlitPing"),
    ("StarlitPing", "StarlitPing"),
    ("Skill_Lv02_MoonStep", "MoonStep"),
    ("MoonStep", "MoonStep"),
    ("Skill_Lv05_GoldStuccoStrike", "TidalWave"),
    ("TidalWave", "TidalWave"),
    ("Skill_Lv06_EscherClimb", "GustStaccato"),
    ("GustStaccato", "GustStaccato"),
    ("Skill_Lv12_CathedralChant", "StoneWall"),
    ("StoneWall", "StoneWall"),
    ("Skill_Lv03_CherryArpeggio", "TidalMend"),
    ("TidalMend", "TidalMend"),
]


# Scalar formatters: emit C++ literals that survive a constexpr context.
def _f(v, default=0.0) -> str:
    x = float(v if v is not None else default)
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ".0"
    return f"{s}f"


def _i(v, default=0) -> int:
    return int(v if v is not None else default)


def _cstr(s: str | None) -> str:
    if not s:
        return "nullptr"
    esc = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'TEXT("{esc}")'


def emit_modifiers_cpp(modifiers: dict) -> str:
    registry = modifiers.get("registry") or []
    rows = []
    for m in registry:
        rows.append(
            "\t\t{ "
            f"{_cstr(m.get('id'))}, {_cstr(m.get('stat'))}, {_cstr(m.get('op'))}, "
            f"{_f(m.get('value'), 1.0)}, {_i(m.get('duration_turns'), 1)}, "
            f"{_cstr(m.get('stacking'))}, {_i(m.get('max_stacks'), 1)}"
            " }"
        )
    table = ",\n".join(rows) if rows else ""
    return f"""
\tstruct FGeneratedModifier
\t{{
\t\tconst TCHAR* Id;
\t\tconst TCHAR* Stat;
\t\tconst TCHAR* Op;
\t\tfloat Value;
\t\tint32 DurationTurns;
\t\tconst TCHAR* Stacking;
\t\tint32 MaxStacks;
\t}};

\tinline const FGeneratedModifier* GetModifierTable(int32& OutCount)
\t{{
\t\tstatic const FGeneratedModifier Table[] =
\t\t{{
{table}
\t\t}};
\t\tOutCount = UE_ARRAY_COUNT(Table);
\t\treturn Table;
\t}}

\tinline bool FindGeneratedModifier(FName ModifierId, FGeneratedModifier& OutMod)
\t{{
\t\tint32 Count = 0;
\t\tconst FGeneratedModifier* Table = GetModifierTable(Count);
\t\tfor (int32 i = 0; i < Count; ++i)
\t\t{{
\t\t\tif (ModifierId == FName(Table[i].Id))
\t\t\t{{
\t\t\t\tOutMod = Table[i];
\t\t\t\treturn true;
\t\t\t}}
\t\t}}
\t\treturn false;
\t}}
"""


# Songcraft skill effects.
#
# Every field is optional in the JSON; the emitters below supply the neutral
# default so a partially-authored effect still produces a valid constexpr row:
#   - toughness_scalar defaults to 1.0 (no scaling)
#   - every other float defaults to 0.0 (no contribution)
#   - sp_gain_on_perfect defaults to 0
#
# modifiers_on_hit / modifiers_on_perfect are authored as arrays but the C++
# table carries only the first entry, since no shipped skill applies more than
# one. `(... or [None])[0]` collapses "absent", "empty array" and "first of N"
# to a single value, and _cstr(None) emits nullptr.
#
# NormalizeSongcraftSkillId is emitted alongside the table so the runtime can
# accept either the authored Skill_LvNN_* id or the canonical songcraft id --
# see SKILL_ID_ALIASES above. Lookup normalises before comparing.
def emit_skill_effects_cpp(songcraft: dict) -> str:
    effects = songcraft.get("skill_effects") or []
    rows = []
    for e in effects:
        sid = e.get("skill_id") or ""
        mod_hit = (e.get("modifiers_on_hit") or [None])[0]
        mod_perf = (e.get("modifiers_on_perfect") or [None])[0]
        rows.append(
            "\t\t{ "
            f"{_cstr(sid)}, {_f(e.get('toughness_scalar'), 1.0)}, "
            f"{_f(e.get('bonus_damage_on_break'))}, "
            f"{_f(e.get('enemy_delay_on_break_av_fraction'))}, "
            f"{_f(e.get('enemy_delay_on_hit_av_fraction'))}, "
            f"{_f(e.get('heal_on_hit_scalar'))}, "
            f"{_f(e.get('ult_gain_bonus_on_perfect'))}, "
            f"{_i(e.get('sp_gain_on_perfect'))}, "
            f"{_cstr(mod_hit)}, {_cstr(mod_perf)}"
            " }"
        )
    table = ",\n".join(rows) if rows else ""
    alias_rows = ",\n".join(
        f"\t\t{{ {_cstr(a)}, {_cstr(c)} }}" for a, c in SKILL_ID_ALIASES
    )
    return f"""
\tstruct FGeneratedSkillEffect
\t{{
\t\tconst TCHAR* SkillId;
\t\tfloat ToughnessScalar;
\t\tfloat BonusDamageOnBreak;
\t\tfloat EnemyDelayOnBreakAvFraction;
\t\tfloat EnemyDelayOnHitAvFraction;
\t\tfloat HealOnHitScalar;
\t\tfloat UltGainBonusOnPerfect;
\t\tint32 SpGainOnPerfect;
\t\tconst TCHAR* ModifierOnHit;
\t\tconst TCHAR* ModifierOnPerfect;
\t}};

\tinline const FGeneratedSkillEffect* GetSkillEffectTable(int32& OutCount)
\t{{
\t\tstatic const FGeneratedSkillEffect Table[] =
\t\t{{
{table}
\t\t}};
\t\tOutCount = UE_ARRAY_COUNT(Table);
\t\treturn Table;
\t}}

\tinline FName NormalizeSongcraftSkillId(FName SkillId)
\t{{
\t\tstatic const struct {{ const TCHAR* From; const TCHAR* To; }} Aliases[] =
\t\t{{
{alias_rows}
\t\t}};
\t\tfor (const auto& A : Aliases)
\t\t{{
\t\t\tif (SkillId == FName(A.From))
\t\t\t{{
\t\t\t\treturn FName(A.To);
\t\t\t}}
\t\t}}
\t\treturn SkillId;
\t}}

\tinline bool FindSkillEffect(FName SkillId, FGeneratedSkillEffect& OutEffect)
\t{{
\t\tconst FName Canonical = NormalizeSongcraftSkillId(SkillId);
\t\tint32 Count = 0;
\t\tconst FGeneratedSkillEffect* Table = GetSkillEffectTable(Count);
\t\tfor (int32 i = 0; i < Count; ++i)
\t\t{{
\t\t\tif (Canonical == FName(Table[i].SkillId))
\t\t\t{{
\t\t\t\tOutEffect = Table[i];
\t\t\t\treturn true;
\t\t\t}}
\t\t}}
\t\treturn false;
\t}}
"""


def main() -> int:
    rules = json.loads(SRC.read_text(encoding="utf-8"))
    r = rules["rhythm"]
    t = rules["turn_economy"]
    s = rules["songcraft"]
    u = rules["ultimate"]
    tough = rules["toughness"]

    o = rules["opening_flow"]

    skill_block = emit_skill_effects_cpp(s)
    mod_block = emit_modifiers_cpp(rules.get("modifiers") or {})

    h = "".join([
        "// GENERATED by Tools/generate_melodia_rules.py from Plugins/MelodiaCore/Rules/melodia_rules.json\n"
        "// DO NOT EDIT — edit the JSON and regenerate. Rules version ",
        f"{rules['_meta']['version']}",
        ".\n"
        "#pragma once\n"
        "\n"
        '#include "HAL/Platform.h"\n'
        '#include "UObject/NameTypes.h"\n'
        "\n"
        "namespace MelodiaRulesGen\n"
        "{\n"
        "\t// Rhythm\n"
        "\tconstexpr float PerfectWindowMs = ",
        f"{r['windows_ms']['perfect']}",
        "f;\n\tconstexpr float GreatWindowMs = ",
        f"{r['windows_ms']['great']}",
        "f;\n\tconstexpr float GoodWindowMs = ",
        f"{r['windows_ms']['good']}",
        "f;\n\tconstexpr float PerfectMultiplier = ",
        f"{r['grade_multipliers']['perfect']}",
        "f;\n\tconstexpr float GreatMultiplier = ",
        f"{r['grade_multipliers']['great']}",
        "f;\n\tconstexpr float GoodMultiplier = ",
        f"{r['grade_multipliers']['good']}",
        "f;\n\tconstexpr float MissMultiplier = ",
        f"{r['grade_multipliers']['miss']}",
        "f;\n\tconstexpr float MaxCombatMultiplier = ",
        f"{r['max_combat_multiplier']}",
        "f;\n\tconstexpr float ComboBonusPerHit = ",
        f"{r['combo_bonus_per_hit']}",
        "f;\n\t// Turn economy\n\tconstexpr int32 BaseAV = ",
        f"{t['base_av']}",
        ";\n\tconstexpr int32 SharedSPStart = ",
        f"{t['shared_sp_start']}",
        ";\n\tconstexpr int32 SharedSPMax = ",
        f"{t['shared_sp_max']}",
        ";\n\t// Songcraft\n\tconstexpr int32 CrescendoMax = ",
        f"{s['crescendo_max']}",
        ";\n\tconstexpr int32 CrescendoGainPerfect = ",
        f"{s['crescendo_gain']['perfect']}",
        ";\n\tconstexpr int32 CrescendoGainGreat = ",
        f"{s['crescendo_gain']['great']}",
        ";\n\tconstexpr int32 CrescendoGainGood = ",
        f"{s['crescendo_gain']['good']}",
        ";\n\tconstexpr int32 CrescendoGainMiss = ",
        f"{s['crescendo_gain']['miss']}",
        ";\n\t// Ultimate\n\tconstexpr float UltGainPerHit = ",
        f"{u['gain_per_hit']}",
        "f;\n\tconstexpr float UltGainPerfect = ",
        f"{u['gain_perfect']}",
        "f;\n\tconstexpr float UltMax = ",
        f"{u['max']}",
        "f;\n\tconstexpr float UltDamageMult = ",
        f"{u['damage_mult']}",
        "f;\n\t// Toughness\n\tconstexpr float ToughnessReduction = ",
        f"{tough['reduction']}",
        "f;\n\tconstexpr float ToughnessBrokenEnemyDamageMult = ",
        f"{tough['broken_enemy_damage_mult']}",
        # RESTORED 2026-07-31: this block is NOT part of the recovered original.
        # The seven Opening* constants had been hand-added to MelodiaRulesGenerated.h
        # in violation of its own DO-NOT-EDIT header, so the generator did not emit
        # them and regenerating would have deleted them -- breaking four callers:
        # MelodiaBattleSession.cpp, MelodiaCoreRulesTests.cpp, MelodiaFirstDungeonGate.cpp,
        # MelodiaOpeningFlowSubsystem.cpp. Every value comes from rules["opening_flow"],
        # so emitting them here restores the single-source-of-truth contract in _meta.
        "f;\n\t// Authored opening flow\n\tconstexpr const TCHAR* OpeningMorningLevel = ",
        f"{_cstr(o['morning_level'])}",
        ";\n\tconstexpr const TCHAR* OpeningDreamstateLevel = ",
        f"{_cstr(o['dreamstate_level'])}",
        ";\n\tconstexpr const TCHAR* OpeningZenLevel = ",
        f"{_cstr(o['zen_level'])}",
        ";\n\tconstexpr const TCHAR* OpeningTutorialEnemyId = ",
        f"{_cstr(o['tutorial_enemy_id'])}",
        ";\n\tconstexpr const TCHAR* OpeningTutorialQuestId = ",
        f"{_cstr(o['tutorial_quest_id'])}",
        ";\n\tconstexpr int32 OpeningFirstDungeonSeed = ",
        f"{_i(o['first_dungeon_seed'])}",
        ";\n\tconstexpr int32 OpeningHeartTokensOnUnlock = ",
        f"{_i(o['heart_tokens_on_unlock'])}",
        ";\n",
        f"{skill_block}",
        "\n",
        f"{mod_block}",
        "\n}\n",
    ])

    OUT_H.write_text(h, encoding="utf-8")

    py = (
        f'"""GENERATED by Tools/generate_melodia_rules.py — DO NOT EDIT.\n'
        f"Edit Plugins/MelodiaCore/Rules/melodia_rules.json and regenerate.\n"
        f'"""\n'
        f"RULES = "
        f"{json.dumps({k: v for k, v in rules.items() if not k.startswith('_')}, indent=2)}"
        f"\n"
    )

    OUT_PY.write_text(py, encoding="utf-8")
    print(f"wrote {OUT_H.relative_to(ROOT)}")
    print(f"wrote {OUT_PY.relative_to(ROOT)}")

    import sys

    sys.path.insert(0, str(ROOT / "Tools"))
    from export_melodia_rhythm_web_config import export_web_config

    web_out = export_web_config(rules)
    print(f"wrote {web_out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
