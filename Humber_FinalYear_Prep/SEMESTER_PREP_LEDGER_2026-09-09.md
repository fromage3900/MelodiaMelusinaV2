# SEMESTER PREP LEDGER — 2026-09-09 (the "long game" file)

Scorecard: prepped where the song is written, shaky where it isn't.
This file tracks what's DONE, what's THE ONE THING, and what future-week
work is pre-staged so each deadline is a polish, not a panic.

## 1) Readiness scorecard

| Lane | State | Evidence |
|---|---|---|
| Schedule truth | ✅ | Banner-verified 4-of-6; Desk widget renders week + countdown live |
| Missing courses (306/309) | 🔴 OPEN | Add-by **Sep 14**. Paste-ready Teams message in ANMN301_REEL_COURSE_BRIEF (co-req argument). Owner sends. |
| COE/OSAP part-time error | 🟡 | Raised in same Cory message. Payment/OSAP check still behind NTID password wall. |
| Applications | ✅ drafts | 9 composed, 0 sent (verified Sent-folder empty). Send order in Docs/Career/APPLICATION_EMAIL_DRAFTS_2026-09-09.md |
| Git spine | ✅ | GIT_TIMELINE_SEM5.md: W1→W15 map, branch policy, Friday squash/tag, Sunday verify |
| Autonomous runners | ✅ | 8:30 daily brief · Sun 19:00 review + 3 MUSTS · Mon 9:00 role scout · all feed WEEKLY_LOG.md → Desk |
| Desktop command center | ✅ | Melusina Desk 4 panels (countdown/week, stickies, portals, gate harp) |
| Assignment head-start | 🟡 staged | 301 Animatic (25%) plan written, NOT executed. 305/304/302 shells shallow-read. |
| **Disk space** | 🔴 CRITICAL | **C: 24.8 GB free / 928.** UE5 builds + PIE saves + render output need ~80-100 GB breathing room. D: 416 GB free, G: 304 GB free. |

## 2) Disk surgery plan (C: → targets) — SCANNED FACTS 2026-09-09 17:0x

Measured: C: free **24.8 GB**. pagefile.sys **36 GB** (C:) · Epic: UE_5.8 **37.1** (KEEP — engine)
· Twinmotion2026.1 **8.4** · DuetNightAbyss **4.1** · RealityScan 0.6 · Twinmotion 2023/24 ~0
· BS_GodFile\\Saved: **Audit 21.5 GB** (the whale), Smartsuit pkg 2.8, Screenshots 0.4
· Downloads 7.7 GB · Temp 4.1 GB · .ollama ~0 on C: · D: 416 free · G: 304 free

Best-value order: 1) Saved\\Audit stale renders→D: (−15-20 GB) 2) pagefile cap 12 GB or move D:
(−24 GB) 3) uninstall Twinmotion/DNA/RealityScan if unused (−13 GB) 4) Temp sweep (−4) 5) Downloads
→D:\\downloads sort (−5+) 6) Storage Sense/Update leftovers (−3-10).

