#!/usr/bin/env python3
"""Read-only GitHub bounty lead scout for the existing Fromage WebGL Treasury.

Uses only the GitHub public search API (or a local --input fixture) and Python
stdlib. This is lead discovery, NOT proof that a bounty is funded, payable,
available to this contributor, or allowed to use AI. It never posts, applies,
spends, runs issue instructions, or updates TREASURY_LEDGER.json.

Examples:
  python Website/fromage-webgl-kit/scripts/bounty_scout.py --live
  python Website/fromage-webgl-kit/scripts/bounty_scout.py --input issues.json
  python Website/fromage-webgl-kit/scripts/bounty_scout.py --live --output local-scout.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.github.com/search/issues"
QUERIES = (
    "is:issue is:open label:bounty",
    "is:issue is:open bounty in:title",
)
ISSUE_URL = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)$")
MONEY = re.compile(r"(?<![\w])(?:(?:USD|CAD)\s*)?(?:US|CA)?\$\s*(\d[\d,]*(?:\.\d{1,2})?)\b", re.I)
FUNDING_URL = re.compile(r"https://(?:www\.)?(?:algora\.io|opencollective\.com)/[^\s)\]>]+", re.I)
MIRRORS = {"bounty-plaza", "bountyscout"}
SPAM = (
    "pppdud", "eleventy gazillion", "negative bounty",
    "bounty expiry is 30 minutes", "pay me $", "follow my github account",
    "infinity dollars", "infinite reward", "bounty for $100000",
)
PRIMARY = ("python", "blender", "houdini", "glb", "gltf", "three.js", "webgl",
           "shader", "unreal", "geometry nodes", "pytest", "cli")
SECONDARY = ("typescript", "javascript", "node.js", "test suite", "json", "api")


def _date(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _claimed_reward(text: str) -> tuple[float, str, str] | None:
    """Extract a plausible advertised amount, NEVER an audited payout."""
    matches = list(MONEY.finditer(text))
    for match in matches:
        amount = float(match.group(1).replace(",", ""))
        if not 20 <= amount <= 5000:
            continue
        context = text[max(0, match.start() - 8):min(len(text), match.end() + 8)].upper()
        currency = "USD" if "US$" in context or "USD" in context else (
            "CAD" if "CA$" in context or "CAD" in context else "UNKNOWN"
        )
        return amount, currency, match.group(0).strip()
    return None


def assess(issue: dict, *, now: datetime | None = None) -> dict | None:
    """Return a lead requiring human review, or None for an unsafe/weak lead."""
    now = now or datetime.now(timezone.utc)
    url = issue.get("html_url") or issue.get("display_url") or ""
    match = ISSUE_URL.fullmatch(url)
    if not match or issue.get("pull_request"):
        return None
    owner, repo, number = match.groups()
    if repo.lower() in MIRRORS or issue.get("state") not in ("open", None):
        return None
    if issue.get("assignee") or issue.get("assignees"):
        return None

    title = issue.get("title") or ""
    body = issue.get("body") or ""
    if not isinstance(title, str) or not isinstance(body, str):
        return None
    text = (title + "\n" + body)[:12000]
    lower = text.lower()
    if any(term in lower for term in SPAM):
        return None
    if "原始链接 / source url" in lower or "coin reward" in lower:
        return None
    if not re.search(r"\bbounty\b|\bpaid issue\b", title, re.I):
        return None

    updated = _date(issue.get("updated_at"))
    if not updated or not now - timedelta(days=90) <= updated <= now + timedelta(days=2):
        return None

    reward = _claimed_reward(title) or _claimed_reward(body)
    if reward is None:
        return None
    amount, currency, claimed = reward
    labels = [x.get("name", "") if isinstance(x, dict) else str(x)
              for x in (issue.get("labels") or [])]
    if any("assigned" in label.lower() or "claimed" in label.lower() for label in labels):
        return None

    primary = any(word in lower for word in PRIMARY)
    secondary = any(word in lower for word in SECONDARY)
    broad = any(word in lower for word in ("rewrite entire", "full platform", "complete ecosystem", "production system"))
    bounded = any(word in lower for word in ("acceptance", "reproduc", "test", "steps to", "done when", "fix "))
    complex_integration = any(word in lower for word in ("gpu hardware", "kernel driver", "requires nvidia",
                                                        "custom silicon", "mainnet", "on-chain"))
    scores = {
        "capability_match": 2 if primary else (1 if secondary else 0),
        "existing_proof": 2 if any(w in lower for w in ("python", "blender", "webgl", "gltf", "glb")) else (1 if secondary else 0),
        "scope_boundedness": 0 if broad else (2 if bounded else 1),
        "sponsor_credibility": 1,  # Github issue ownership is NOT funding verification.
        "budget_adequacy": 2 if amount >= 100 else 1,
        "reuse_potential": 2 if any(w in lower for w in ("test", "fix", "cli", "tool")) else 1,
        "low_legal_ip_risk": 1,  # License, AI rules, and payment terms still require human review.
        "low_integration_risk": 0 if complex_integration else (2 if primary and bounded else 1),
    }
    total = sum(scores.values())
    fund_match = FUNDING_URL.search(text)
    return {
        "issue_url": url,
        "repo": owner + "/" + repo,
        "number": int(number),
        "title": title[:240],
        "updated_at": issue.get("updated_at"),
        "claimed_reward": {"amount": amount, "currency": currency, "source_text": claimed},
        "funding_link_for_manual_check": fund_match.group(0).rstrip(".,") if fund_match else None,
        "funding_verification": "UNVERIFIED",
        "eligibility_and_ai_rules": "UNVERIFIED",
        "scores": scores,
        "score_out_of_16": total,
        "status": "REVIEW_PAYMENT" if total >= 13 else ("WATCH" if total >= 9 else "IGNORE"),
        "human_gate": "Verify sponsor, actual escrow/terms, payout country, AI policy, issue ownership, open PRs, and test feasibility before contacting or coding.",
    }


def discover(per_query: int) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Melodia-Treasury-ReadOnly-Scout"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    found: list[dict] = []
    for query in QUERIES:
        url = API + "?" + urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": per_query})
        try:
            with urlopen(Request(url, headers=headers, method="GET"), timeout=15) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"GitHub public issue discovery unavailable; no changes made: {exc}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise RuntimeError("Unexpected GitHub search response; no changes made.")
        found.extend(payload["items"])
    return found


def shortlist(issues: list[dict], *, top: int = 3, now: datetime | None = None) -> dict:
    if not isinstance(issues, list):
        raise ValueError("Expected a JSON list of GitHub issues")
    dedup: dict[str, dict] = {}
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        lead = assess(issue, now=now)
        if lead and lead["status"] != "IGNORE":
            key = lead["issue_url"].lower()
            if key not in dedup or dedup[key]["score_out_of_16"] < lead["score_out_of_16"]:
                dedup[key] = lead
    ranked = sorted(dedup.values(), key=lambda item: (-item["score_out_of_16"],
                     -item["claimed_reward"]["amount"], item["issue_url"]))
    return {
        "schema": "melodia.treasury_bounty_scout.v1",
        "discovery_count": len(issues),
        "candidates_after_gates": len(ranked),
        "shortlist": ranked[:top],
        "money_received": 0,
        "warning": "Lead-only screening. All payment, country, rules and availability remain unverified. Never post a PR, claim a bounty, or spend automatically.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true", help="Read GitHub public issue search (no writes)")
    source.add_argument("--input", type=Path, help="Offline JSON issue list or GitHub search {items: [...]} fixture")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--per-query", type=int, default=20)
    parser.add_argument("--output", type=Path, help="Optional report output; no file written by default")
    args = parser.parse_args(argv)
    if not 1 <= args.top <= 10 or not 1 <= args.per_query <= 30:
        parser.error("--top must be 1..10 and --per-query 1..30")
    try:
        if args.live:
            issues = discover(args.per_query)
        else:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            issues = payload.get("items", []) if isinstance(payload, dict) else payload
        result = shortlist(issues, top=args.top)
        content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            sys.stdout.write(content)
        return 0
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        print(f"[bounty_scout] HOLD: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
