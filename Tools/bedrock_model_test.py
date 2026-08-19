#!/usr/bin/env python3
"""Quick test of which Bedrock models are invocable in this account."""
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import boto3

session = boto3.Session(profile_name="bedrock", region_name="us-east-1")
rt = session.client("bedrock-runtime")

profiles = [
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "global.openai.gpt-5.6-luna",
    "us.openai.gpt-5.6-sol",
    "mistral.mistral-large-2402-v1:0",
    "nvidia.nemotron-nano-12b-v2",
    "qwen.qwen3-coder-next",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
]

for p in profiles:
    try:
        resp = rt.converse(
            modelId=p,
            messages=[{"role": "user", "content": [{"text": "Hi"}]}],
            inferenceConfig={"maxTokens": 32, "temperature": 0.1},
        )
        print(f"OK: {p}", file=sys.stderr, flush=True)
    except Exception as e:
        emsg = str(e)[:120]
        print(f"FAIL: {p}: {emsg}", file=sys.stderr, flush=True)

print("Done.", file=sys.stderr, flush=True)
