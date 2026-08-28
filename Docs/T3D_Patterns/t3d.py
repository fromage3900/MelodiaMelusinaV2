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
from pathlib import Path

MCP = 'http://127.0.0.1:9316/mcp'
PATTERNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patterns')
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = PROJECT_ROOT / 'Tools'
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from t3d_safe_wire import safe_wire  # noqa: E402


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


def wardrobe_common_args(parser):
    parser.add_argument('--asset', required=True)
    parser.add_argument('--pattern', required=True)
    parser.add_argument('--graph', default='EventGraph')
    parser.add_argument('--set', action='append', metavar='K=V')


def sea_above_wire(args, *, allow_mutation: bool) -> int:
    text = load(args.pattern)
    supplied = kv(args.set)
    missing = [token for token in tokens(text) if token not in supplied]
    if missing:
        print(f"missing --set for: {', '.join(missing)}")
        return 2
    if args.go and not args.expected_fingerprint:
        print('REFUSED: --go requires --expected-fingerprint')
        return 2
    ok, manifest, evidence_dir = safe_wire(
        args.asset,
        args.graph,
        {'t3d': text, 'placeholders': supplied, 'compile': True},
        args.expected_fingerprint,
        dry_run=not (args.go and allow_mutation),
    )
    print(json.dumps({'ok': ok, 'outcome': manifest.get('outcome'), 'evidence': str(evidence_dir)}, indent=2))
    return 0 if ok else 1


def wardrobe_wire(args, *, allow_mutation: bool, require_battle_enable: bool = False) -> int:
    if require_battle_enable and not args.enable_battle:
        print('REFUSED: battle wardrobe gate is disabled; pass --enable-battle for an explicit owner-approved dry run.')
        return 2
    text = load(args.pattern)
    supplied = kv(args.set)
    missing = [token for token in tokens(text) if token not in supplied]
    if missing:
        print(f"missing --set for: {', '.join(missing)}")
        return 2
    if args.go and not args.expected_fingerprint:
        print('REFUSED: --go requires --expected-fingerprint')
        return 2
    ok, manifest, evidence_dir = safe_wire(
        args.asset,
        args.graph,
        {'t3d': text, 'placeholders': supplied, 'compile': True},
        args.expected_fingerprint,
        dry_run=not (args.go and allow_mutation),
    )
    print(json.dumps({'ok': ok, 'outcome': manifest.get('outcome'), 'evidence': str(evidence_dir)}, indent=2))
    return 0 if ok else 1


def validate_wardrobe_catalog(args) -> int:
    contract_path = Path(args.catalog).resolve()
    drafts_path = Path(args.drafts).resolve()
    try:
        contract = json.loads(contract_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({'ok': False, 'error': f'catalog_contract: {exc}'}, indent=2))
        return 1
    drafts = sorted(drafts_path.glob('*.json')) if drafts_path.is_dir() else []
    ids = []
    errors = []
    for draft in drafts:
        try:
            data = json.loads(draft.read_text(encoding='utf-8'))
            cosmetic_id = str(data.get('CosmeticId', '')).strip()
            if not cosmetic_id:
                errors.append(f'{draft.name}: missing CosmeticId')
            ids.append(cosmetic_id)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f'{draft.name}: {exc}')
    duplicates = sorted({item for item in ids if item and ids.count(item) > 1})
    if duplicates:
        errors.append(f'duplicate CosmeticId values: {duplicates}')
    expected_gacha = int(contract.get('gacha_count', 38))
    if len(drafts) != expected_gacha:
        errors.append(f'draft_count {len(drafts)} != expected_gacha_count {expected_gacha}')
    payload = {
        'ok': not errors,
        'contract': str(contract_path),
        'drafts': str(drafts_path),
        'draft_count': len(drafts),
        'expected_total': contract.get('target_count'),
        'demo_count': contract.get('demo_count'),
        'gacha_count': expected_gacha,
        'first_outfit_gate': contract.get('first_outfit_gate'),
        'battle_gate': contract.get('battle_gate'),
        'errors': errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


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

    # Wardrobe workflows use the composite safe-wire transaction rather than
    # the legacy direct injector. They are intentionally named so external
    # LiveLink/OSC adapters can target a stable command surface.
    s = sub.add_parser('validate_wardrobe_nodes')
    wardrobe_common_args(s)
    s = sub.add_parser('inject_wardrobe_node')
    wardrobe_common_args(s)
    s.add_argument('--expected-fingerprint')
    s.add_argument('--go', action='store_true')
    s = sub.add_parser('wire_wardrobe_battle_gate')
    wardrobe_common_args(s)
    s.add_argument('--expected-fingerprint')
    s.add_argument('--enable-battle', action='store_true')
    s.add_argument('--go', action='store_true')
    s = sub.add_parser('validate_wardrobe_catalog')
    s.add_argument('--catalog', default=str(PROJECT_ROOT / 'specs' / 'wardrobe' / 'wardrobe_catalog_manifest.v1.json'))
    s.add_argument('--drafts', default=str(PROJECT_ROOT / 'Plugins' / 'MelodiaWardrobe' / 'Content' / 'MelodiaWardrobe' / 'Drafts'))
    s = sub.add_parser('validate_sea_above_nodes')
    wardrobe_common_args(s)
    s = sub.add_parser('inject_sea_above_node')
    wardrobe_common_args(s)
    s.add_argument('--expected-fingerprint')
    s.add_argument('--go', action='store_true')
    a = ap.parse_args()

    if a.cmd == 'list':
        for n in names():
            t = load(n)
            print(f"  {n:20} {t.count('Begin Object Class='):>2} nodes   params: {', '.join(tokens(t)) or '(none)'}")
        return 0

    if a.cmd == 'show':
        sys.stdout.write(load(a.pattern))
        return 0

    if a.cmd == 'validate_wardrobe_catalog':
        return validate_wardrobe_catalog(a)

    if a.cmd == 'validate_wardrobe_nodes':
        a.expected_fingerprint = None
        a.go = False
        a.enable_battle = True
        return wardrobe_wire(a, allow_mutation=False)

    if a.cmd == 'inject_wardrobe_node':
        a.enable_battle = True
        return wardrobe_wire(a, allow_mutation=True)

    if a.cmd == 'wire_wardrobe_battle_gate':
        return wardrobe_wire(a, allow_mutation=True, require_battle_enable=True)

    if a.cmd == 'validate_sea_above_nodes':
        a.expected_fingerprint = None
        a.go = False
        return sea_above_wire(a, allow_mutation=False)

    if a.cmd == 'inject_sea_above_node':
        return sea_above_wire(a, allow_mutation=True)

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
