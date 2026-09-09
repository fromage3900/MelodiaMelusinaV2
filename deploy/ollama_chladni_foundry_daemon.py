"""Chladni pattern foundry daemon (P0 Sheep pitch-C proof support).
Output: Imports/Data/Chladni/*.json + *.svg - Stop: deploy/OLLAMA_CHLADNI_STOP or deploy/STOP_ALL
Deterministic nodal-pattern solver (square-plate marching squares + exact circular-membrane
nodal sets), Board-02 legibility ranking, qwen3:8b display names (soft-fail). Drafts only:
no .uasset writes, no gate certification, no runtime authority.
Schema: MelodiaChladniSheet-draft-v1
"""
from __future__ import annotations
import argparse
import json
import math
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Imports" / "Data" / "Chladni"
STOPS = [ROOT / "deploy" / "OLLAMA_CHLADNI_STOP", ROOT / "deploy" / "STOP_ALL"]
LOG = ROOT / "deploy" / "ollama_chladni.log"
MODEL, MODEL_FALLBACK = "qwen3:8b", "qwen2.5-coder:7b"
API = "http://127.0.0.1:11434/api/generate"
CAP, SLEEP_S = 48, 4
SCHEMA = "MelodiaChladniSheet-draft-v1"

PALETTE = {
    "field": "#F6F0E3",       # ivory paper field (Board 06, Sheet A page language)
    "frame": "#8F83C4",       # thin lavender drafting line (Board 06)
    "blush": "#D98CA6",       # nodal line 1 (Sheet A blush creature language)
    "mauve": "#A96E96",       # nodal line 2
    "lilac": "#7E74C9",       # nodal line 3
    "pearl_shadow": "#B7AC99",  # nodal line 4 (deepened pearl for stroke legibility)
    "cyan": "#4FA8BE",        # driven-point marker ONLY (restrained cyan accent)
}
PALETTE_PROVENANCE = ("derived from BOARD_06 language: ivory field, lavender drafting "
                      "lines, blush/mauve creature, restrained cyan accent; owner review "
                      "required before real texture authoring")
LINE_COLORS = ["blush", "mauve", "lilac", "pearl_shadow"]

PITCH = {"C": 0, "D": 2, "E": 4, "G": 7}


def note_hz(name, octave=4):
    """Equal-temperament frequency, A4 = 440 Hz."""
    semis = PITCH[name] + (octave - 4) * 12
    return round(440.0 * 2 ** ((semis - 9) / 12), 2)


FAMILIES = {
    "C": [("C", 4, 1.0)],
    "C_E": [("C", 4, 1.0), ("E", 4, 0.55)],
    "C_E_G": [("C", 4, 1.0), ("E", 4, 0.6), ("G", 4, 0.45)],
}
SQUARE_MODES = [(1, 1), (1, 2), (2, 2), (1, 3), (2, 3), (3, 3)]
CIRC_MODES = [(0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (3, 1), (2, 2), (0, 3)]
GRID = 192
MIN_NODAL_LEN, MAX_NODAL_LEN = 1.0, 26.0
WEIGHTS = {"order": 0.25, "legibility": 0.20, "negative_space": 0.20,
           "symmetry": 0.25, "coherence": 0.10}


def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True)
    LOG.open("a", encoding="utf-8").write(line + "\n")


def stopped(stops=None):
    return any(s.exists() for s in (stops or STOPS))


def slug(s):
    return re.sub(r"[^A-Za-z0-9_-]", "_", s)


def sample_candidate(rng):
    """One review-grade candidate spec. family/geometry/mode chosen by seeded rng."""
    fam = rng.choices(["C", "C_E", "C_E_G"], weights=[0.5, 0.3, 0.2])[0]
    notes = FAMILIES[fam]
    geom = rng.choices(["square", "circular"], weights=[0.55, 0.45])[0]
    modes = []
    if geom == "square":
        for _ in notes:
            n, m = rng.choice(SQUARE_MODES)
            w = rng.uniform(0.35, 1.0) * rng.choice([1.0, -1.0])
            modes.append({"n": n, "m": m, "w": round(w, 3)})
    else:
        for _ in notes:
            n, p = rng.choice(CIRC_MODES)
            modes.append({"n": n, "p": p,
                          "phase": round(rng.uniform(0.0, math.pi), 3)})
    seed = rng.randrange(0, 16 ** 4)
    if geom == "square":
        mtok = "_".join(f"n{mo['n']}m{mo['m']}" for mo in modes)
    else:
        mtok = "_".join(f"n{mo['n']}p{mo['p']}" for mo in modes)
    cid = f"Chl_{'Sq' if geom == 'square' else 'Cr'}_{mtok}_{fam}_{seed:04x}"
    return {"id": slug(cid), "family": fam, "geometry": geom,
            "notes": [{"name": n, "octave": o, "hz": note_hz(n, o), "amp": a}
                      for n, o, a in notes],
            "modes": modes, "seed": seed}
