"""Negative test for the cycle guard added 2026-09-30.

A committed guard nobody has seen fail is not evidence. This injects the two
real cycle shapes and asserts they are caught:

  1. a SELF-LINK  - link_sockets must REFUSE it (and record it), because
     that is the exact shape that killed GN_BRUTALIST_CityBlock
  2. an A -> B -> A cycle built by hand behind link_sockets' back -
     find_link_cycles must still report it

Then asserts a clean tree reports no cycles, so the guard cannot pass by
always returning [].
"""
import sys

sys.path.insert(0, r"P:\MelodiaMelusinaV2-Laptop\deploy")

import bpy  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402

fails = []


def check(label, cond, detail=""):
    print("  [%s] %s %s" % ("PASS" if cond else "FAIL", label, detail))
    if not cond:
        fails.append(label)


print("=" * 70)
print("0. what does a socket expose for its owning node?")
core.reset_link_failures()
t = core.new_geometry_tree("GN_GUARD_PROBE")[0]
a = core.safe_node(t, 'ShaderNodeMath', (0, 0))
s_out = a.outputs[0]
s_in = a.inputs[0]
print("   socket type      : %s" % type(s_out).__name__)
print("   hasattr .node    : %s" % hasattr(s_out, "node"))
print("   .node value      : %r" % (getattr(s_out, "node", "<<absent>>"),))
print("   hasattr .id_data : %s" % hasattr(s_out, "id_data"))
print("   .id_data value   : %r" % (getattr(s_out, "id_data", "<<absent>>"),))
print("   out.node is in.node : %s"
      % (getattr(s_out, "node", None) is getattr(s_in, "node", None)))
print("   links BEFORE      : %d" % len(t.links))

print("=" * 70)
print("1. self-link is refused by link_sockets")
core.reset_link_failures()
t = core.new_geometry_tree("GN_GUARD_SELFLINK")[0]
a = core.safe_node(t, 'ShaderNodeMath', (0, 0))
before = len(t.links)
core.link_sockets(t, a.outputs[0], a.inputs[0])
recorded = core.link_failures().get(t.name) or []
after = len(t.links)
check("self-link recorded as a link failure", bool(recorded),
      "-> %s" % (recorded[0][:70] if recorded else "NOT RECORDED"))
check("no NEW link created", after == before,
      "-> links %d -> %d" % (before, after))

print("=" * 70)
print("2. two-node cycle A -> B -> A is reported")
core.reset_link_failures()
t2 = core.new_geometry_tree("GN_GUARD_CYCLE")[0]
n1 = core.safe_node(t2, 'ShaderNodeMath', (0, 0))
n2_ = core.safe_node(t2, 'ShaderNodeMath', (200, 0))
t2.links.new(n1.outputs[0], n2_.inputs[0])      # bypasses link_sockets
t2.links.new(n2_.outputs[0], n1.inputs[0])      # ... so the guard must catch
cyc = core.find_link_cycles(t2)
check("cycle detected", bool(cyc), "-> %s" % (cyc or "NONE"))
check("cycle names both nodes", bool(cyc) and n1.name in cyc[0]
      and n2_.name in cyc[0], "-> %s" % (cyc[0] if cyc else "-"))

print("=" * 70)
print("3. a clean tree reports NO cycles (guard is not always-true)")
core.reset_link_failures()
t3 = core.new_geometry_tree("GN_GUARD_CLEAN")[0]
c1 = core.safe_node(t3, 'ShaderNodeMath', (0, 0))
c2 = core.safe_node(t3, 'ShaderNodeMath', (200, 0))
core.link_sockets(t3, c1.outputs[0], c2.inputs[0])
core.link_sockets(t3, c2.outputs[0], c1.inputs[0])   # legal 2-cycle? no - DAG
clean = core.find_link_cycles(t3)
# c1 -> c2 and c2 -> c1 IS a cycle; use a true DAG instead
t4 = core.new_geometry_tree("GN_GUARD_DAG")[0]
d1 = core.safe_node(t4, 'ShaderNodeMath', (0, 0))
d2 = core.safe_node(t4, 'ShaderNodeMath', (200, 0))
d3 = core.safe_node(t4, 'ShaderNodeMath', (400, 0))
core.link_sockets(t4, d1.outputs[0], d2.inputs[0])
core.link_sockets(t4, d2.outputs[0], d3.inputs[0])
dag = core.find_link_cycles(t4)
check("acyclic graph reports no cycles", dag == [], "-> %s" % (dag or "[]"))

print("=" * 70)
print("GUARD TEST %s (%d failure(s))"
      % ("PASS" if not fails else "FAIL", len(fails)))
if fails:
    sys.exit(1)
