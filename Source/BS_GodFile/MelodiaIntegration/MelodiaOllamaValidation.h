#pragma once

#include "CoreMinimal.h"

/**
 * Async, non-reflected Ollama validation helper (unwired as of 2026-07-31).
 *
 * Replaces the blocking `_popen` probe in MelodiaNarrativeSubsystem.cpp
 * (`SendToOllama`). This file is deliberately plain C++ -- no UCLASS/USTRUCT/
 * UPROPERTY/UFUNCTION -- so it carries none of the reflected-surface burden
 * that Live Coding cannot bake. It has no call sites yet; wiring it in is a
 * one-call change in MelodiaNarrativeSubsystem::HandleQuillNotification, to be
 * done in the next closed-editor window (see
 * Docs/Handoffs/CLAUDE_COORDINATION_NOTE_2026-07-31.md).
 *
 * Behaviour contract (mirrors the _popen probe):
 *  - POST to http://127.0.0.1:11434/api/generate (local Ollama daemon).
 *  - Prompt asks the model to answer 'valid' or 'invalid' for the intent.
 *  - bValid is true iff the reply contains 'valid' (case-insensitive), false
 *    on any transport error or empty reply -- same semantics as the probe.
 *  - Fire-and-forget: the request is owned by the callback via TSharedPtr, so
 *    nothing needs to be ticked or cleaned up by the caller.
 */
namespace MelodiaOllamaValidation
{
	/** Runs the validation on a background thread; never blocks the game thread. */
	void ValidateMessageAsync(const FString& Message, TFunction<void(bool bValid, const FString& RawReply)> OnComplete);
}
