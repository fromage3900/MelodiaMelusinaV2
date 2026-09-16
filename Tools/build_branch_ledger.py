"""Read-only remote inventory. Never closes PRs or removes refs."""
import collections
import datetime
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8").strip()


def main():
    baseline = git("rev-parse", "origin/main")
    live = {remote + "/" + ref.removeprefix("refs/heads/"): sha
            for remote in git("remote").splitlines()
            for sha, ref in (line.split() for line in git("ls-remote", "--heads", remote).splitlines())}
    prs = json.loads(subprocess.check_output([
        "gh", "pr", "list", "--repo", "fromage3900/MelodiaMelusinaV2", "--state", "open",
        "--limit", "1000", "--json", "number,title,url,headRefName,baseRefName,headRefOid"], text=True))
    rows = []
    for ref in git("for-each-ref", "--format=%(refname:short)", "refs/remotes").splitlines():
        if ref.endswith("/HEAD"):
            continue
        sha = git("rev-parse", ref)
        if ref not in live:
            rows.append(dict(ref=ref, sha=sha, classification="dead", remote_exists=False,
                             unique_patch_commits=[], files=[],
                             recommendation="remote already absent; prune cached tracking ref only after owner approval"))
            continue
        if ref in live and sha != live[ref]:
            raise RuntimeError(f"Remote changed; fetch then repeat: {ref}")
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", sha, baseline]).returncode
        if ancestor not in (0, 1):
            raise RuntimeError(f"Ancestry check failed for {ref}")
        unique = []
        files = []
        if ancestor:
            unique = [line[2:] for line in git("cherry", baseline, sha).splitlines() if line.startswith("+ ")]
            # Branch-authored changes since divergence, not reverse deletions of newer main work.
            common = subprocess.run(["git", "merge-base", baseline, sha], capture_output=True, text=True)
            if common.returncode not in (0, 1):
                raise RuntimeError(f"Merge base failed for {ref}")
            changed = (git("diff", "--no-renames", "--name-only", common.stdout.strip(), sha).splitlines()
                       if common.returncode == 0 else git("ls-tree", "-r", "--name-only", sha).splitlines())
            tip_diff = set(git("diff", "--no-renames", "--name-only", baseline, sha).splitlines())
            files = sorted(set(changed) & tip_diff) if unique else []
        classification = "unique-work" if files else "merged-equivalent"
        protected_lane = ref == "origin/main" or "collab/laptop/longterm" in ref
        rows.append(dict(ref=ref, sha=sha, classification=classification, remote_exists=ref in live,
                         unique_patch_commits=unique, files=files,
                         recommendation="retain canonical/workstation lane" if protected_lane else
                         ("reconcile selected files; never merge wholesale" if files else "close/archive after owner approval")))
    by_ref = {r["ref"]: r for r in rows}
    if set(live) - set(by_ref):
        raise RuntimeError("Missing live branches; fetch before auditing")
    for pr in prs:
        row = by_ref.get("origin/" + pr["headRefName"])
        if row is None or row["sha"] != pr["headRefOid"]:
            raise RuntimeError(f"PR head missing/stale; fetch before audit: {pr['number']}")
        pr.update({key: row[key] for key in ("classification", "files", "recommendation")})
    output = Path("Docs/Evidence/BRANCH_LEDGER_2026-09-13.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(
        schema="melodia.branch_ledger.v1", captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        live_branch_count=len(live), cached_ref_count=len(rows),
        baseline=baseline, method="Ancestry then git cherry patch equivalence. Files are branch-authored paths still differing at tip; unique-work is a reconciliation candidate, not a claim every hunk is wanted. No branch deemed dead without owner disposition.",
        open_prs=prs, remote_branches=rows), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(path=str(output), branches=len(rows), open_prs=len(prs),
                         counts=dict(collections.Counter(r["classification"] for r in rows)))))


if __name__ == "__main__":
    main()
