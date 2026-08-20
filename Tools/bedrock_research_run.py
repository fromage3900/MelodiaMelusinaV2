#!/usr/bin/env python3
"""Clean Bedrock research runner — invokes models via Converse API."""
import sys
import os
import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import boto3
from botocore.config import Config

cfg = Config(retries={"max_attempts": 5, "mode": "adaptive"}, region_name="us-east-1")
rt = boto3.client("bedrock-runtime", config=cfg, region_name="us-east-1")

PROMPTS = {
    "ue-indie-best-practices": """You are a research assistant with deep knowledge of Unreal Engine game development, particularly indie development practices from 2023-2026.

Research and produce a comprehensive report on the top 0.1% Unreal Engine indie development workflows and practices for UE5. Cover:
1) Source control discipline (Git+LFS for UE5, gitignore patterns, locking for 2000+ asset files)
2) CI/CD pipeline design (automated build/cook/deploy)
3) Modular C++ architecture (module structure, Blueprint-Native bridges, hot-reload avoidance)
4) Automation stack (Python scripting, BuildGraph, headless testing)
5) Asset pipeline optimization (FBX import, texture streaming, auditing)
6) Performance profiling and iteration loops (fast iteration, shader compilation)
7) Documentation and knowledge management for solo devs
8) Multi-agent AI collaboration workflows (Cursor, Claude, Copilot orchestration)

For each, name specific devs/teams, their tools/configs, and measurable outcomes. Cite real tool names, GitHub repos, config files. Target: UE 5.8 project shipping a Persona-lite JRPG with rhythm combat.""",

    "cn-jp-git-git-resources": """You are a research assistant fluent in Chinese (Simplified) and Japanese (native level).

Research and produce a comprehensive bilingual report (Chinese + Japanese sections) on Unreal Engine / Git / Source Control resources, tutorials, and communities in Chinese and Japanese for indie game developers.

CHINESE: communities (Tieba, Zhihu, Bilibili, QQ groups), Git/LFS tutorials in Chinese, UE5 tutorials by Chinese creators, GitHub/Gitee repos with UE5+Git workflows, domestic LFS solutions.

JAPANESE: communities (5ch, Qiita, Zenn, BOOTH, UEGJ), Git/LFS tutorials in Japanese, UE5 tutorials by Japanese creators (YouTube, NicoNico, Qiita, Zenn), GitHub repos with UE5+Git, Persona-series technical analysis (social link/calendar/combat architecture).

For BOTH: provide search terms (English + native script) for Google/Baidu/Qiita/Zenn/Bilibili/NicoNico, specific URLs, quality ratings (High/Medium/Low), active status. Format as structured bilingual report with search term tables.""",

    "persona-integration-parallelization": """You are a research assistant with deep expertise in game architecture for Persona-style JRPGs (Persona 3, 4, 5, Royal, and indie reimplementations).

Research and produce a comprehensive technical report on methods to parallelize and improve the integration layer for Persona-styled video games. Cover:
1) Layer decoupling strategies (calendar/social vs combat vs narrative)
2) Event bus and command patterns for cross-layer communication
3) Save system architecture for "one action per day" model across process restarts
4) Authority delegation (which layer owns which state)
5) Persona 5 Royal technical analysis (Velvet Room, Mementos, daily life data sharing)
6) Indie Persona reimplementations and their published architectures
7) Parallel development patterns for multi-lane dev teams
8) Persona-specific anti-patterns (shared mutable state, race conditions)

Provide concrete architectural patterns, code-level examples (C++/Blueprint/UE5), specific recommendations for a Persona-lite JRPG on UE 5.8 with: standalone JRPG template base, QuillScript narrative, Harmonix-style rhythm overlay, social stats/bond system. Include interface names, subsystem names, data flow diagrams (ASCII), and prioritized recommendations. Target: existing Melodia architecture (MelodiaCore, MelodiaIntegration, TurnBasedJRPGTemplate, QuillScript).""",
}

# Model fallback chains
MODELS = {
    "ue-indie-best-practices": ["us.anthropic.claude-3-sonnet-20240229-v1:0", "us.openai.gpt-5.6-sol", "qwen.qwen3-coder-next"],
    "cn-jp-git-git-resources": ["qwen.qwen3-coder-next", "us.anthropic.claude-3-sonnet-20240229-v1:0", "us.openai.gpt-5.6-sol"],
    "persona-integration-parallelization": ["us.anthropic.claude-3-sonnet-20240229-v1:0", "us.openai.gpt-5.6-sol", "qwen.qwen3-coder-next"],
}

OUTPUT_DIR = "BS_GodFile/Docs/Research"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def invoke(prompt, model_id, max_tokens=8192):
    """Invoke Bedrock Converse API."""
    response = rt.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3, "topP": 0.9},
    )
    text = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})
    return text, usage


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "all"
    if topic == "all":
        topics = list(PROMPTS.keys())
    else:
        topics = [topic]

    for t in topics:
        prompt = PROMPTS[t]
        for model_id in MODELS[t]:
            try:
                print(f"  Trying {model_id} for {t}...", file=sys.stderr, flush=True)
                text, usage = invoke(prompt, model_id)
                print(f"  OK: input={usage.get('inputTokens', '?')} output={usage.get('outputTokens', '?')}", file=sys.stderr, flush=True)
                filename = f"{t}.md"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# Research: {t}\n\n")
                    f.write(f"Source: Amazon Bedrock Converse API (model: {model_id})\n")
                    f.write(f"Date: {datetime.datetime.now().isoformat()}\n\n")
                    f.write("---\n\n")
                    f.write(text)
                    if not text.endswith("\n"):
                        f.write("\n")
                print(f"  Written to {filepath}", file=sys.stderr, flush=True)
                break
            except Exception as e:
                print(f"  FAILED: {model_id}: {e}", file=sys.stderr, flush=True)
                continue
        else:
            print(f"  ALL MODELS FAILED for {t}", file=sys.stderr, flush=True)

    print("\n✅ Research complete.", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
