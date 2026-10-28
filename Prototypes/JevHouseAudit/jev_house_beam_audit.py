"""Jev plan-audit via beam (Nous Portal, response_format json_object).

One call: Choice (next block) + Choice (riskiest) + Noul (owner gate) +
Score (readiness), criteria text transmitted, authored-only enforcement,
distributions recorded. Sampling rule: one run now; repeat on near-tie.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', '..', 'Tools'))
from model_router import _nous_creds  # noqa: E402, process-env creds only

MODEL = 'reflection/beam-1.0-501b-a23b:free'

NEXT_BLOCK = {
    "ASSEMBLER_GREEN": "Finish house.py joint/stair/roof pass so the pure-python gate is green on SALON_FIRST (no editor needed).",
    "PACKAGER": "Build melodia::house::1.0 subnet with arch output, PCG scatter branch, and full artist parm folders/menus.",
    "UE_STAGE": "Import refreshed salon_bay, instantiate the STAGE actor, idle-editor cook plus readback and captures.",
    "COMMIT_DOCS": "Write receipts, update the stack pin and breakdown, force-add reviewed files, close out status.",
}
RISKIEST = {
    "JOINT_GEOMETRY": "Snapped-room joint trim orientation or winding renders wrong in UE.",
    "SOCKET_TRANSFORM": "Portal frame yaw/offset math misplaces linked rooms.",
    "UE_COOK_SCALE": "The full-house cook OOMs or signal-11s like the 2026-10-22 RoomShell cook.",
    "ROOF_PITCH": "The mansard or conical roof sweep self-intersects on some footprint.",
}

STATE = {
    "assembler_smoke": "green (joint mode resolved coincident portals; gate all_pass, 23117 prims, 0 unmapped)",
    "variants_refresh": "7/7 admit with zero unmapped roles (SalonLive receipt 2026-10-28)",
    "editor": "blocked after modal episode; staging script and surveyed spot ready",
    "packager": "pending (subnet design fixed: arch + PCG Partition/Scatter + artist folders)",
    "ue_stage": "blocked on editor idle",
}

PROMPT = """You are a production judgment service for a Houdini procedural-house build.
Current verified state:
%s

Answer exactly these four questions in ONE JSON object. For each choice give
"choice" (one of the listed keys), "confidence" (0-1), and "probabilities"
(a map of EVERY listed key to a probability summing to 1).

1. order (Choice): which single next block unblocks the working house system fastest?
%s
2. riskiest (Choice): which assumption is riskiest - most likely to invalidate the build if wrong?
%s
3. human (Noul 0-1): does an owner decision gate execution before agents run the next block?
4. readiness (Score 0-4: 0 blocked, 1 fragile, 2 partial, 3 ready, 4 proven): how execution-ready is this track?

Return ONLY JSON: {"order": {"choice": ..., "confidence": ..., "probabilities": {...}},
"riskiest": {...}, "human": <float>, "readiness": {"score": <int>, "probabilities": [...]}}.
""" % (json.dumps(STATE),
       json.dumps(NEXT_BLOCK), json.dumps(RISKIEST))


def call_beam():
    key, base = _nous_creds()
    payload = {"model": MODEL,
               "messages": [{"role": "user", "content": PROMPT}],
               "temperature": 0.2, "max_tokens": 6000,
               "response_format": {"type": "json_object"}}
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + key}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    return body['choices'][0]['message']['content']


def main():
    raw = call_beam()
    try:
        ans = json.loads(raw)
    except Exception:
        print('NON-JSON-RESPONSE:' + raw[:800])
        sys.exit(2)
    decision = dict(source='jev-live', model=MODEL, state=dict(STATE))
    order = ans.get('order', {})
    risk = ans.get('riskiest', {})
    decision['order'] = order.get('choice')
    decision['order_probs'] = {k: float(order.get('probabilities', {}).get(k, 0.0))
                               for k in NEXT_BLOCK}
    decision['riskiest'] = risk.get('choice')
    decision['riskiest_probs'] = {k: float(risk.get('probabilities', {}).get(k, 0.0))
                                  for k in RISKIEST}
    decision['needs_human'] = bool((ans.get('human', 1) or 0) > 0.5)
    decision['needs_human_prob'] = float(ans.get('human', 0) or 0.0)
    decision['readiness'] = int((ans.get('readiness', {}) or {}).get('score', 0))
    decision['confidence'] = float(order.get('confidence', 0.0))
    valid = (decision['order'] in NEXT_BLOCK and decision['riskiest'] in RISKIEST
             and 0 <= decision['readiness'] <= 4)
    decision['authored_only'] = valid
    if not valid:
        decision['source'] = 'classical-fallback'
        decision['reason'] = 'beam returned out-of-set choice; fallback'
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'house_beam_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S'))
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(dict(decision=decision, raw=ans), fh, indent=2)
    print(json.dumps(decision, indent=2))
    print('receipt: ' + out)


if __name__ == '__main__':
    main()
