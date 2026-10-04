#!/usr/bin/env python3
"""Melodia Video-QA Bridge -- Gemini Video Understanding for Unreal PIE Captures.

Provides a reliable local CLI for Melodia agents to send Unreal PIE captures
to Gemini video understanding and receive structured, machine-readable visual QA reports.

Usage:
    python Tools/gemini_video_qa.py \\
        --video Saved/Captures/UI/overworld_ui_pass.mp4 \\
        --profile overworld-ui \\
        --out Saved/Audit/VideoQA/overworld_ui_pass.json

Profiles:
    - overworld-ui : Overworld UI and HUD integration (Bow HUD, reticles, bars, dialog, compendium, input focus, cursor leakage)
    - animation    : Character locomotion, combat releases, WaveHarp aim/draw/release, secondary motion, posture continuity
    - environment  : Level composition, Substrate toon shading, lighting, PCG scatter, visual stability
    - choral-sheep : Choral Sheep companion behaviors, wool SSS, adornments, follow paths, harmonize reactions
    - gameplay     : End-to-end rhythm-JRPG loop: navigation, battle transition, rhythm grading, reward feedback
    - custom       : User-defined evaluation criteria via --prompt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Official Google GenAI SDK imports
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

DEFAULT_MODEL = "gemini-3.8-flash"
SCHEMA_VERSION = 1
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_TIMEOUT = 600.0

# ---------------------------------------------------------------------------
# Profile definitions and system instructions
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict[str, Any]] = {
    "overworld-ui": {
        "description": "Overworld UI and HUD integration pass (Bow HUD, reticles, bars, dialogue, compendium, input focus, cursor leakage)",
        "default_processing": "agentic",
        "system_instruction": (
            "You are a professional visual QA analyst evaluating Unreal Engine 5 gameplay capture video "
            "for the rhythm-JRPG 'Melodia'. You are inspecting the Overworld UI and HUD systems.\n\n"
            "Distinguish strictly between HARD FUNCTIONAL REQUIREMENTS and DESIGN EXPECTATIONS:\n\n"
            "A. HARD FUNCTIONAL REQUIREMENTS (Severity: critical or high -> overall_verdict: FAIL):\n"
            "1. Input Focus & Cursor Leakage: The mouse cursor MUST ONLY be visible when interactive menus or compendium "
            "are active. When returning to overworld gameplay control, the cursor MUST be immediately hidden. "
            "Any cursor remaining visible during active exploration/locomotion is a HIGH-severity defect.\n"
            "2. Menu Continuity & Navigation: Opening a menu must display the correct panel once without duplication. "
            "Closing a menu must cleanly dismiss the panel, restore full gameplay movement/camera control, and leave no stuck overlays.\n"
            "3. Layout Integrity: No sibling widget overlaps, no off-screen clipping of buttons or critical info, proper 16:9 margins.\n"
            "4. Legibility & State: Text must not be truncated, box-clipped, or displaying raw engine placeholder/debug strings.\n\n"
            "B. DESIGN EXPECTATIONS & POLISH (Severity: medium, low, or info -> overall_verdict: PASS or REVIEW):\n"
            "1. BowHUD Reticle & Charge Arc: Reticle dims during idle exploration (~32-50% opacity); charge arc/chord dots reflect weapon state. "
            "Do not FAIL solely on minor opacity or ornamental tuning if functionality is intact.\n"
            "2. Status Bars & Cartouches: Health/MP bar fills (coral/blue) and F-interact cartouche sizing (~340-370px). "
            "Report minor layout/styling nuances as low/medium polish items, not functional blockers.\n"
            "3. Transitions: Fade transitions and menu opening/closing animations should ease smoothly without single-frame black pops.\n\n"
            "Provide timestamps (mm:ss.fff or hh:mm:ss) for every observed interaction, defect, healthy section, and manual recheck."
        ),
    },
    "animation": {
        "description": "Character locomotion, combat releases, WaveHarp aim/draw/release, secondary motion, posture continuity",
        "default_processing": "agentic",
        "system_instruction": (
            "You are a senior technical animator and visual QA specialist reviewing Unreal Engine 5 gameplay captures "
            "of character motion in 'Melodia'.\n\n"
            "Key evaluation criteria:\n"
            "1. Locomotion Continuity: Idle, walk, run, turn, and stop transitions. Check for foot sliding (skating), "
            "root pops, sudden teleportation, or orientation snaps.\n"
            "2. Stressed Shoulder Poses: Check shoulder silhouette continuity, clavicle popping, armpit collapse, "
            "and unnatural shoulder-to-arm spacing during weapon draws and idle-to-attack transitions.\n"
            "3. Combat & Weapon Alignment: WaveHarp floating astrolabe placement, five-shot chord basic attack releases "
            "(semitones 0/4/7/11/12), RMB charged draw/hold/fire/recovery. Verify prop grip alignment and left-hand contact.\n"
            "4. Secondary Motion: Kawaii physics simulation on hair strands, ornaments, pearl jewelry, shirt hem, skirt chains. "
            "Check for mesh penetration, explosive physics oscillations, or persistent drift.\n"
            "5. Zero T-Pose Tolerance: The character must never snap to T-pose or reference pose during state transitions or montage stops.\n\n"
            "Provide precise timestamps for every animation interaction, deformation defect, healthy sequence, and manual recheck."
        ),
    },
    "environment": {
        "description": "Level composition, Substrate toon shading, lighting, PCG scatter, and visual stability",
        "default_processing": "agentic",
        "system_instruction": (
            "You are an environment artist and technical director reviewing visual fidelity and composition in Unreal Engine 5 "
            "levels for 'Melodia' (e.g., L_MelusinaMorning, LV_SeaAbove_Prototype, L_SakuraPath).\n\n"
            "Key evaluation criteria:\n"
            "1. Geometry & Shading: Substrate multi-layer materials, toon shading, rock/architecture meshes, water shaders, "
            "no z-fighting, no texture streaming delay or missing mipmaps.\n"
            "2. Lighting & Atmosphere: Ultra Dynamic Sky, volumetric clouds, sunlight gradient, volumetric fog, rim lighting on hero assets.\n"
            "3. Scatter & Foliage: PCG flower and grass scatter density, no floating meshes or ungrounded foliage, no geometry penetration.\n"
            "4. Camera & Viewport: No near-plane clipping, smooth camera tracking, no abrupt LOD pops or shadow popping.\n\n"
            "Provide precise timestamps for all observations."
        ),
    },
    "choral-sheep": {
        "description": "Choral Sheep companion behaviors, wool SSS, adornments, follow paths, and harmonize reactions",
        "default_processing": "agentic",
        "system_instruction": (
            "You are a visual QA evaluator examining the 'Choral Sheep' companion creature in 'Melodia'.\n\n"
            "Key evaluation criteria:\n"
            "1. Follow & Pathing: Sheep following player pawn, path navigation, distance maintenance, dell arrival transitions.\n"
            "2. Animations: Idle, walk, trot, graze, bleat, ear flick, tail wag, and harmonic resonance.\n"
            "3. Aesthetics: Wool subsurface scattering (SSS), wool strand styling, horns, floral crown stability, emissive chime response on musical triggers.\n"
            "4. Interaction: Player proximity response, harmonize reaction, facial/eye shader expressions.\n\n"
            "Provide precise timestamps for all companion behaviors and defects."
        ),
    },
    "gameplay": {
        "description": "End-to-end rhythm-JRPG loop: navigation, battle transition, rhythm grading, reward feedback",
        "default_processing": "agentic",
        "system_instruction": (
            "You are a gameplay QA lead testing the rhythm-JRPG gameplay loop in 'Melodia'.\n\n"
            "Key evaluation criteria:\n"
            "1. Seams: Quill narrative dialogue -> Phoenix/TurnBased battle encounter -> Rhythm combat execution -> Graded result -> Return to exploration.\n"
            "2. Rhythm Highway: Note highway readability, note approach timing, lane hit burst Niagara particles, grade pop feedback (PERFECT, GREAT, GOOD, MISS).\n"
            "3. Damage & Feedback: Floating damage numbers, enemy hit reactions, sound/visual synchrony, HP bar updates.\n"
            "4. Controls: Seamless FLOW (real-time movement/bow) to SEQUENCE (rhythm mini-game) and back.\n\n"
            "Provide precise timestamps for all gameplay transitions, note hits, and UI updates."
        ),
    },
    "custom": {
        "description": "User-defined evaluation profile using custom prompt instructions",
        "default_processing": "agentic",
        "system_instruction": (
            "You are an expert game visual QA analyst reviewing Unreal Engine gameplay capture video. "
            "Inspect the video according to user-supplied evaluation criteria and report structured observations, "
            "interactions, defects, healthy sections, and manual rechecks with precise timestamps."
        ),
    },
}

# Strict JSON Schema passed to Gemini response_format
STRUCTURED_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_verdict": {
            "type": "string",
            "enum": ["PASS", "FAIL", "REVIEW"],
            "description": "Overall QA verdict: PASS if all expected visual behaviors passed and no critical/high defects were found; FAIL if any critical or high defect occurred; REVIEW if ambiguous or manual recheck required.",
        },
        "interactions": {
            "type": "array",
            "description": "List of distinct UI or gameplay interactions observed in the capture.",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "description": "Timestamp in mm:ss.fff or hh:mm:ss format where the interaction occurred."},
                    "control": {"type": "string", "description": "Name of the UI control, button, or gameplay element tested (e.g. Compendium, Reticle, Dialogue)."},
                    "expected": {"type": "string", "description": "Expected visual outcome for this control."},
                    "observed": {"type": "string", "description": "Actual observed visual outcome in the video."},
                    "verdict": {"type": "string", "enum": ["PASS", "FAIL", "REVIEW"], "description": "Verdict for this specific interaction."},
                    "confidence": {"type": "number", "description": "Confidence score between 0.0 and 1.0."},
                    "evidence_type": {"type": "string", "description": "Evidence type, e.g. visual_observation."},
                },
                "required": ["timestamp", "control", "expected", "observed", "verdict", "confidence", "evidence_type"],
            },
        },
        "defects": {
            "type": "array",
            "description": "List of visual, layout, animation, or focus defects identified in the video.",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "description": "Timestamp in mm:ss.fff or hh:mm:ss where the defect was observed."},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"], "description": "Severity level."},
                    "category": {"type": "string", "description": "Defect category, e.g. input_focus, layout_overlap, animation_pop, visual_glitch, text_clipping."},
                    "observation": {"type": "string", "description": "Concrete description of the observed defect."},
                    "expected": {"type": "string", "description": "What was expected instead."},
                    "confidence": {"type": "number", "description": "Confidence score between 0.0 and 1.0."},
                    "evidence_type": {"type": "string", "description": "Evidence type, e.g. visual_observation."},
                    "recommended_recheck": {"type": "string", "description": "Recommended frame range or action to inspect."},
                },
                "required": ["timestamp", "severity", "category", "observation", "expected", "confidence", "evidence_type", "recommended_recheck"],
            },
        },
        "healthy_sections": {
            "type": "array",
            "description": "Continuous time spans where features operated cleanly without defects.",
            "items": {
                "type": "object",
                "properties": {
                    "start_timestamp": {"type": "string", "description": "Start timestamp of healthy section."},
                    "end_timestamp": {"type": "string", "description": "End timestamp of healthy section."},
                    "feature": {"type": "string", "description": "Feature or subsystem functioning properly."},
                    "observation": {"type": "string", "description": "Summary of healthy behavior."},
                },
                "required": ["start_timestamp", "end_timestamp", "feature", "observation"],
            },
        },
        "manual_rechecks": {
            "type": "array",
            "description": "Ambiguous moments requiring manual human or high-resolution re-inspection.",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "description": "Timestamp requiring review."},
                    "reason": {"type": "string", "description": "Reason for uncertainty."},
                    "context": {"type": "string", "description": "Context or surroundings of the event."},
                },
                "required": ["timestamp", "reason", "context"],
            },
        },
    },
    "required": ["overall_verdict", "interactions", "defects", "healthy_sections", "manual_rechecks"],
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def sanitize_secret(text: str) -> str:
    """Redact any potential API key patterns or sensitive tokens from error messages."""
    if not text:
        return ""
    # Redact Google API keys (AIza...)
    text = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_API_KEY]", text)
    # Redact generic bearer tokens
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9\-\._~+/]+=*", r"\1[REDACTED_TOKEN]", text, flags=re.IGNORECASE)
    return text


def compute_file_hash_and_size(path: Path | str) -> tuple[str, int]:
    """Calculate SHA256 hex digest and file size in bytes."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Video file not found: {p}")
    hasher = hashlib.sha256()
    size = 0
    with p.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


