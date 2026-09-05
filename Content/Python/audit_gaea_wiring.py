"""Audit the Gaea mask wiring on M_Master_Nikki_Landscape, end to end.

Answers one question: for each Gaea lane, does the mask parameter reach the
material output, and which LandscapeLayerSample does it gate?

Run OUTSIDE the editor against exports produced by monolith:
    material_query export_material_graph      -> nodes + props
    material_query get_full_connection_graph  -> connections + material_outputs
"""
import json
import sys
from collections import defaultdict, deque


def load(conn_path, expr_path):
    conn = json.load(open(conn_path))
    exp = json.load(open(expr_path))
    return conn, {n["id"]: n for n in exp["nodes"]}


def audit(conn_path, expr_path):
    conn, nodes = load(conn_path, expr_path)
    edges = conn["connections"]
    outputs = conn["material_outputs"]

    def pname(i):
        return nodes.get(i, {}).get("props", {}).get("ParameterName", "")

    def label(i):
        n = nodes.get(i, {})
        p = pname(i)
        return "%s%s" % (n.get("class", "?"), "[" + p + "]" if p else "")

    inc, out = defaultdict(list), defaultdict(list)
    for e in edges:
        inc[e["to"]].append((e["from"], e.get("to_input")))
        out[e["from"]].append((e["to"], e.get("to_input")))

    roots = [o["expression"] for o in outputs]
    seen, q = set(roots), deque(roots)
    while q:
        n = q.popleft()
        for s, _ in inc.get(n, []):
            if s not in seen:
                seen.add(s)
                q.append(s)

    # every LandscapeLayerSample and what multiplies it
    print("=== Gaea lanes: mask -> layer ===")
    lanes = []
    for nid, n in nodes.items():
        if n.get("class") != "Multiply":
            continue
        srcs = [s for s, _ in inc.get(nid, [])]
        layer = next((s for s in srcs
                      if nodes.get(s, {}).get("class") == "LandscapeLayerSample"), None)
        if not layer:
            continue
        other = [s for s in srcs if s != layer]
        # walk back from the non-layer input to find the Gaea mask/weight
        found = []
        stack, local = list(other), set()
        while stack:
            c = stack.pop()
            if c in local:
                continue
            local.add(c)
            p = pname(c)
            if p.startswith("Gaea_"):
                found.append(p)
            for s, _ in inc.get(c, []):
                stack.append(s)
        lanes.append((pname(layer), sorted(set(found)), nid, nid in seen))

    for lyr, masks, nid, reach in sorted(lanes):
        status = "reaches output" if reach else "DEAD - never reaches output"
        print("  layer %-8s <- %-42s [%s]" %
              (lyr, ", ".join(masks) if masks else "(no Gaea param)", status))

    print()
    print("=== every Gaea parameter: consumers + reachability ===")
    gaea = {i: pname(i) for i in nodes if pname(i).startswith("Gaea_")
            or pname(i).startswith("bGaea") or pname(i) == "bUseGaeaMasks"}
    for i, p in sorted(gaea.items(), key=lambda kv: kv[1]):
        cons = out.get(i, [])
        r = "reaches output" if i in seen else "DEAD"
        if not cons:
            drives = "-> nothing (orphan)"
        else:
            drives = "-> " + ", ".join("%s[%s]" % (label(t), inp) for t, inp in cons[:3])
        print("  %-26s %-14s %s" % (p, r, drives))


if __name__ == "__main__":
    audit(sys.argv[1], sys.argv[2])
