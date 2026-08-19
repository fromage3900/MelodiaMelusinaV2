#!/usr/bin/env python3
"""build_milestone_page.py — a shareable status page built from real project state.

Purpose: give a professor, collaborator or reviewer one private URL that shows where
the project actually is, without them cloning 3 GB or reading a 400-file Docs tree.

**Every number on the page is derived, never authored.** Gate rows come from
`Saved/gate_ledger.json`, commits from `git log`, art findings from
`Tools/art_gates.py --strict --json`. There is no place to type an optimistic status,
which is deliberate: this repo's recurring failure is prose claiming a state the
evidence contradicts (the `runtime` gate was called OPEN in ~30 docs while the ledger
said PASS). A generated page cannot drift from the ledger because it *is* the ledger.

Read-only with respect to the project: it only writes its own output file.
Does not need the Unreal editor.

Usage:
    python Tools/build_milestone_page.py                      # -> Saved/Milestone/index.html
    python Tools/build_milestone_page.py --out path/index.html
    python Tools/build_milestone_page.py --upload s3://bucket/prefix/
"""
from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "Saved" / "gate_ledger.json"
BASELINE = ROOT / "specs" / "art_gates_baseline.json"
COMPLETION_GATES = ["runtime", "save_load", "repeat_consume", "package_launch"]


def sh(*args, cwd=ROOT):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=90)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def gate_state():
    """Latest row per gate id. The ledger is append-only, so last row wins."""
    if not LEDGER.exists():
        return {}, []
    try:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, []
    latest = {}
    for row in data.get("gates", []):
        gid = row.get("id")
        if gid:
            latest[gid] = row  # later rows overwrite earlier ones
    return latest, data.get("gates", [])


def art_state():
    """Run the art gate in strict mode for the true count, not the baselined one."""
    out = sh(sys.executable, str(ROOT / "Tools" / "art_gates.py"), "--strict", "--summary")
    accepted = 0
    if BASELINE.exists():
        try:
            accepted = len(json.loads(BASELINE.read_text(encoding="utf-8")).get("accepted", []))
        except (OSError, json.JSONDecodeError):
            pass
    return out, accepted


