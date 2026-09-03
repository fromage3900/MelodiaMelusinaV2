#!/usr/bin/env python3
import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "surreal_architecture_gen.py"
text = p.read_text(encoding="utf-8")
markers = ("ð", "â", "Ã", "Â", "Ï")
broken = []
for m in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text):
    s = m.group(1)
    if any(x in s for x in markers):
        broken.append(s)

print("broken count", len(broken))
for s in broken[:20]:
    fixed = None
    for enc in ("cp1252", "latin-1"):
        try:
            f = s.encode(enc).decode("utf-8")
            if f != s and "\ufffd" not in f:
                fixed = (enc, f)
                break
        except Exception:
            pass
    if fixed:
        print("OK", enc, repr(s[:40]), "->", repr(fixed[1][:40]))
    else:
        cps = [hex(ord(c)) for c in s[:8]]
        print("NOFIX", repr(s[:50]), cps)