def get_api_key(strict: bool = True) -> str | None:
    """Retrieve GEMINI_API_KEY from environment only. Never prints or logs value."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key and strict:
        sys.stderr.write(
            "Error: GEMINI_API_KEY environment variable is not set.\n"
            "Please set GEMINI_API_KEY in your environment before running Tools/gemini_video_qa.py.\n"
        )
        sys.exit(1)
    return key or None


def verify_agentic_processing(steps: list[Any]) -> tuple[bool, list[dict[str, Any]]]:
    """Verify from interaction response steps whether video processing actually occurred.

    The presence of `processing_call` / `processing_result` steps confirms that
    Gemini dynamically inspected video segments.
    """
    processing_steps: list[dict[str, Any]] = []
    if not steps:
        return False, processing_steps

    for step in steps:
        step_type = getattr(step, "type", None) or (step.get("type") if isinstance(step, dict) else None)
        if step_type in ("processing_call", "processing_result"):
            entry: dict[str, Any] = {"type": step_type}
            step_id = getattr(step, "id", None) or (step.get("id") if isinstance(step, dict) else None)
            call_id = getattr(step, "call_id", None) or (step.get("call_id") if isinstance(step, dict) else None)
            if step_id:
                entry["id"] = str(step_id)
            if call_id:
                entry["call_id"] = str(call_id)
            processing_steps.append(entry)

    verified = len(processing_steps) > 0
    return verified, processing_steps


def upload_and_poll_video(
    client: Any,
    video_path: Path,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    """Upload video using Files API and poll until processing reaches ACTIVE."""
    sys.stderr.write(f"Uploading {video_path.name} to Gemini Files API...\n")
    try:
        file_obj = client.files.upload(file=str(video_path))
    except Exception as exc:
        raise RuntimeError(f"Failed to upload video file: {sanitize_secret(str(exc))}") from exc

    file_name = file_obj.name
    sys.stderr.write(f"Uploaded file resource: {file_name}. Polling processing status...\n")

    start_time = time.time()
    while True:
        try:
            current_file = client.files.get(name=file_name)
        except Exception as exc:
            raise RuntimeError(f"Failed polling file status: {sanitize_secret(str(exc))}") from exc

        state_str = str(getattr(current_file, "state", "")).upper()
        if "ACTIVE" in state_str:
            sys.stderr.write(f"File {file_name} is ACTIVE and ready for interaction.\n")
            return current_file
        if "FAILED" in state_str:
            err = getattr(current_file, "error", "Unknown error")
            raise RuntimeError(f"Gemini file processing failed for {file_name}: {sanitize_secret(str(err))}")

        if time.time() - start_time > timeout:
            raise TimeoutError(f"Exceeded {timeout}s timeout waiting for video processing on {file_name}")

        time.sleep(poll_interval)


def parse_interaction_output(raw_text: str) -> dict[str, Any]:
    """Parse JSON output from Gemini response, stripping markdown code fences if present."""
    clean_text = raw_text.strip()
    if clean_text.startswith("```"):
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
        clean_text = re.sub(r"\s*```$", "", clean_text)
    clean_text = clean_text.strip()

    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError as exc:
        # Fallback regex extraction of outermost JSON object
        match = re.search(r"(\{.*\})", clean_text, flags=re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            raise ValueError(f"Could not parse valid JSON from model response: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in model response, got {type(data).__name__}")

    # Normalize fields according to output contract
    data.setdefault("overall_verdict", "REVIEW")
    if data["overall_verdict"] not in ("PASS", "FAIL", "REVIEW"):
        data["overall_verdict"] = "REVIEW"

    data.setdefault("interactions", [])
    data.setdefault("defects", [])
    data.setdefault("healthy_sections", [])
    data.setdefault("manual_rechecks", [])

    return data


# ---------------------------------------------------------------------------
# Mock fixture generator (offline test / CI support)
# ---------------------------------------------------------------------------

def generate_mock_report(
    video_path: Path,
    profile_name: str,
    model: str,
    processing_mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate deterministic mock output and raw response for offline testing."""
    mock_payload = {
        "overall_verdict": "FAIL" if profile_name == "overworld-ui" else "PASS",
        "interactions": [
            {
                "timestamp": "00:18.400",
                "control": "Compendium",
                "expected": "Compendium screen opens once",
                "observed": "Compendium panel appears",
                "verdict": "PASS",
                "confidence": 0.96,
                "evidence_type": "visual_observation",
            },
            {
                "timestamp": "00:25.100",
                "control": "BowHUD Reticle",
                "expected": "Reticle opacity drops to 32% during idle exploration",
                "observed": "Reticle dims to expected idle opacity",
                "verdict": "PASS",
                "confidence": 0.94,
                "evidence_type": "visual_observation",
            },
        ],
        "defects": (
            [
                {
                    "timestamp": "00:42.100",
                    "severity": "high",
                    "category": "input_focus",
                    "observation": "Cursor remains visible after menu closes",
                    "expected": "Cursor hidden when gameplay control returns",
                    "confidence": 0.91,
                    "evidence_type": "visual_observation",
                    "recommended_recheck": "Inspect 00:40-00:45",
                }
            ]
            if profile_name == "overworld-ui"
            else []
        ),
        "healthy_sections": [
            {
                "start_timestamp": "00:00.000",
                "end_timestamp": "00:15.200",
                "feature": "Overworld HUD Idle",
                "observation": "HUD elements steady, no flickering or overlap",
            }
        ],
        "manual_rechecks": [
            {
                "timestamp": "00:42.100",
                "reason": "Uncertain if cursor visible was OS cursor or in-game hardware cursor",
                "context": "Post-menu close transition",
            }
        ],
    }

    mock_steps = [
        {"type": "user_input", "content": [{"type": "text", "text": "Analyze UI video"}]},
        {"type": "processing_call", "id": "proc_call_001"},
        {"type": "processing_result", "call_id": "proc_call_001"},
        {"type": "model_output", "content": [{"type": "text", "text": json.dumps(mock_payload)}]},
    ]

    mock_raw = {
        "id": "mock-interaction-001",
        "model": model,
        "status": "completed",
        "steps": mock_steps,
        "output_text": json.dumps(mock_payload),
        "usage": {
            "prompt_tokens": 1420,
            "candidates_tokens": 580,
            "total_tokens": 2000,
        },
    }

    return mock_payload, mock_raw