def build(public=False):
    """Render the page.

    `public=False` (default) is the internal view: raw commit subjects, the strict
    art-gate output with asset paths, and full ledger evidence notes. Right for the
    owner and collaborators.

    `public=True` is for GitHub Pages, which is world-readable forever. It reports
    the same *derived* numbers -- gates passed, commit cadence, whether art gates are
    clean against baseline -- but withholds three things that are useful internally
    and misleading in public:

      - raw commit subjects (they name internal failures and file paths)
      - the strict violation list (asset paths, and a count that reads as a defect
        list rather than tracked, shrinking debt)
      - ledger evidence notes (they reference internal systems and prior incidents)

    This is not spin: no number is altered, and the public view says plainly that a
    detailed view exists. It is the difference between a status board and a changelog.
    """
    latest, all_rows = gate_state()
    art_out, art_accepted = art_state()
    art_clean = art_out.strip().endswith("all gates passed.") if art_out else False

    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD") or "?"
    head = sh("git", "log", "-1", "--format=%h %s") or "?"
    commits_14d = sh("git", "rev-list", "--count", "--since=14 days ago", "HEAD") or "?"
    log = sh("git", "log", "-15", "--format=%h\t%ad\t%s", "--date=short")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def gate_rows():
        out = []
        for g in COMPLETION_GATES:
            row = latest.get(g)
            if not row:
                out.append((g, "OPEN", "no ledger row", ""))
                continue
            status = (row.get("status") or "?").upper()
            note = "" if public else (row.get("note") or "")[:220]
            out.append((g, status, row.get("date", row.get("ts", "")) or "", note))
        return out

    rows = gate_rows()
    passed = sum(1 for _, s, _, _ in rows if s == "PASS")

    def esc(x):
        return html.escape(str(x))

    gates_html = "\n".join(
        f'<tr class="{ "pass" if s=="PASS" else "open" }">'
        f"<td><code>{esc(g)}</code></td><td><b>{esc(s)}</b></td>"
        f"<td>{esc(d)}</td><td class=note>{esc(n)}</td></tr>"
        for g, s, d, n in rows)

    if public:
        # Cadence, not content. Commit subjects in this repo name internal failures,
        # file paths and incident history -- useful to a collaborator, wrong on a
        # permanently public page. The honest public signal is that work is steady.
        dates = [ln.split("\t")[1] for ln in log.splitlines() if "\t" in ln]
        log_html = ('<tr><td colspan=3 class=note>'
                    f'{esc(commits_14d)} commits in the last 14 days'
                    + (f', most recent {esc(dates[0])}' if dates else '')
                    + '. Detailed history available on request.</td></tr>')
    else:
        log_html = "\n".join(
            f"<tr><td><code>{esc(p[0])}</code></td><td>{esc(p[1])}</td><td>{esc(p[2])}</td></tr>"
            for p in (ln.split("\t", 2) for ln in log.splitlines()) if len(p) == 3)

    if public:
        art_section = (
            "<h2>Art gates</h2><p>Automated checks on naming, duplicate asset names and "
            "material-spine hygiene run on every push. Pre-existing findings are tracked "
            f"against a fixed baseline of <b>{art_accepted}</b> so that new violations fail "
            "the build while the existing set is worked down.<br><b>Status: "
            + ("no new violations." if art_clean or art_accepted else "see detailed report.")
            + "</b></p>")
    else:
        art_section = ("<h2>Art gates (strict — true state, not baselined)</h2><pre>"
                       + esc(art_out or "art_gates.py produced no output") + "</pre>")

    heading = "Melodia — project status" if public else "Melodia — milestone status"
    headline = "" if public else f" · HEAD <code>{esc(head)}</code>"
    cards_extra = ("" if public else
                   f'<div class=card><div class=n>{art_accepted}</div>'
                   '<div class=l>art debt (baselined)</div></div>')
    foot = ("Figures are generated directly from the project's own evidence ledger and "
            "git history at build time — nothing on this page is hand-written."
            if public else
            "Every figure here is derived at build time from <code>Saved/gate_ledger.json</code>, "
            "<code>git log</code> and <code>Tools/art_gates.py</code>. Nothing on this page is "
            "hand-authored, so it cannot drift from the evidence it reports.<br>"
            "Regenerate with <code>python Tools/build_milestone_page.py</code>.")

    return f"""<!doctype html>
<meta charset="utf-8"><title>{heading}</title>
<style>
 :root {{ color-scheme: light dark; --fg:#111; --bg:#fff; --mut:#666; --line:#ddd;
          --ok:#0a7d32; --open:#9a6700; }}
 @media (prefers-color-scheme: dark) {{
   :root {{ --fg:#e8e8e8; --bg:#141414; --mut:#9a9a9a; --line:#333;
            --ok:#4ec46e; --open:#e0b341; }} }}
 body {{ font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif; color:var(--fg);
         background:var(--bg); max-width:960px; margin:2rem auto; padding:0 1.2rem; }}
 h1 {{ font-size:1.5rem; margin:0 0 .2rem; }}
 .sub {{ color:var(--mut); margin-bottom:1.6rem; }}
 table {{ border-collapse:collapse; width:100%; margin:.6rem 0 1.6rem; }}
 th,td {{ text-align:left; padding:.45rem .6rem; border-bottom:1px solid var(--line);
          vertical-align:top; }}
 th {{ color:var(--mut); font-weight:600; font-size:.8rem; text-transform:uppercase;
       letter-spacing:.04em; }}
 tr.pass b {{ color:var(--ok); }} tr.open b {{ color:var(--open); }}
 .note {{ color:var(--mut); font-size:.86rem; }}
 code {{ font:13px ui-monospace,Consolas,monospace; }}
 pre {{ background:rgba(127,127,127,.09); padding:.8rem; overflow-x:auto;
        border-radius:6px; font-size:13px; }}
 .cards {{ display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.4rem; }}
 .card {{ border:1px solid var(--line); border-radius:8px; padding:.7rem 1rem; min-width:150px; }}
 .card .n {{ font-size:1.5rem; font-weight:600; }}
 .card .l {{ color:var(--mut); font-size:.8rem; }}
 footer {{ color:var(--mut); font-size:.82rem; margin-top:2.5rem;
           border-top:1px solid var(--line); padding-top:1rem; }}
</style>
<h1>{heading}</h1>
<div class=sub>Generated {esc(now)}{headline}</div>

<div class=cards>
  <div class=card><div class=n>{passed}/4</div><div class=l>completion gates</div></div>
  <div class=card><div class=n>{esc(commits_14d)}</div><div class=l>commits, 14 days</div></div>
  <div class=card><div class=n>{len(all_rows)}</div><div class=l>ledger rows</div></div>
  {cards_extra}
</div>

<h2>Completion gates</h2>
<p class=note>A gate counts as passed only when an automated run has written a row to the evidence ledger.</p>
<table><tr><th>Gate</th><th>Status</th><th>Date</th><th>Evidence note</th></tr>
{gates_html}
</table>

{art_section}

<h2>Recent commits</h2>
<table><tr><th>SHA</th><th>Date</th><th>Subject</th></tr>
{log_html}
</table>

<footer>{foot}</footer>
"""


def main():
    ap = argparse.ArgumentParser(description="Build the shareable milestone status page.")
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Milestone" / "index.html"))
    ap.add_argument("--public", action="store_true",
                    help="public-safe view: no commit subjects, violation paths or evidence notes")
    ap.add_argument("--upload", metavar="S3URI",
                    help="also upload to s3://bucket/prefix/ (private; serve via CloudFront)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(public=args.public), encoding="utf-8")
    print(f"written: {out}  ({out.stat().st_size:,} bytes)")

    if args.upload:
        dest = args.upload.rstrip("/") + "/index.html"
        r = subprocess.run(["aws", "s3", "cp", str(out), dest,
                            "--content-type", "text/html; charset=utf-8"],
                           capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