### SURGERY DONE (2026-09-09 evening) — C: 24.8 → 27.6 GB free, net +2.8 after a VS installer ate ~11 mid-sweep
- DONE: VS Installer Packages cache cleared (−10.4 GB, elevated) · dead VS install channel in
  Temp `cqhwgfcg` (−3.7) · Temp >2day sweep (−4.1→0.4) · Code logs · rmbak rescued to
  MelusinaWorkspace. OWNER RULE LEARNED: **Saved/Audit is OFF-LIMITS for moves/deletes** (whale
  is git-tracked `substance_staging` 8.5 GB + `bake` 1.4 + lookdev blends; 7.6 GB untracked .blend
  corpses exist there but owner said don't touch — respected).
- REMAINING, in size order (owner's call): pagefile 36 GB→12 GB cap (needs reboot, ~+24 GB —
  current real usage only 2.8 GB) · Twinmotion2026.1 8.4 + DuetNightAbyss 4.1 + RealityScan 0.6
  (uninstall if truly unused, +13) · Downloads 7.7 GB → D:\\downloads · WinUpdate cache 1.1 ·
  `~\\.cache\\codex-runtimes` 1.28 + `~\\.codex\\sessions` 0.61 (agent history — ask before).
- Target ≥120 GB free before Dec renders → the pagefile + Epic-uninstalls + Downloads trio gets
  ~45 GB of it; the rest is Saved (owner-gated) or drive-relocation policy (Epic engines install
  to D: going forward).
- Note: a `disk_report2.txt` full-drive scan (D:/G:) ran in background; D:\\game 499 GB +
  D:\\music 256 + kontakt 170 + downloads 120 + Wuthering 104 + humber animation 100 = D: is
  mostly games+music, still 416 GB free.

## 2b) old estimates kept for context

| Target | Est. gain | Risk | How |
|---|---|---|---|
| `C:\...\Temp` (4.1 GB) | ~4 GB | none | clean old + ours (panel logs, crops). Safe now. |
| Recycle Bin | ? | none | `Clear-RecycleBin` |
| Downloads 7.7 GB | ~7 GB | low | move (not delete) the big media to D:; keep installers you actually need |
| Epic engine versions | 10-20 GB | medium | uninstall engines NOT used by BS_GodFile (keep UE_5.8 + whatever plugin builds need). Verify list first. |
| `BS_GodFile\Saved` 26.5 GB | ~10-15 GB | medium | Autosaves/Backup/Logs/old CrashLogs + stale PIE captures → move to D:. NEVER touch `Saved/gate_ledger.json`, `Saved/Echo`, `Saved/Daemon`, `Saved/Recovery`. |
| uv/pip/npm/agent caches | ~5-10 GB | low | `uv cache clean`, npm cache verify-clean, stray .claude/.codex/.cursor logs |
| Hibernation file | 6-32 GB | low-medium | `powercfg /h off` (or shrink to 40%) — kills fast-startup hiberfil |
| Windows Update leftovers / Storage Sense | 3-10 GB | low | Disk Cleanup as admin (previous installs, delivery optimization) |
| Ollama models (.ollama) | ? | KEEP | daemon lane depends on qwen3:8b + coder:30b — leave |
| _TouchDesigner frozen copy | ? | ask | memory says "never cite"; if >20 GB on C:, move to G:/archive — OWNER CALL |

Rule of thumb: free ≥120 GB on C: before Dec renders.

## 3) Pre-staged future assignments (the actual "head start ×2")

- **301 Animatic Story Edit (25%, DUE Fri OCT 9, 5 PM — confirmed from assignment page; brief's
  "~Sep 25" guess was wrong)** — plan exists (REEL_COURSE_BRIEF §head-start + VERIFIED RULES: MP4
  1920x1080@24, silent, ShepherdBrennan_AnimaticCreation_2026-10-09, title+end cards, <=3 fades,
  pacing table). Doubles as Capstone beat-board. Real prerequisite: the short film's storyboard
  panels ("your full set from your short film project") — logline+panels must exist first, which
  IS the W1 tracker task. 10-15 h recommended, so a 2-week runway from Sep 25.
- **301 Audio & Sync (15%, W4-6)** — reuse animatic scratch audio; extend the 30-sec pass.
- **301 Titles/Credits/Export (15%, W7-9)** — nothing to do yet; the export-spec habit now = free later.
- **301 Curation Plan (15%) + Final Reel (30%, W12-14)** — the reel shots table in
  Capstone_Portfolio_Tracker.md is EMPTY. Filling shot concepts IS the plan; do 1 shot/week from
  existing Melodia renders (shot 5 = capstone hero = Sea Above / KaleidoNave beauty pass).
- **302 (Avery)** — join Teams fwkqj0s now; outline PDF unread → next sweep.
- **304 (Par)** — "content on the way"; nothing pre-staged is possible.
- **305 (Corbett) History** — week-1 notes live; the unread Discussion = first cheap grade point.
  Critical Path PDF on shell → read, fill deadlines into tracker.
- **306 Capstone 1** — gated on registration. When it lands: tracker's Pre-prod rows already map W1-W4.
- **309 Career Connections** — resume + variants pipeline already drafted (Docs/Career). Its deliverables are ~80% pre-made.

## 4) Standing weekly rhythm (already running)

Daily 8:30 brief → WEEKLY_LOG.md · Sun 19:00 review + next 3 MUSTS · Mon 9:00 role scout ·
Friday git squash-merge + tag · Sunday backup drive check (D:/G:).

## 5) Do-not-touch list

Unsent Gmail drafts (9) · Saved/gate_ledger.json + Echo + Daemon + Recovery · .ollama models ·
frozen _TouchDesigner (move only with owner OK) · git: no clean/checkout -- . ever.