# ---------------------------------------------------------------------------
# Core Bridge Runner
# ---------------------------------------------------------------------------

def run_video_qa(
    video_path: str | Path,
    profile: str = "overworld-ui",
    out_path: str | Path | None = None,
    model: str = DEFAULT_MODEL,
    processing_mode: str = "agentic",
    custom_prompt: str | None = None,
    save_raw: bool | str = False,
    timeout: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    mock: bool = False,
) -> dict[str, Any]:
    """Execute video QA analysis and produce deterministic JSON report conforming to contract."""
    start_ts = datetime.now(timezone.utc)
    v_path = Path(video_path).resolve()
    if not v_path.is_file():
        raise FileNotFoundError(f"Target video does not exist: {v_path}")

    sha256_hash, size_bytes = compute_file_hash_and_size(v_path)
    profile_info = PROFILES.get(profile, PROFILES["custom"])
    effective_processing = processing_mode if processing_mode in ("agentic", "static") else profile_info["default_processing"]

    raw_response_path: str | None = None
    if save_raw:
        if isinstance(save_raw, str):
            raw_response_path = save_raw
        elif out_path:
            p = Path(out_path)
            raw_response_path = str(p.parent / f"{p.stem}_raw.json")
        else:
            raw_response_path = f"Saved/Audit/VideoQA/{v_path.stem}_raw.json"

    # Execution flow: Mock vs Real
    if mock:
        parsed_body, raw_response = generate_mock_report(v_path, profile, model, effective_processing)
        verified_agentic, processing_steps = verify_agentic_processing(raw_response.get("steps", []))
        duration = 0.5
        usage_info = raw_response.get("usage", {})
        file_uri = f"mock://files/{v_path.stem}"
    else:
        if genai is None:
            raise RuntimeError(
                "The 'google-genai' package is required but not installed. Run: pip install google-genai"
            )

        api_key = get_api_key(strict=True)
        client = genai.Client(api_key=api_key, http_options={"timeout": 180.0})

        # 1. Upload video and poll until active
        file_obj = upload_and_poll_video(client, v_path, poll_interval=poll_interval, timeout=timeout)
        file_uri = getattr(file_obj, "uri", "")

        # 2. Build system instruction and user prompt
        system_instruction = profile_info["system_instruction"]
        user_prompt_text = (
            f"Analyze this Unreal Engine 5 gameplay capture video for profile '{profile}'.\n"
            f"Video file: {v_path.name} (SHA-256: {sha256_hash}, Size: {size_bytes} bytes).\n"
        )
        if custom_prompt:
            user_prompt_text += f"\nAdditional Instructions:\n{custom_prompt}\n"
        user_prompt_text += "\nOutput your evaluation as a valid JSON object matching the requested schema."

        # 3. Construct input content blocks
        interaction_input = [
            {
                "type": "video",
                "uri": file_uri,
                "mime_type": getattr(file_obj, "mime_type", "video/mp4") or "video/mp4",
                "processing": effective_processing,
            },
            {
                "type": "text",
                "text": user_prompt_text,
            },
        ]

        # 4. Call interactions.create with agentic video processing
        sys.stderr.write(
            f"Sending interaction request to Gemini (model: {model}, processing: {effective_processing})...\n"
        )
        max_attempts = 4
        interaction = None
        for attempt in range(1, max_attempts + 1):
            try:
                interaction = client.interactions.create(
                    model=model,
                    input=interaction_input,
                    system_instruction=system_instruction,
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": STRUCTURED_OUTPUT_SCHEMA,
                    },
                )
                break
            except Exception as exc:
                err_msg = sanitize_secret(str(exc))
                is_hard_quota = any(
                    term in err_msg.lower()
                    for term in ("per day", "daily", "upgrade your tier", "retry in ")
                )
                is_transient = (not is_hard_quota) and any(
                    code in err_msg
                    for code in ("503", "429", "500", "502", "504", "high demand", "rate limit", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
                )
                if is_transient and attempt < max_attempts:
                    backoff = attempt * 8.0
                    sys.stderr.write(
                        f"Transient error from Gemini ({err_msg}). Retrying in {backoff:.1f}s (attempt {attempt}/{max_attempts})...\n"
                    )
                    sys.stderr.flush()
                    time.sleep(backoff)
                else:
                    raise RuntimeError(f"Gemini interaction request failed: {err_msg}") from exc

        # 5. Extract output and verify dynamic inspection
        raw_output_text = getattr(interaction, "output_text", "")
        if not raw_output_text:
            raise ValueError("Interaction returned empty output_text from model.")

        parsed_body = parse_interaction_output(raw_output_text)
        interaction_steps = getattr(interaction, "steps", []) or []
        verified_agentic, processing_steps = verify_agentic_processing(interaction_steps)

        # Serialize raw interaction for auditing
        raw_response = {}
        if hasattr(interaction, "model_dump"):
            try:
                raw_response = interaction.model_dump()
            except Exception:
                raw_response = {"output_text": raw_output_text}
        else:
            raw_response = {"output_text": raw_output_text}

        duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
        usage_obj = getattr(interaction, "usage", None)
        usage_info = {}
        if usage_obj:
            p_tok = getattr(usage_obj, "prompt_tokens", None) or getattr(usage_obj, "total_input_tokens", None)
            c_tok = getattr(usage_obj, "candidates_tokens", None) or getattr(usage_obj, "total_output_tokens", None)
            tot_tok = getattr(usage_obj, "total_tokens", None)
            usage_info = {
                "prompt_tokens": p_tok,
                "candidates_tokens": c_tok,
                "total_tokens": tot_tok,
            }

    # If requested mode was agentic, verified flag reflects actual dynamic inspection steps
    if effective_processing == "agentic":
        processing_mode_verified = verified_agentic
    else:
        processing_mode_verified = True

    # Assemble base shape strictly per Output Contract
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "video": {
            "path": str(video_path),
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
        },
        "model": model,
        "processing_mode_requested": effective_processing,
        "processing_mode_verified": processing_mode_verified,
        "overall_verdict": parsed_body.get("overall_verdict", "REVIEW"),
        "interactions": parsed_body.get("interactions", []),
        "defects": parsed_body.get("defects", []),
        "healthy_sections": parsed_body.get("healthy_sections", []),
        "manual_rechecks": parsed_body.get("manual_rechecks", []),
        "raw_response_path": raw_response_path,
        "execution_metadata": {
            "started_at": start_ts.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 3),
            "file_uri": file_uri,
            "processing_steps_found": len(processing_steps),
            "processing_steps": processing_steps,
            "token_usage": usage_info,
        },
    }

    # Save raw response if requested
    if raw_response_path:
        raw_p = Path(raw_response_path)
        raw_p.parent.mkdir(parents=True, exist_ok=True)
        with raw_p.open("w", encoding="utf-8") as f:
            json.dump(raw_response, f, indent=2, default=str)
        sys.stderr.write(f"Raw interaction saved to: {raw_response_path}\n")

    # Save final report to output path if specified
    if out_path:
        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        sys.stderr.write(f"QA Report written to: {out_p}\n")

    return report


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Melodia Video-QA Bridge -- Gemini video understanding for Unreal PIE captures.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to local video capture file (.mp4, .mov, etc.)",
    )
    parser.add_argument(
        "--profile",
        default="overworld-ui",
        choices=list(PROFILES.keys()),
        help="QA profile to evaluate (default: overworld-ui)",
    )
    parser.add_argument(
        "--out",
        help="Path to write the structured JSON output report",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model override (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--processing-mode",
        choices=["agentic", "static", "auto"],
        default="agentic",
        help="Processing mode override (default: agentic)",
    )
    parser.add_argument(
        "--prompt",
        help="Optional custom instructions or criteria extension",
    )
    parser.add_argument(
        "--save-raw",
        nargs="?",
        const=True,
        default=False,
        help="Save raw Gemini interaction response to path or sidecar file",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds for upload and processing (default: {DEFAULT_TIMEOUT}s)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL}s)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline mock mode for testing and CI validation",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        report = run_video_qa(
            video_path=args.video,
            profile=args.profile,
            out_path=args.out,
            model=args.model,
            processing_mode=args.processing_mode,
            custom_prompt=args.prompt,
            save_raw=args.save_raw,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            mock=args.mock,
        )
    except FileNotFoundError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)
    except (ValueError, TypeError) as exc:
        sys.stderr.write(f"Configuration Error: {exc}\n")
        sys.exit(1)
    except TimeoutError as exc:
        sys.stderr.write(f"Timeout Error: {exc}\n")
        sys.exit(2)
    except Exception as exc:
        sys.stderr.write(f"Execution Error: {sanitize_secret(str(exc))}\n")
        sys.exit(2)

    # If --out was not passed, emit JSON directly to stdout
    if not args.out:
        print(json.dumps(report, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
