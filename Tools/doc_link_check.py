import os, re
from collections import Counter

SKIP = {'.git', 'node_modules', 'Content', 'Intermediate', 'Saved',
        'DerivedDataCache', 'Binaries', '.claude', 'Plugins', 'my-site-clean'}
bad, tot = [], 0

for dp, dn, fn in os.walk('.'):
    dn[:] = [d for d in dn if d not in SKIP and not d.startswith('_Quarantine')]
    for f in fn:
        if not f.endswith('.md'):
            continue
        p = os.path.join(dp, f)
        try:
            t = open(p, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for m in re.finditer(r'\[([^\]]{1,80})\]\(([^)]+)\)', t):
            tgt = m.group(2).split('#')[0].strip()
            if not tgt or tgt.startswith(('http', 'mailto:', '<')):
                continue
            tot += 1
            if not os.path.exists(os.path.normpath(os.path.join(dp, tgt))):
                bad.append((p.replace(os.sep, '/'), m.group(1)[:36], tgt))

print('checked %d local links, %d BROKEN\n' % (tot, len(bad)))
for f, n in Counter(b[0] for b in bad).most_common(15):
    print('%3d  %s' % (n, f))
print()
for b in bad[:25]:
    print('  %s\n       [%s] -> %s' % (b[0], b[1], b[2]))
