# Melodia Render Queue — Humber to Home PC

Status: Fall 2026 production infrastructure.

The queue uses a dedicated render-queue Git branch carrying only tiny JSON job manifests. It does not merge into main. Render outputs remain under Saved/RenderFarm on the worker.

Authoring flow:
1. Finish and push the source change.
2. From Humber, run deploy/render_queue_submit.ps1.
3. The manifest records the exact source commit SHA.
4. On the home PC, use a dedicated clean render clone and run deploy/render_queue_worker.ps1.
5. The worker processes one job by default and records completion in Saved/RenderFarm/queue-ledger.json.

Blender inputs must be repository-relative tracked blend files. Blender jobs may use frame ranges.

Unreal jobs are distributed by complete shot or camera-cut / Level Sequence, not arbitrary temporal frame slicing.

Safety rules:
- no public SSH;
- no network scanning;
- no daemon on Humber;
- no credentials in manifests;
- worker refuses a dirty checkout;
- revision changes require explicit AllowCheckout;
- use a dedicated home render clone.

First acceptance proof:
- queue a five-frame Blender job;
- inspect it on the worker without Execute;
- run it with Execute and AllowCheckout;
- confirm the render job manifest and queue ledger report completion.
