"""Jev round 3: house track next block (beam, json_object, authored-only)."""
import json
import os
import sys
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'Tools'))
from model_router import _nous_creds  # noqa: E402

MODEL = 'reflection/beam-1.0-501b-a23b:free'
NEXT = {
    "COLLISION_OUTPUT": "Emit collision_geo walk/capsule groups from the assembler and prove a capsule sweep offline before any editor cook.",
    "UE_STAGE": "Import the staged HDA, instantiate, idle-editor cook, readback sections/materials/capture.",
    "CORRIDOR_ROOF": "Roof rebuild + corridor-link specs from the assembler vocabulary, prototyped in pure Python.",
    "COMMIT_DOCS": "Receipts, pin, status closeout and force-add of reviewed files.",
}
RISK = {
    "UE_COOK_SCALE": "The full-house cook OOMs or signal-11s live like the 2026-10-22 RoomShell cook.",
    "PCG_UE_BRIDGE": "UE PCG fails to read the house point custom data (surface/room/surf_id).",
    "SOCKET_TRANSFORM": "Portal frame yaw/offset math misplaces linked rooms.",
    "DRIVE_REGRESSION": "The pending drive/restore proof fails and invalidates parm wiring.",
}
STATE = {
    "assembler": "green (23,117 prims, all_pass, committed)",
    "house_hda": "green (arch + 1,310 PCG pts, artist parms, committed)",
    "editor_tools": "monolith namespace absent from catalog; editor restarted fresh",
    "drive_restore": "running in background, receipt pending",
    "missing": "collision_geo output, corridor/roof rebuild, manifest addendum",
}
PROMPT = """You are a production judgment service for a Houdini procedural-house build.
Verified state:
%s
Answer exactly these four questions in ONE JSON object. For Choice questions give
"choice" (one of the listed keys), "confidence" (0-1), and "probabilities"
(a map of EVERY listed key summing to 1).
1. order (Choice): which single next block unblocks the working procedural house fastest?
%s
2. riskiest (Choice): which assumption is riskiest if wrong?
%s
3. human (Noul 0-1): does an owner decision gate execution before agents run the next block?
4. readiness (Score 0-4: 0 blocked, 1 fragile, 2 partial, 3 ready, 4 proven).
Return ONLY JSON: {"order": {"choice": ..., "confidence": ..., "probabilities": {...}}, "riskiest": {...}, "human": <float>, "readiness": {"score": <int>, "probabilities": [...]}}.
""" % (json.dumps(STATE), json.dumps(NEXT), json.dumps(RISK))


def main():
    key, base = _nous_creds()
    payload = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}],
               "temperature": 0.2, "max_tokens": 6000,
               "response_format": {"type": "json_object"}}
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + key}, method='POST')
    with urllib.request.urlopen(req, timeout=240) as resp:
        raw = json.loads(resp.read().decode())['choices'][0]['message']['content']
    try:
        ans = json.loads(raw)
    except Exception:
        print('NON-JSON-RESPONSE: ' + str(raw)[:300])
        sys.exit(2)
    decision = dict(source='jev-live', model=MODEL, state=dict(STATE))
    order, risk = ans.get('order', {}), ans.get('riskiest', {})
    decision['order'] = order.get('choice')
    decision['order_probs'] = {k: float(order.get('probabilities', {}).get(k, 0.0))
                               for k in NEXT}
    decision['riskiest'] = risk.get('choice')
    decision['riskiest_probs'] = {k: float(risk.get('probabilities', {}).get(k, 0.0))
                                  for k in RISK}
    decision['needs_human'] = bool((ans.get('human', 1) or 0) > 0.5)
    decision['needs_human_prob'] = float(ans.get('human', 0) or 0.0)
    decision['readiness'] = int((ans.get('readiness', {}) or {}).get('score', 0))
    decision['confidence'] = float(order.get('confidence', 0.0))
    decision['authored_only'] = (decision['order'] in NEXT
                                 and decision['riskiest'] in RISK)
    if not decision['authored_only']:
        decision['source'] = 'classical-fallback'
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'house_beam_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S'))
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(dict(decision=decision, raw=ans), fh, indent=2)
    print(json.dumps(decision, indent=2))
    print('receipt: ' + out)


if __name__ == '__main__':
    main()
