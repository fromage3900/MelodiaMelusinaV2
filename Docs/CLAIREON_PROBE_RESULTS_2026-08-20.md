# Claireon Tool-Call Probe Results — 2026-08-20

Harness: `Tools/test_claireon_toolcalls.py`
Reports: `Saved/Audit/claireon_probe_<model>_2026-08-20.json`

## What this measures (and what it does NOT)

Claireon exposes exactly TWO MCP tools: `tool_search` (discover) and
`python_execute` (act, where catalog tools are called as `claireon.<name>(...)`).
This probe scores whether a local model produces that two-step discovery pattern
under a 2-tool manifest, across 8 tasks.

**This is a CLIENT-SIDE measurement.** The Claireon editor was DOWN for every run
(port 64998 not listening, proxy 43017 not listening). No `python_execute` ever
round-tripped to Unreal. This measures model behaviour under Claireon's manifest
shape — it is NOT evidence that Claireon works on UE 5.8.

Scored axes:
| Axis | Meaning |
|---|---|
| surface adherence | Stayed inside the 2 real tools (didn't invent a flat tool) |
| tool choice | Picked the correct one of the 2 |
| arg shape | Used the expected arg key (`query` / `tool_name` / `code`) |
| arg subject | Arg value points at the right subject |

Pass = correct tool AND correct arg key.

## Results (2 models completed)

| Model | Pass | Surface | Tool choice | Arg shape | Arg subject |
|---|---|---|---|---|---|
| qwen2.5-coder:7b | **7/8** | 100% | 87.5% | 87.5% | 87.5% |
| deepseek-coder:6.7b | **1/8** | 37.5% | 12.5% | 12.5% | 25.0% |

### qwen2.5-coder:7b — 7/8
Only failure: `execute_python_direct` — asked to run Python that counts selected
actors, it chose `tool_search` instead of `python_execute`. Over-searching, which
is the safe direction of error for an unsandboxed execution tool.

Notably passed `no_flat_hallucination`: told to "compile the Blueprint at
/Game/...", it searched instead of inventing a flat `bp_compile` tool. That is
exactly the behaviour Claireon's 2-tool design depends on.

100% surface adherence — never once hallucinated a tool outside the manifest.

### deepseek-coder:6.7b — 1/8
The failure mode is **format compliance, not reasoning**. Raw outputs show it
frequently identifies the right tool in prose but never emits JSON:

- `discover_blueprint`: "You can use the `tool_search` tool to search for tools
  related to editing Blueprint graphs..." — correct answer, unparseable form.
- `widget_discovery`: "you can use the `python_execute` tool with the `inspect`
  module" — wrong tool AND hallucinated a module.
- `detail_named_tool`: refused outright — "I'm sorry, but I can't provide... the
  tool `bp_apply_delta` is not available."

5 of 8 responses were unparseable prose. This model is not usable as an MCP
client without a constrained-decoding layer.

## BLOCKER: Ollama runtime failure (unresolved)

The remaining 6 models could not be scored. Ollama's `llama-server` crashes on
model load:

```
{"error":"llama-server process has terminated: exit status 0xffffffff: NTSTATUS 0xffffffff"}
```

Confirmed crashing via direct `curl` to `/api/chat`, bypassing the harness
entirely: `qwen2.5-coder:14b`, `deepseek-r1:14b`, `deepseek-r1:7b`,
`qwen3.8-27b`, and — critically — **`qwen2.5-coder:7b` and
`deepseek-coder:6.7b`, which had completed successfully ~20 minutes earlier**.

That regression is the important detail: the two passing runs above are real
(reports on disk, timestamped 12:49 and 13:13), but the runtime degraded during
the session. This is an Ollama/host problem, not a harness problem.

- Memory was NOT the cause: 20 GB free of 64 GB at crash time.
- Ollama's API stayed up throughout (`/api/tags` responded); only the model
  subprocess died.
- `/api/ps` showed models loading, then an empty list after each crash.

Not scored: qwen2.5-coder:14b, deepseek-r1:14b, deepseek-r1:7b, qwen3.8-27b,
muse-glimmer-30b, hf.co/bartowski/Muse-Glimmer-30B-GGUF.

### To resume
Restart the Ollama service, then:
```
python Tools/test_claireon_toolcalls.py --model qwen2.5-coder:14b --timeout 300
python Tools/test_claireon_toolcalls.py --all
```
If crashes persist, check the Ollama server log and GPU driver state. The `0xffffffff`
NTSTATUS on model load typically indicates a runtime/driver fault, not a bad GGUF
(the same files loaded successfully earlier in this session).

## Harness note (shell quirk, recorded)

Running the probe under this session's MSYS bash intermittently returned exit 127
or exit -1 with no stdout on long calls. Reports still land on disk when the model
responds; trust `Saved/Audit/*.json` over terminal stdout. Direct `curl` to
`/api/chat` is the reliable way to isolate model-vs-harness failures.

## Honest read

One data point is genuinely encouraging: a 7B local coder model hit 100% surface
adherence and 7/8 on Claireon's discovery pattern, including correctly refusing to
hallucinate a flat tool name. That is the single most relevant question for
Claireon's "expose almost nothing, let the model search" bet, and it points the
right way.

But n=2 with the editor offline is not a benchmark. The open question from
`Docs/Research/UE_AGENT_BENCHMARK_DESIGN_2026-08-19.md` — does `tool_search` →
`python_execute` work with a non-Claude client — remains open until Claireon
actually builds on 5.8 and a real `python_execute` round-trips.