def square_field(spec, grid=GRID):
    n = grid + 1
    f = [[0.0] * n for _ in range(n)]
    tot = sum(abs(mo["w"]) for mo in spec["modes"]) or 1.0
    for mo in spec["modes"]:
        a = abs(mo["w"]) / tot
        sgn = 1.0 if mo["w"] >= 0 else -1.0
        nn, mm = mo["n"], mo["m"]
        for iy in range(n):
            y, cy = iy / grid, math.cos(mm * math.pi * iy / grid)
            cy2, cx2 = math.cos(nn * math.pi * iy / grid), math.cos(mm * math.pi * iy / grid)
            for ix in range(n):
                cx = math.cos(nn * math.pi * ix / grid)
                term = cx * math.cos(mm * math.pi * iy / grid)
                term2 = math.cos(mm * math.pi * ix / grid) * math.cos(nn * math.pi * iy / grid)
                f[iy][ix] += a * (term + sgn * term2) / 2.0
    return f


def bessel_j(n, x):
    """First-kind Bessel via downward recurrence from a high-order series seed."""
    if x < 0:
        return ((-1) ** n) * bessel_j(n, -x)
    if x == 0:
        return 1.0 if n == 0 else 0.0
    top = n + 40
    f_next, f_cur = 0.0, 1e-300
    vals = [0.0] * (top + 2)
    for k in range(top, -1, -1):
        f_prev = (2.0 * (k + 1) / x) * f_cur - f_next
        vals[k] = f_prev
        f_next, f_cur = f_cur, f_prev
    scale = vals[0] + 2.0 * sum(vals[k] for k in range(2, top + 1, 2))
    norm = 1.0 / scale if scale else 0.0
    return vals[n] * norm


def bessel_zero(n, p):
    """p-th positive zero of J_n by bisection between sign brackets."""
    x, hits, step = 0.05, [], 0.15
    prev = bessel_j(n, x)
    guard = 0
    while len(hits) < p and guard < 5000:
        x += step
        cur = bessel_j(n, x)
        if cur == 0:
            hits.append(x)
        elif prev * cur < 0:
            lo, hi = x - step, x
            for _ in range(60):
                mid = (lo + hi) / 2
                if bessel_j(n, lo) * bessel_j(n, mid) <= 0:
                    hi = mid
                else:
                    lo = mid
            hits.append((lo + hi) / 2)
        prev = cur
        guard += 1
    if len(hits) < p:
        raise ValueError(f"zero not bracketed n={n} p={p}")
    return hits[p - 1]


def circular_analytic(spec):
    """Exact nodal circles + diameter spokes (no grid evaluation needed)."""
    circles, spokes = set(), []
    for mo in spec["modes"]:
        r0 = bessel_zero(mo["n"], mo["p"])
        for j in range(1, mo["p"]):
            circles.add(round(bessel_zero(mo["n"], j) / r0, 6))
        circles.add(1.0)
        if mo["n"] > 0:
            for k in range(2 * mo["n"]):
                ang = mo["phase"] + (k + 0.5) * math.pi / mo["n"]
                spokes.append(round(ang % (2 * math.pi), 6))
    return sorted(circles), sorted(set(spokes))


