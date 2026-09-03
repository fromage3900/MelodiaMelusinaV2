# Campaign 4 — Result Matrix (terminal results)

**Gate id:** `runtime` (completes the `runtime` row begun by Campaign 1)
**Requirement:** `_VERTICAL_SLICE_SCOPE.md` — Victory, Defeat, Fled, and
unavailable; each resumes/aborts Quill **exactly once**; no duplicate
dialogue, no double-resume, no lost pending result.

## Preconditions

1. Campaign 1 recorded (the battle plays).
2. `python Tools/echo_run.py status` → editor reachable.
3. The B4 closure wiring is in place (`verify_battle_closure.py` 10/10 on the
   live graph: `Switch → Sequence_3/4/5 → CompleteBattle` + PlayerWon/EnemyWon/
   Keys legs). Graph-connected is not play-proven — that is what this campaign
   does.

## Matrix

| Terminal | How to reach | Must observe |
|---|---|---|
| Victory | Win the encounter | Quill resumes exactly once; `melodia:flag` consequence applied once |
| Defeat | Party wipe → confirm | One `CompleteBattle` leg; no duplicate confirmation |
| Fled | Flee succeeds | Keys leg (dead-unit rewards are authored design); Quill resumes once |
| Unavailable | Encounter requested when battle can't start (unregistered id / no tagged actor) | Typed authored safe path; no fabricated result |

## Anti-checks (the defect classes that shipped before)

1. **No double Quill resume** — `Restore()` + `Next()` exactly once per
   terminal result. Count them in the log.
2. **No stub-silent defeat** — `BP_DefeatDialogue` must not be a no-op
   (`OpenLevel` pin fed by a live `mainMenuMapName`).
3. **Interpreter invalidation during terminal broadcast** — a recoverable
   pending result must survive a failed Quill resume, not vanish.
4. **Manual save disabled during active narrative battle** — the save UI must
   not allow mid-battle saves.

## Record

```text
python Tools/echo_run.py record runtime pass --note "Victory/Defeat/Fled/unavailable matrix: each resumes/aborts Quill exactly once"
```

This pass **replaces** the Campaign 1 `runtime` row's status (latest row wins
in the ledger views). If any cell of the matrix fails, record `fail` with the
cell and the log evidence.
