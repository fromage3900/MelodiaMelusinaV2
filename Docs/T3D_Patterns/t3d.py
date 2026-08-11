#!/usr/bin/env python3
"""Drive Monolith's T3D injection from the command line.

    python Docs/T3D_Patterns/t3d.py list
    python Docs/T3D_Patterns/t3d.py show subsystem_call
    python Docs/T3D_Patterns/t3d.py check  subsystem_call --asset /Game/... --set subsystem_class=/Script/...
    python Docs/T3D_Patterns/t3d.py inject subsystem_call --asset /Game/... --set ... [--go]

`check` never mutates. `inject` dry-runs unless you pass --go, and always prints the
before/after graph fingerprint so the edit is proven rather than assumed.

Requires the editor running with Monolith on 127.0.0.1:9316.
"""
import argparse, json, os, re, sys, urllib.request

MCP = 'http://127.0.0.1:9316/mcp'
PATTERNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patterns')


def call(tool, args, timeout=180):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                       'params': {'name': tool, 'arguments': args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    if 'error' in r:
        raise SystemExit(f"MCP error: {r['error'].get('message')}")
    c = r.get('result', {}).get('content', [])
    return c[0].get('text', '') if c else ''


def bq(action, **params):
    raw = call('blueprint_query', {'action': action, 'params': params})
    try:
        return json.loads(raw)
    except Exception:
        raise SystemExit(f"unparseable response: {raw[:400]}")


def load(name):
    p = os.path.join(PATTERNS, name if name.endswith('.t3d') else name + '.t3d')
    if not os.path.exists(p):
        raise SystemExit(f"no such pattern: {name}\nAvailable: {', '.join(names())}")
    return open(p, encoding='utf-8').read()


def names():
    return sorted(f[:-4] for f in os.listdir(PATTERNS) if f.endswith('.t3d'))


def tokens(text):
    """Free tokens the caller must supply — {{GUID:...}} are minted by the engine side."""
    return sorted(set(re.findall(r'\{\{(?!GUID:)([A-Za-z0-9_]+)\}\}', text)))


def kv(pairs):
    out = {}
    for p in pairs or []:
        if '=' not in p:
            raise SystemExit(f"--set expects key=value, got: {p}")
        k, v = p.split('=', 1)
        out[k] = v
    return out


def report(d):
    for f in d.get('findings', []):
        print(f"  [{f['severity']}/{f['kind']}] {f['detail']}" + (f"  (node {f['node']})" if f.get('node') else ''))
    print(f"  valid={d.get('valid')} engine_accepts={d.get('engine_accepts')} declared_nodes={d.get('declared_nodes')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list')
    s = sub.add_parser('show');  s.add_argument('pattern')
    for c in ('check', 'inject'):
        s = sub.add_parser(c)
        s.add_argument('pattern')
        s.add_argument('--asset', required=True)
        s.add_argument('--graph', default=None)
        s.add_argument('--set', action='append', metavar='K=V')
        if c == 'inject':
            s.add_argument('--go', action='store_true', help='actually mutate (default is dry run)')
    a = ap.parse_args()

    if a.cmd == 'list':
        for n in names():
            t = load(n)
            print(f"  {n:20} {t.count('Begin Object Class='):>2} nodes   params: {', '.join(tokens(t)) or '(none)'}")
        return 0

    if a.cmd == 'show':
        sys.stdout.write(load(a.pattern))
        return 0

    text = load(a.pattern)
    supplied = kv(a.set)
    missing = [t for t in tokens(text) if t not in supplied]
    if missing:
        raise SystemExit(f"missing --set for: {', '.join(missing)}")

    params = dict(asset_path=a.asset, t3d=text, placeholders=supplied)
    if a.graph:
        params['graph_name'] = a.graph

    if a.cmd == 'check':
        report(bq('validate_nodes_t3d', **params))
        return 0

    if not a.go:
        print("DRY RUN (pass --go to apply)")
        report(bq('inject_nodes_t3d', dry_run=True, **params))
        return 0

    fp = dict(asset_path=a.asset)
    if a.graph:
        fp['graph_name'] = a.graph
    before = bq('get_graph_fingerprint', **fp).get('fingerprint')
    d = bq('inject_nodes_t3d', **params)
    report(d)
    if not d.get('injected'):
        print(f"  NOT INJECTED: {d.get('reason')}")
        return 1
    for n in d.get('nodes', []):
        print(f"  + {n['id']:22} {n['class']:24} linked_pins={n['linked_pins']}")
    after = bq('get_graph_fingerprint', **fp).get('fingerprint')
    print(f"  compiled_clean={d.get('compiled_clean')} errors={d.get('compile_errors')}")
    print(f"  fingerprint {before} -> {after}  changed={before != after}")
    print("  NOT SAVED — save the asset when you are happy with it.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
