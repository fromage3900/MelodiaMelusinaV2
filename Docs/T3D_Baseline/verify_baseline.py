#!/usr/bin/env python3
"""Re-export the material spine from the live editor and diff it against the committed baseline.

Exit 0 = clean, exit 1 = drift or export failure. Intended as a gate, not a report.

    python Docs/T3D_Baseline/verify_baseline.py            # check only
    python Docs/T3D_Baseline/verify_baseline.py --update   # accept drift, rewrite baseline

Requires the UE editor running with Monolith on 127.0.0.1:9316.
"""
import argparse, difflib, hashlib, json, os, sys, urllib.request

MCP = 'http://127.0.0.1:9316/mcp'
BASE = os.path.dirname(os.path.abspath(__file__))
MATS = os.path.join(BASE, 'materials')
CATALOG = os.path.join(BASE, 'material_catalog.json')
MAX_BYTES = 4194304


def call(tool, args, timeout=180):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                       'params': {'name': tool, 'arguments': args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    c = r.get('result', {}).get('content', [])
    return c[0].get('text', '') if c else ''


def export(ue_path):
    """Return (payload_text, error). A success envelope with full_bytes != returned_bytes is an error:
    the 256 KiB default silently returns a plain-text notice that looks like a successful export."""
    raw = call('project_query', {'action': 'export_asset_text',
                                 'asset_path': ue_path, 'max_bytes': MAX_BYTES})
    try:
        env = json.loads(raw)
    except Exception:
        return None, raw.strip()[:200]
    if not env.get('success'):
        return None, str(env)[:200]
    if env.get('full_bytes') != env.get('returned_bytes'):
        return None, f"TRUNCATED {env.get('returned_bytes')}/{env.get('full_bytes')}"
    return env.get('text', ''), None


def canonical(text):
    """Order-insensitive form of a T3D payload, for comparison only.

    UE emits sibling objects in a non-deterministic order, so re-exporting an
    UNTOUCHED material yields different bytes and a different sha256. On
    2026-08-08 that produced four false DRIFT reports (MF_AnimeSkinWrap,
    MF_Gemstone, MF_IridescenceSheen, M_Master_Impressionist_Toon) whose line
    multisets were provably identical to the baseline -- nothing had changed.

    A gate that cries wolf gets ignored, which is worse than no gate (see
    MONOLITH_GUIDE Recipe 15 on flaky fingerprints). So: sort sibling objects
    and property lines at every level, then compare. Reordered siblings compare
    equal; any added, removed or altered line still differs.

    The sort is RECURSIVE. The payload is usually a single outer object whose
    CHILDREN are what get reordered, so sorting only the top level does nothing
    -- that was the first attempt at this fix and it caught none of the four.

    This is a comparison aid only -- the stored .t3d files and their sha256 are
    untouched, so the committed baseline remains a byte-exact record.
    """
    lines = [l.strip() for l in text.replace('\r\n', '\n').split('\n')]
    pos = 0

    def parse_block():
        """Consume one Begin..End Object at lines[pos]; return its canonical text."""
        nonlocal pos
        header = lines[pos]
        pos += 1
        scalars, children = [], []
        while pos < len(lines):
            s = lines[pos]
            if s.startswith('Begin Object'):
                children.append(parse_block())
            elif s.startswith('End Object'):
                pos += 1
                return '\n'.join([header] + sorted(scalars) + sorted(children) + ['End Object'])
            else:
                if s:
                    scalars.append(s)
                pos += 1
        raise ValueError('unterminated Begin Object')

    try:
        top, scalars = [], []
        while pos < len(lines):
            s = lines[pos]
            if s.startswith('Begin Object'):
                top.append(parse_block())
            else:
                if s:
                    scalars.append(s)
                pos += 1
    except (ValueError, IndexError):
        return None                  # unbalanced payload: do not pretend to canonicalise
    return '\n'.join(sorted(scalars) + sorted(top))


def reordered_only(baseline_text, live_text):
    """True when the two payloads differ only in sibling-object order."""
    a, b = canonical(baseline_text), canonical(live_text)
    return a is not None and b is not None and a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--update', action='store_true', help='accept drift and rewrite the baseline')
    ap.add_argument('--diff', action='store_true', help='print a unified diff for each drifted asset')
    args = ap.parse_args()

    cat = json.load(open(CATALOG))
    assets = [a for f in cat['families'].values() for a in f['assets']]
    drift, failed, clean, reordered = [], [], 0, []

    for a in sorted(assets, key=lambda a: a['name']):
        payload, err = export(a['ue_path'])
        if err:
            failed.append((a['name'], err))
            print(f"FAIL   {a['name']:44} {err}")
            continue
        sha = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        if sha == a['sha256']:
            clean += 1
            continue
        # Byte mismatch is not proof of change: check whether it is only the
        # exporter's sibling ordering before reporting drift.
        try:
            baseline_text = open(os.path.join(BASE, a['file']), encoding='utf-8').read()
        except OSError as e:
            failed.append((a['name'], f'baseline unreadable: {e}'))
            print(f"FAIL   {a['name']:44} baseline unreadable: {e}")
            continue
        if reordered_only(baseline_text, payload):
            clean += 1
            reordered.append(a['name'])
            continue
        nodes = payload.count('Begin Object Class=')
        drift.append((a, payload, sha, nodes))
        print(f"DRIFT  {a['name']:44} {a['payload_bytes']:>9,} -> {len(payload.encode()):>9,} B  "
              f"{a['nodes']:>5} -> {nodes:>5} nodes")
        if args.diff:
            old = open(os.path.join(BASE, a['file']), encoding='utf-8').read().splitlines()
            for line in list(difflib.unified_diff(old, payload.splitlines(),
                                                  'baseline', 'live', n=1, lineterm=''))[:60]:
                print('   ' + line)

    if reordered:
        print(f"\n{len(reordered)} asset(s) differed only in exporter object order "
              f"(counted clean, baseline left alone):")
        for name in reordered:
            print(f"   REORDERED  {name}")

    print(f"\n=== {clean} clean | {len(drift)} drifted | {len(failed)} failed "
          f"| {len(assets)} total ===")

    if args.update and drift:
        for a, payload, sha, nodes in drift:
            with open(os.path.join(BASE, a['file']), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(payload)
            a.update(sha256=sha, nodes=nodes, payload_bytes=len(payload.encode()),
                     lines=payload.count('\n') + 1)
        for f in cat['families'].values():
            f['payload_bytes'] = sum(x['payload_bytes'] for x in f['assets'])
            f['nodes'] = sum(x['nodes'] for x in f['assets'])
        cat['total_payload_bytes'] = sum(f['payload_bytes'] for f in cat['families'].values())
        cat['total_nodes'] = sum(f['nodes'] for f in cat['families'].values())
        json.dump(cat, open(CATALOG, 'w'), indent=2)
        print(f"baseline updated: {len(drift)} assets")
        return 0

    return 1 if (drift or failed) else 0


if __name__ == '__main__':
    sys.exit(main())
