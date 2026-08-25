#!/usr/bin/env python3
"""
ui_style_audit.py - inventory every authored widget style, then propose tokens.

WHY THIS SPEEDS UP VISUAL POLISH

The slow part of a polish pass is not applying styles, it is discovering what
you currently have. 31 widget Blueprints authored over months carry an unknown
number of font sizes, greys and paddings, most of them accidental near-misses
rather than decisions. A designer -- human or agent -- cannot produce a
consistent spec without that inventory, so the first day of any polish pass is
spent rebuilding it by hand, in the editor, one widget at a time.

This does that pass in one command: walk every WBP, read the visual properties
off every widget, cluster the values, and report where the near-misses are.
Then it proposes a token set: the smallest palette that covers what is already
there, with each raw value mapped to its nearest token.

Output is a text dashboard plus --json for an agent to act on. It CHANGES
NOTHING -- Monolith's ui_query.batch_style / set_font / set_brush are the
apply side, and applying is a separate, reviewable decision.

    python Tools/ui_style_audit.py                     # audit everything
    python Tools/ui_style_audit.py --filter Rhythm     # only matching WBPs
    python Tools/ui_style_audit.py --json Saved/Dashboards/ui_tokens.json
    python Tools/ui_style_audit.py --out Saved/Dashboards/ui_style.txt

Requires the editor with Monolith on 9316. Read-only.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mcp_client import monolith  # noqa: E402

WIDTH = 78

# Widget classes worth auditing, and which properties carry their visual identity.
VISUAL_PROPS = {
    "TextBlock":     ["Font", "ColorAndOpacity", "ShadowOffset", "ShadowColorAndOpacity",
                      "Justification"],
    "RichTextBlock": ["ColorAndOpacity"],
    "Button":        ["ColorAndOpacity", "BackgroundColor"],
    "Border":        ["Background", "BrushColor", "Padding"],
    "Image":         ["Brush", "ColorAndOpacity"],
    "ProgressBar":   ["FillColorAndOpacity", "Percent"],
}


def rule(ch="-"):
    return ch * WIDTH


def header(title, sub=""):
    out = ["", "=" * WIDTH, f" {title}"]
    if sub:
        out.append(f" {sub}")
    out.append("=" * WIDTH)
    return out


def call(action, params):
    raw = monolith("ui_query", {"action": action, "params": params})
    if isinstance(raw, str) and raw.startswith("ERROR"):
        raise RuntimeError(raw[:160])
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        raise RuntimeError(f"unparseable {action}: {str(raw)[:160]}")


def list_widget_blueprints(pattern=None):
    """Every WBP under /Game, via the asset registry."""
    code = (
        "import json, unreal\n"
        "ar = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        "f = unreal.ARFilter(package_paths=['/Game'], recursive_paths=True,\n"
        "                    class_names=['WidgetBlueprint'])\n"
        "out = [str(a.package_name) for a in ar.get_assets(f)]\n"
        'print("__UI__" + json.dumps(sorted(out)))\n'
    )
    raw = monolith("editor_query", {"action": "run_python", "params": {"command": code}})
    payload = json.loads(raw) if isinstance(raw, str) else raw
    for item in payload.get("output", []):
        for line in str(item.get("output", "")).splitlines():
            if line.startswith("__UI__"):
                paths = json.loads(line[len("__UI__"):])
                paths = [p for p in paths if "/_ThirdParty/" not in p]
                if pattern:
                    rx = re.compile(pattern, re.I)
                    paths = [p for p in paths if rx.search(p)]
                return paths
    raise RuntimeError("could not enumerate widget blueprints")


def walk_tree(node, out, depth=0):
    """Flatten a widget tree into (name, class) pairs."""
    if not isinstance(node, dict):
        return
    name, cls = node.get("name"), node.get("class")
    if name and cls:
        out.append((name, cls))
    for child in node.get("children", []) or []:
        walk_tree(child, out, depth + 1)


# ------------------------------------------------------------------ parsing

FONT_RX = re.compile(r"TypefaceFontName=\"([^\"]+)\".*?Size=([\d.]+)", re.S)
FONT_RX2 = re.compile(r"Size=([\d.]+).*?TypefaceFontName=\"([^\"]+)\"", re.S)
RGBA_RX = re.compile(r"R=([\d.\-]+),G=([\d.\-]+),B=([\d.\-]+),A=([\d.\-]+)")


def parse_font(value):
    m = FONT_RX.search(value or "")
    if m:
        return m.group(1), float(m.group(2))
    m = FONT_RX2.search(value or "")
    if m:
        return m.group(2), float(m.group(1))
    return None


def parse_color(value):
    m = RGBA_RX.search(value or "")
    if not m:
        return None
    return tuple(round(float(g), 4) for g in m.groups())


def to_hex(rgba):
    """Hex for display. Channels above 1.0 are HDR and would silently clamp.

    UE stores emissive/glow UI colours above 1.0. Clamping them to hex makes two
    genuinely different colours print identically -- (0,1,1) and (0,2.5,2.5) both
    read as #00FFFF -- which looks like a clustering bug and is actually a
    display one. The gain suffix keeps them distinguishable.
    """
    r, g, b, a = rgba
    peak = max(r, g, b)
    if peak > 1.0001:
        # Do not clamp HDR into hex: (0,255,250) and (0,255,255) both become
        # #00FFFF, so distinct colours print identically. Show the channels.
        s = f"hdr({r:.3g},{g:.3g},{b:.3g})"
    else:
        def c(x):
            return max(0, min(255, int(round(x * 255))))
        s = f"#{c(r):02X}{c(g):02X}{c(b):02X}"
    if abs(a - 1.0) > 1e-6:
        s += f" a={a:.2f}"
    return s


def color_distance(a, b):
    """Crude perceptual-ish distance on RGB, ignoring alpha."""
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])) ** 0.5


# ------------------------------------------------------------------ audit

def audit(paths, verbose=False):
    fonts = Counter()          # (typeface, size) -> count
    colors = Counter()         # rgba -> count
    paddings = Counter()
    per_widget = defaultdict(list)
    failures = []
    scanned = 0

    for wbp in paths:
        try:
            tree = call("get_widget_tree", {"asset_path": wbp})
        except RuntimeError as e:
            failures.append((wbp, str(e)))
            continue
        flat = []
        walk_tree(tree.get("root") or {}, flat)
        for name, cls in flat:
            if cls not in VISUAL_PROPS:
                continue
            try:
                props = call("list_widget_properties",
                             {"asset_path": wbp, "widget_name": name})
            except RuntimeError as e:
                failures.append((f"{wbp}:{name}", str(e)))
                continue
            scanned += 1
            byname = {p["property_name"]: p.get("current_value", "")
                      for p in props.get("properties", [])}
            for prop in VISUAL_PROPS[cls]:
                val = byname.get(prop)
                if not val:
                    continue
                if prop == "Font":
                    f = parse_font(val)
                    if f:
                        fonts[f] += 1
                        per_widget[wbp].append((name, cls, "Font", f"{f[0]} {f[1]:g}"))
                elif "Color" in prop or prop in ("Background", "Brush"):
                    c = parse_color(val)
                    if c:
                        colors[c] += 1
                        per_widget[wbp].append((name, cls, prop, to_hex(c)))
                elif prop == "Padding":
                    paddings[val.strip()] += 1
    return {
        "fonts": fonts, "colors": colors, "paddings": paddings,
        "per_widget": per_widget, "failures": failures,
        "scanned": scanned, "wbp_count": len(paths),
    }


def cluster_colors(colors, threshold=0.06):
    """Group near-identical colors into tokens.

    Alpha is deliberately NOT part of clustering: #FFFFFF at a=1.0 and a=0.5 are
    the same colour used at two opacities, not two colours. Clustering on RGBA
    while measuring distance on RGB produced duplicate same-hex clusters, so
    collapse to RGB first and carry the alphas as a property of the token.
    """
    rgb_counts = Counter()
    alphas = defaultdict(Counter)
    for (r, g, b, a), n in colors.items():
        rgb_counts[(r, g, b)] += n
        alphas[(r, g, b)][a] += n

    clusters = []
    for rgb, n in sorted(rgb_counts.items(), key=lambda kv: -kv[1]):
        placed = False
        for cl in clusters:
            if color_distance(rgb, cl["token"]) <= threshold:
                cl["members"].append((rgb, n))
                cl["total"] += n
                cl["alphas"].update(alphas[rgb])
                placed = True
                break
        if not placed:
            clusters.append({"token": rgb, "members": [(rgb, n)], "total": n,
                             "alphas": Counter(alphas[rgb])})
    return clusters


# ------------------------------------------------------------------ render

def render(data, threshold):
    fonts, colors = data["fonts"], data["colors"]
    lines = header("UI STYLE AUDIT",
                   f"{data['wbp_count']} widget blueprints, {data['scanned']} styled widgets")

    lines += ["", f"  distinct font (face,size) pairs   {len(fonts)}",
              f"  distinct colors                   {len(colors)}",
              f"  distinct paddings                 {len(data['paddings'])}"]
    if data["failures"]:
        lines.append(f"  unreadable                        {len(data['failures'])}")

    lines += header("FONTS", "every authored face/size, most used first")
    if fonts:
        peak = max(fonts.values())
        for (face, size), n in fonts.most_common():
            bar = "#" * int(round(n / peak * 24))
            lines.append(f"  {face[:18]:<20}{size:>6g}pt {n:>4}  {bar}")
        sizes = sorted({s for _f, s in fonts})
        lines += ["", f"  {len(sizes)} distinct sizes: {', '.join(f'{s:g}' for s in sizes)}"]
        if len(sizes) > 6:
            lines.append("  More than six sizes is usually drift, not a type scale.")
    else:
        lines.append("  none found")

    lines += header("COLOR CLUSTERS", f"grouped at distance <= {threshold}")
    clusters = cluster_colors(colors, threshold)
    for cl in sorted(clusters, key=lambda c: -c["total"]):
        tok = to_hex(cl["token"] + (1.0,))
        alist = ", ".join(f"{a:g}" for a, _ in sorted(cl["alphas"].items(), reverse=True))
        lines.append(f"  {tok:<12}used {cl['total']:>4}x   "
                     f"{len(cl['members'])} shade(s), alpha: {alist[:34]}")
        if len(cl["members"]) > 1:
            for rgb, n in sorted(cl["members"], key=lambda m: -m[1])[1:]:
                lines.append(f"      near-miss {to_hex(rgb + (1.0,)):<12} x{n:<4} "
                             f"d={color_distance(rgb, cl['token']):.3f}")
    near = sum(1 for c in clusters if len(c["members"]) > 1)
    lines += ["", f"  {len(colors)} raw colors collapse to {len(clusters)} tokens; "
                  f"{near} cluster(s) contain near-misses."]
    if near:
        lines.append("  Near-misses are the cheapest polish win: they read as sloppiness")
        lines.append("  but cost one batch_style call each to unify.")

    lines += header("PROPOSED TOKENS", "smallest palette covering what is already authored")
    for i, cl in enumerate(sorted(clusters, key=lambda c: -c["total"]), 1):
        lines.append(f"  --color-{i:<2}  {to_hex(cl['token'] + (1.0,)):<12} {cl['total']:>4} uses")
    for i, ((face, size), n) in enumerate(fonts.most_common(), 1):
        lines.append(f"  --font-{i:<3} {face} {size:g}pt{'':<6} {n:>3} uses")

    if data["failures"]:
        lines += header("UNREADABLE")
        for what, why in data["failures"][:12]:
            lines.append(f"  {what[:44]:<46}{why[:28]}")
    return lines


def main():
    ap = argparse.ArgumentParser(description="Inventory authored widget styles and propose tokens.")
    ap.add_argument("--filter", help="regex; only audit matching widget blueprint paths")
    ap.add_argument("--threshold", type=float, default=0.06,
                    help="color clustering distance (default 0.06)")
    ap.add_argument("--json", help="write machine-readable audit here")
    ap.add_argument("--out", help="write the text dashboard here")
    args = ap.parse_args()

    try:
        paths = list_widget_blueprints(args.filter)
    except Exception as e:
        print(f"ERROR {e}")
        print("If the editor is running but silent, grep the log for MODAL_OPEN --")
        print("a modal dialog blocks the game thread and Monolith answers there.")
        return 3
    if not paths:
        print("no widget blueprints matched")
        return 1

    print(f"auditing {len(paths)} widget blueprint(s)...", file=sys.stderr)
    data = audit(paths)
    text = "\n".join(render(data, args.threshold)) + "\n"
    print(text)

    if args.out:
        p = args.out if os.path.isabs(args.out) else os.path.join(PROJECT, args.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="\n").write(text)
        print(f"written: {p}")

    if args.json:
        p = args.json if os.path.isabs(args.json) else os.path.join(PROJECT, args.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        payload = {
            "widget_blueprints": paths,
            "fonts": [{"face": f, "size": s, "count": n} for (f, s), n in data["fonts"].items()],
            "colors": [{"rgba": list(c), "hex": to_hex(c), "count": n}
                       for c, n in data["colors"].items()],
            "clusters": [{"token": to_hex(c["token"] + (1.0,)), "total": c["total"],
                          "alphas": sorted(c["alphas"]),
                          "shades": [to_hex(m + (1.0,)) for m, _ in c["members"]]}
                         for c in cluster_colors(data["colors"], args.threshold)],
            "per_widget": {k: v for k, v in data["per_widget"].items()},
        }
        json.dump(payload, open(p, "w", encoding="utf-8"), indent=2)
        print(f"written: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
