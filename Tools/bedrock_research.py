#!/usr/bin/env python3
"""
bedrock_research.py — Use Amazon Bedrock Converse API to research
top-tier UE indie dev practices, Chinese/Japanese git+UE resources, and
Persona-style game integration parallelization methods.

Uses Claude 3.7 Sonnet (cross-region) for English-depth reasoning and
Qwen3-Coder for Chinese/Japanese linguistic discovery.

Usage:
  python Tools/bedrock_research.py --topic ue-indie-best-practices
  python Tools/bedrock_research.py --topic cn-jp-git-git-resources
  python Tools/bedrock_research.py --topic persona-integration-parallelization
  python Tools/bedrock_research.py --topic all
"""
from __future__ import annotations

import argparse
import json
import sys

import boto3
from botocore.config import Config

# Retry config: adaptive mode handles both throttling and burst
RETRY_CFG = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},
    region_name="us-east-1",
)

bedrock_rt = boto3.client("bedrock-runtime", config=RETRY_CFG, region_name="us-east-1")

# ── Prompts ───────────────────────────────────────────────────────────────────

PROMPT_UE_INDI = """You are a research assistant with deep knowledge of Unreal Engine game development, particularly indie development practices from 2023-2026.

Research and produce a comprehensive report on the **top 0.1% Unreal Engine indie development workflows and practices** — the practices used by the most successful, technically sophisticated solo devs and micro-teams shipping UE5 games in 2024-2026.

Cover these areas:
1. **Source control discipline**: Git + Git LFS strategies specifically for UE5 (what file types to track, what to gitignore, locking strategies for 2,000+ asset files)
2. **CI/CD pipeline design**: Automated build testing, automated cooking, automated deployment to stores
3. **Modular C++ architecture**: How top devs structure C++ modules, plugins, and Blueprint-Native bridges to avoid recompilation bottlenecks
4. **Automation stack**: Python scripting, build graph, automation tools, headless testing
5. **Asset pipeline optimization**: FBX import automation, texture streaming, asset auditing
6. **Performance profiling and iteration loops**: Fast iteration cycles, shader compilation optimization
7. **Documentation and knowledge management**: How solo devs maintain docs while developing
8. **Multi-agent AI collaboration**: How developers combine Cursor, Claude, ChatGPT, GitHub Copilot in their workflow

For each area, name specific indie devs or micro-studios (by handle/studio name where known), their concrete tools/scripts/configurations, and the measurable outcomes they achieved (e.g., "reduced build times from X to Y", "cut iteration time from Z minutes to W seconds").

Format as a structured Markdown report with clear sections, bullet points, and concrete technical recommendations that can be directly applied to a UE 5.8 project. Be specific and avoid generic advice.

Cite specific tool names, GitHub repos, configuration file names, and workflow scripts where you can. This is research for a real UE 5.8 indie project shipping a Persona-lite JRPG with rhythm combat."""

PROMPT_CN_JP = """You are a research assistant fluent in Chinese (Simplified) and Japanese (native level). You have deep knowledge of the technical developer communities in mainland China, Japan, and the broader CJK region.

Research and produce a comprehensive report on **Unreal Engine / Git / Source Control resources, tutorials, and communities in Chinese and Japanese** that are relevant to indie game developers.

For CHINESE (Simplified Chinese) resources, cover:
1. **Major communities**: BBS forums (like Tieba, Zhihu, Bilibili tech creators), Discord servers, QQ groups
2. **Git/Git-LFS tutorials**: Specific Chinese-language guides, video series, blog posts about Git+LFS for UE game dev
3. **Unreal Engine tutorials**: Chinese developers creating UE5 content (Bilibili creators, Zhihu authors), specific series about source control
4. **GitHub repositories**: Chinese indie devs' UE5 projects on GitHub with proper Git+UE5 workflows (search for repos tagged with 'unreal-engine', 'ue5', 'git-lfs', '蓝图', '虚幻引擎')
5. **Tools and platforms**: Chinese Git hosting (Gitee, GitLab China), domestic LFS solutions

For JAPANESE resources, cover:
1. **Major communities**: 2ch/5ch, Qiita, Zenn, BOOTH, Japanese Unreal Engine user group
2. **Git/Git-LFS tutorials**: Specific Japanese-language guides, video series, blog posts
3. **Unreal Engine tutorials**: Japanese creators on YouTube, NicoNico, Qiita, Zenn about UE5 + source control
4. **GitHub repositories**: Japanese devs' UE5 projects with Git workflows
5. **Persona-series specific**: Japanese technical analysis of Persona 5/4/3 game architecture, social link systems, calendar mechanics — especially how indie devs replicate these in UE5

For BOTH:
- Provide **search terms** (both English and native script) that would find these resources (for Google/Bing, Baidu, Qiita/Zenn, Bilibili, NicoNico)
- Provide **specific URLs** where possible (blog posts, video series, GitHub repos, forum threads)
- Rate each resource by quality/reliability (High/Medium/Low)
- Note which resources are **currently active** (as of 2025-2026) vs archived

Format as a structured bilingual report with parallel Chinese and Japanese sections, search term tables, and a curated resource list with URLs and quality ratings.

Include **Persona series technical breakdowns** by Japanese devs: how the social link/calendar system is architected, how combat phases interleave with narrative, save system patterns."""