def marching_squares(f):
    n = len(f) - 1
    segs = []
    for iy in range(n):
        for ix in range(n):
            a, b = f[iy][ix], f[iy][ix + 1]
            c, d = f[iy + 1][ix + 1], f[iy + 1][ix]
            idx = (1 if a > 0 else 0) | (2 if b > 0 else 0) | \
                (4 if c > 0 else 0) | (8 if d > 0 else 0)
            if idx in (0, 15):
                continue
            t, r, bo, l = (ix + (0.0 - a) / (b - a or 1e-12), iy), \
                (ix + 1, iy + (0.0 - b) / (c - b or 1e-12)), \
                (ix + (0.0 - d) / (c - d or 1e-12), iy + 1), \
                (ix, iy + (0.0 - a) / (d - a or 1e-12))
            table = {1: (l, t), 2: (t, r), 3: (l, r), 4: (r, bo), 5: (t, l, r, bo),
                     6: (t, bo), 7: (l, bo), 8: (l, bo), 9: (t, bo), 10: (t, r, l, bo),
                     11: (r, bo), 12: (l, r), 13: (t, r), 14: (l, t)}
            pts = table.get(idx)
            if pts:
                segs.append((pts[0], pts[1]))
                if len(pts) == 4:
                    segs.append((pts[2], pts[3]))
    return segs
def presence_grid(spec, size=48):
    """Coarse nodal-presence bitmap used by all legibility scores."""
    g = [[0] * size for _ in range(size)]

    def mark(x, y):
        ix = min(size - 1, max(0, int(x * size)))
        iy = min(size - 1, max(0, int(y * size)))
        g[iy][ix] = 1

    if spec["geometry"] == "square":
        for (x1, y1), (x2, y2) in marching_squares(square_field(spec)):
            for t in (0.25, 0.5, 0.75):
                mark((x1 + (x2 - x1) * t) / GRID, (y1 + (y2 - y1) * t) / GRID)
    else:
        circles, spokes = circular_analytic(spec)
        for r in circles:
            for a in range(360):
                th = a * math.pi / 180
                mark(0.5 + 0.5 * r * math.cos(th), 0.5 + 0.5 * r * math.sin(th))
        for ang in spokes:
            for i in range(48):
                t = i / 47
                mark(0.5 + 0.5 * t * math.cos(ang), 0.5 + 0.5 * t * math.sin(ang))
    return g


def components(g):
    n = len(g)
    seen = [[False] * n for _ in range(n)]
    sizes = []
    for iy in range(n):
        for ix in range(n):
            if g[iy][ix] and not seen[iy][ix]:
                stack, sz = [(ix, iy)], 0
                seen[iy][ix] = True
                while stack:
                    x, y = stack.pop()
                    sz += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < n and 0 <= ny < n and g[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                sizes.append(sz)
    return sizes


def agreement(g, fn):
    n = len(g)
    same = 0
    for iy in range(n):
        for ix in range(n):
            jy, jx = fn(iy, ix)
            if g[iy][ix] == g[jy][jx]:
                same += 1
    return same / (n * n)


def score_candidate(spec):
    g, n = presence_grid(spec), 48
    pres = sum(sum(row) for row in g)
    if pres == 0:
        return None
    if spec["geometry"] == "square":
        segs = marching_squares(square_field(spec))
        length = sum(math.dist((x1, y1), (x2, y2))
                     for (x1, y1), (x2, y2) in segs) / GRID
        tot = sum(mo["n"] + mo["m"] for mo in spec["modes"])
        order = max(0.0, min(1.0, 1.0 - (tot - 2) / 10.0))
    else:
        circles, spokes = circular_analytic(spec)
        length = sum(2 * math.pi * r for r in circles) + len(spokes)
        tot = sum(mo["n"] + mo["p"] for mo in spec["modes"])
        order = max(0.0, min(1.0, 1.0 - (tot - 1) / 8.0))
    if not (MIN_NODAL_LEN <= length <= MAX_NODAL_LEN):
        return None
    comps = components(g)
    big = sum(s for s in comps if s >= 8)
    legibility = big / pres
    b, blocks, empty = 8, 0, 0
    for by in range(0, n, b):
        for bx in range(0, n, b):
            blocks += 1
            hit = False
            for y in range(by, by + b):
                for x in range(bx, bx + b):
                    if g[y][x]:
                        hit = True
                        break
                if hit:
                    break
            if not hit:
                empty += 1
    negative_space = empty / blocks
    fx = agreement(g, lambda iy, ix: (iy, n - 1 - ix))
    fy = agreement(g, lambda iy, ix: (n - 1 - iy, ix))
    fd = agreement(g, lambda iy, ix: (n - 1 - iy, n - 1 - ix))
    sym = (fx + fy + fd) / 3.0
    coherence = sym if len(spec["modes"]) > 1 else 1.0
    parts = {"order": order, "legibility": legibility,
             "negative_space": negative_space, "symmetry": sym, "coherence": coherence}
    keys = list(parts) if len(spec["modes"]) > 1 else [k for k in parts if k != "coherence"]
    rank = sum(parts[k] * WEIGHTS[k] for k in keys) / sum(WEIGHTS[k] for k in keys)
    return {"rank": round(rank, 4), "nodal_length": round(length, 3),
            "scores": {k: round(v, 4) for k, v in parts.items()}}


def esc(s):
    return xml_escape(str(s))


def xml_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def frame_open():
    return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">',
            f'<rect width="240" height="240" fill="{PALETTE["field"]}"/>',
            f'<rect x="6" y="6" width="228" height="228" fill="none" '
            f'stroke="{PALETTE["frame"]}" stroke-width="1"/>']