PROMPT_PERSONA = """You are a research assistant with deep expertise in game architecture, specifically Persona-style JRPGs (Persona 3, 4, 5, and their indie reimplementations).

Research and produce a comprehensive report on **methods to parallelize and improve the integration layer for Persona-styled video games**, focusing on how the narrative layer, social simulation layer, calendar/day-cycle layer, JRPG combat layer, and rhythm/action layer can be developed in parallel without tight coupling.

Cover these areas:
1. **Layer decoupling strategies**: How to separate the calendar/social simulation from combat from narrative, so teams can work on each independently
2. **Event bus and command patterns**: How Persona games route inputs between layers (e.g., "social action triggers combat stat change triggers narrative flag")
3. **Save system architecture**: How Persona games handle save round-trips across process restarts (critical for Persona's "one action per day" model)
4. **Authority delegation**: Which layer owns which state (narrative owns story flags, combat owns HP/damage, social owns bond ranks, calendar owns day progression)
5. **Persona 5 Royal technical analysis**: The specific integration points between the Velvet Room (meta-NPC), Mementos (dungeon), and daily life (social links) — how do these share data?
6. **Indie reimplementations**: Games like "Persona 5 Royal" reimplementations, "Project Re Fantasy" clones, or indie Persona-like games that have published their architecture (e.g., "Aria the Galgame", "Twin Mirror" alternatives)
7. **Parallel development patterns**: How to split Persona-style games across multiple dev lanes (social sim lane, combat lane, narrative lane, calendar lane) while maintaining integration integrity
8. **Persona-specific anti-patterns**: What breaks when you try to parallelize Persona-style games (e.g., shared mutable state between calendar and combat, race conditions in stat updates)

Provide concrete architectural patterns, code-level examples (C++/Blueprint/UE5), and specific recommendations for a Persona-lite JRPG built in UE 5.8 that uses:
- A standalone JRPG template as the mechanical base
- QuillScript for narrative dialogue
- A rhythm combat overlay (Harmonix-style)
- Social stats and bond rank system

Include specific interface names, subsystem names, and data flow diagrams that would work with the existing Melodia architecture (MelodiaCore, MelodiaIntegration, TurnBasedJRPGTemplate, QuillScript).

Format as a structured technical report with architecture diagrams (as text/ASCII), interface contracts, and prioritized recommendations."""

PROMPTS = {
    "ue-indie-best-practices": (PROMPT_UE_INDI, "us.anthropic.clause-sonnet-4-20250514-v2:0", "anthropic.claude-sonnet-4-20250514-v1:0"),
    "cn-jp-git-git-resources": (PROMPT_CN_JP, "qwen.qwen3-coder-next", "qwen.qwen3-coder-next"),
    "persona-integration-parallelization": (PROMPT_PERSONA, "us.anthropic.clause-sonnet-4-20250514-v2:0", "anthropic.claude-sonnet-4-20250514-v1:0"),
}


def invoke_model(prompt: str, primary_model: str, fallback_model: str, max_tokens: int = 8192) -> str:
    """Invoke Bedrock Converse API, trying primary model first, then fallback."""
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]
    inference_config = {"maxTokens": max_tokens, "temperature": 0.3, "topP": 0.9}

    for model_id in [primary_model, fallback_model]:
        try:
            print(f"  ↻ Invoking {model_id}...", file=sys.stderr)
            response = bedrock_rt.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig=inference_config,
            )
        except Exception as e:
            print(f"  ✗ {model_id} failed: {e}", file=sys.stderr)
            continue

        output = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        print(
            f"  ✓ {model_id} succeeded — "
            f"input={usage.get('inputTokens', '?')} tokens, "
            f"output={usage.get('outputTokens', '?')} tokens",
            file=sys.stderr,
        )
        return output

    return f"ERROR: All model invocations failed for prompt starting with: {prompt[:80]}..."


def main():
    parser = argparse.ArgumentParser(description="Bedrock-powered research for Melodia workflows")
    parser.add_argument(
        "--topic",
        choices=["ue-indie-best-practices", "cn-jp-git-git-resources", "persona-integration-parallelization", "all"],
        default="all",
    )
    parser.add_argument(
        "--output-dir",
        default="BS_GodFile/Docs/Research",
    )
    args = parser.parse_args()

    import os
    os.makedirs(args.output_dir, exist_ok=True)

    if args.topic == "all":
        topics = list(PROMPTS.keys())
    else:
        topics = [args.topic]

    results = {}
    for topic in topics:
        prompt, primary, fallback = PROMPTS[topic]
        print(f"\n🔬 Researching: {topic}", file=sys.stderr)
        result = invoke_model(prompt, primary, fallback, max_tokens=8192)
        results[topic] = result

        # Write to file
        filename = f"{topic}.md"
        filepath = os.path.join(args.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Research: {topic}\n\n")
            f.write(f"Source: Amazon Bedrock Converse API\n")
            f.write(f"Date: {__import__('datetime').datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            f.write(result)
        print(f"  → Written to {filepath}", file=sys.stderr)

    print("\n✅ All research complete.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