def caption(svg, text):
    svg.append(f'<text x="12" y="230" font-family="Georgia,serif" font-size="10" '
               f'fill="{PALETTE["mauve"]}">{esc(text)}</text></svg>')


def join_paths(segs):
    """Chain endpoint-touching segments so SVGs stay small."""
    ends = {}
    for i, ((x1, y1), (x2, y2)) in enumerate(segs):
        ends.setdefault((round(x1, 3), round(y1, 3)), []).append(i)
        ends.setdefault((round(x2, 3), round(y2, 3)), []).append(i)
    paths, used = [], set()
    for i, ((x1, y1), (x2, y2)) in enumerate(segs):
        if i in used:
            continue
        used.add(i)
        path, cur, guard = [(x1, y1), (x2, y2)], (x2, y2), 0
        while guard < 4000:
            guard += 1
            nxt = None
            for j in ends.get((round(cur[0], 3), round(cur[1], 3)), []):
                if j not in used:
                    nxt = j
                    break
            if nxt is None:
                break
            used.add(nxt)
            (ax, ay), (bx, by) = segs[nxt]
            if (round(ax, 3), round(ay, 3)) == (round(cur[0], 3), round(cur[1], 3)):
                go = (bx, by)
            else:
                go = (ax, ay)
            path.append(go)
            cur = go
        paths.append(path)
    return paths


def svg_square(segs, caption_text, color_idx=0):
    S = 240.0 / GRID
    svg = frame_open()
    for i, path in enumerate(join_paths(segs)):
        c = PALETTE[LINE_COLORS[(color_idx + i) % len(LINE_COLORS)]]
        pts = " ".join(f"{p[0] * S:.1f},{p[1] * S:.1f}" for p in path)
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{c}" '
                   'stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>')
    caption(svg, caption_text)
    return "\n".join(svg) + "\n"


def svg_circular(circles, spokes, caption_text, seed):
    rng = random.Random(seed)
    base = [PALETTE[c] for c in LINE_COLORS]
    rng.shuffle(base)
    svg = frame_open()
    for i, r in enumerate(circles):
        c = base[i % len(base)]
        svg.append(f'<circle cx="120" cy="120" r="{r * 108:.1f}" fill="none" '
                   f'stroke="{c}" stroke-width="1.8"/>')
    for i, ang in enumerate(spokes):
        c = base[(i + len(circles)) % len(base)]
        x2 = 120 + 108 * math.cos(ang)
        y2 = 120 + 108 * math.sin(ang)
        svg.append(f'<line x1="120" y1="120" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>')
    svg.append(f'<circle cx="120" cy="120" r="2.6" fill="{PALETTE["cyan"]}"/>')
    caption(svg, caption_text)
    return "\n".join(svg) + "\n"
def ollama_json(prompt, no_ollama=False):
    """Ask the local model for ONE small JSON object; None on any failure (soft lane)."""
    if no_ollama:
        return None
    for model in (MODEL, MODEL_FALLBACK):
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0.7, "num_predict": 220}}).encode()
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                text = json.loads(r.read())["response"]
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    data["_model"] = model
                    return data
        except Exception as e:
            log(f"ollama note failed ({model}): {e}")
    return None


def fallback_name(spec):
    fam = spec["family"]
    if spec["geometry"] == "square":
        mtok = "+".join(f"{m['n']}{m['m']}" for m in spec["modes"])
        return f"Square {mtok} - {fam}"
    mtok = "+".join(f"{m['n']}.{m['p']}" for m in spec["modes"])
    return f"Ring {mtok} - {fam}"


def build_sheet(spec, no_ollama=False):
    scored = score_candidate(spec)
    if scored is None:
        return None, None
    cap = f"{spec['family'].replace('_', '+')} · {fallback_name(spec)}"
    if spec["geometry"] == "square":
        svg = svg_square(marching_squares(square_field(spec)), cap)
    else:
        circles, spokes = circular_analytic(spec)
        svg = svg_circular(circles, spokes, cap, spec["seed"])
    svg = svg.replace("·", "&#183;")
    ask = ollama_json(
        f"You name Chladni nodal-pattern drafts for a cozy rhythm JRPG proof board. "
        f"Pattern: {cap}. Palette: blush/pearl/lilac/cream. "
        f'Output ONLY JSON: {{"display_name": "<=5 words", '
        f'"production_note": "<=18 words, how a textile artist could use it"}}. '
        f"No markdown.", no_ollama=no_ollama)
    sheet = {
        "schema": SCHEMA,
        "id": spec["id"],
        "family": spec["family"],
        "notes": spec["notes"],
        "geometry": spec["geometry"],
        "modes": spec["modes"],
        "seed": spec["seed"],
        "rank": scored["rank"],
        "nodal_length": scored["nodal_length"],
        "scores": scored["scores"],
        "rank_weights": dict(WEIGHTS),
        "display_name": ask.get("display_name", fallback_name(spec))
        if ask else fallback_name(spec),
        "production_note": ask.get("production_note", "draft preview; owner picks for texture authoring")
        if ask else "draft preview; owner picks for texture authoring",
        "name_model": ask.get("_model", "deterministic-fallback") if ask else "deterministic-fallback",
        "palette": dict(PALETTE),
        "palette_provenance": PALETTE_PROVENANCE,
        "status": "draft",
    }
    return sheet, svg


def write_sheet(sheet, svg):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{sheet['id']}.json").write_text(json.dumps(sheet, indent=2), encoding="utf-8")
    (OUT / f"{sheet['id']}.svg").write_text(svg, encoding="utf-8")


def existing_ids():
    if not OUT.exists():
        return set()
    return {p.stem for p in OUT.glob("*.json")}


def mint_once(rng, no_ollama=False, cap=CAP):
    ids = existing_ids()
    if len(ids) >= cap:
        return None
    for _ in range(40):
        spec = sample_candidate(rng)
        if spec["id"] in ids:
            continue
        sheet, svg = build_sheet(spec, no_ollama=no_ollama)
        if sheet is None:
            continue
        return sheet, svg
    return None
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Chladni pattern foundry daemon (draft sheets)")
    p.add_argument("--once", type=int, default=0, help="mint N sheets then exit")
    p.add_argument("--cap", type=int, default=CAP)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--no-ollama", action="store_true", help="offline: skip model naming lane")
    return p.parse_args(argv)


def run_loop(args, rng, stops=None):
    stops = stops or STOPS
    made = 0
    while not stopped(stops) and (args.once and made < args.once or not args.once):
        if len(existing_ids()) >= args.cap:
            log(f"cap reached ({args.cap}); exit")
            break
        got = mint_once(rng, no_ollama=args.no_ollama, cap=args.cap)
        if got is None:
            log("no mintable candidate this pass; exit")
            break
        sheet, svg = got
        write_sheet(sheet, svg)
        made += 1
        log(f"written: {sheet['id']} rank={sheet['rank']} ({sheet['display_name']})")
        if not args.once:
            time.sleep(SLEEP_S)
    log("exit")
    return made


def main(argv=None):
    args = parse_args(argv)
    rng = random.Random(args.seed)
    log(f"start (cap {args.cap}, have {len(existing_ids())}, once={args.once}, "
        f"no_ollama={args.no_ollama})")
    return run_loop(args, rng)


if __name__ == "__main__":
    main()
