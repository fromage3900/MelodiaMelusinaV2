// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Graph/ADSDialogueNode.h"
#include "Graph/ADSDialogueResponseNode.h"
#include <GameFramework/PlayerController.h>
#include "Graph/ADSGraphEdge.h"
#include "AGSGraphNode.h"
#include <CineCameraActor.h>
#include "AGSCondition.h"
#include "ADSDialoguePartecipantComponent.h"
#include <Sound/SoundBase.h>
#include <Engine/World.h>
#include <TimerManager.h>  


void UADSDialogueNode::ActivateNode()
{
	Super::ActivateNode();

	if (participant) {
		if (participant && controller && CameraSettings.CinematicType == EDialogueCinematicType::CameraActor && CameraSettings.CameraActor.Get()) {
			controller->SetViewTargetWithBlend(CameraSettings.CameraActor.Get(), CameraSettings.BlendTime);
		}
		else {
			participant->SetCamera(CameraSettings);
		}
	
		if (ShouldAutoProgress())
		{
			const float AudioDuration = CalculateNodeDuration();

			// Set timer to auto-progress when audio finishes
			participant->GetWorld()->GetTimerManager().SetTimer(
				AutoProgressTimerHandle,
				this,
				&UADSDialogueNode::OnAudioFinished,
				AudioDuration,
				false
			);
		}
	}
	else {

	}



}

bool UADSDialogueNode::ShouldAutoProgress()
{
	//we only auto proceed if there are no valid answers
	return bAutoProgressNode && GetAllValidAnswers(controller) == TArray<UADSDialogueResponseNode*>();
}

UADSDialogueNode::UADSDialogueNode()
{
#if WITH_EDITOR
	BackgroundColor = FLinearColor::Black;
	ContextMenuName = FText::FromString("Dialogue Node");
#endif
	bAutoProgressNode = true;
	DurationType = EDialogueNodeDurationType::Auto;
	CustomDuration = 2.0f;
	ReadingSpeed = 15.0f;

}

TArray<UADSDialogueResponseNode*>  UADSDialogueNode::GetAllValidAnswers(APlayerController* inController)
{
	TArray<UADSDialogueResponseNode*>  outResponses;
	for (UAGSGraphNode* child : ChildrenNodes)
	{
		UADSDialogueResponseNode* response = Cast<UADSDialogueResponseNode>(child);
		if (response && response->CanBeActivated(inController))
		{
			UADSGraphEdge* edge = Cast< UADSGraphEdge>(GetEdge(response));
			if (edge && edge->CanBeActivated(inController)) {
				outResponses.Add(response);
			}

		}
	}

	// Sort responses by their horizontal position in the graph so that the order
	// returned matches the left-to-right layout authored in the dialogue editor.
	outResponses.Sort([](const UADSDialogueResponseNode& A, const UADSDialogueResponseNode& B)
	{
		return A.GetNodePosition().X < B.GetNodePosition().X;
	});

	return outResponses;
}


bool UADSDialogueNode::CanBeActivated(APlayerController* inController)
{
	controller = inController;
	for (UAGSCondition* cond : ActivationConditions) {
		if (cond && !cond->VerifyForNode(inController, this))
			return false;
	}
	return true;
}

void UADSDialogueNode::DeactivateNode()
{
	if (AutoProgressTimerHandle.IsValid())
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().ClearTimer(AutoProgressTimerHandle);
		}
		AutoProgressTimerHandle.Invalidate();
	}

	Super::DeactivateNode();
}

float UADSDialogueNode::CalculateNodeDuration() const
{
	switch (DurationType)
	{
	case EDialogueNodeDurationType::Custom:
	{
		// Use custom duration directly
		return FMath::Max(CustomDuration, 0.1f);
	}

	case EDialogueNodeDurationType::Auto:
	{
		// Try to get audio duration first
		const float AudioDuration = GetAudioDuration();
		if (AudioDuration > 0.0f)
		{
			return AudioDuration;
		}

		// Fallback to text-based calculation if no audio
		const float TextDuration = GetTextBasedDuration();
		if (TextDuration > 0.0f)
		{
			return TextDuration;
		}

	}

	case EDialogueNodeDurationType::TextBased:
	{
		// Calculate based on text length
		const float TextDuration = GetTextBasedDuration();
		if (TextDuration > 0.0f)
		{
			return TextDuration;
		}
	}

	default:
	{
		return 5.f;
	}
	}
}

float UADSDialogueNode::GetTextBasedDuration() const
{
	// Get text length
	const FString TextString = Text.ToString();
	const int32 TextLength = TextString.Len();

	if (TextLength <= 0)
	{
		return 0.0f;
	}

	// Calculate duration based on reading speed (characters per second)
	// Add minimum of 1 second for very short texts
	const float CalculatedDuration = static_cast<float>(TextLength) / ReadingSpeed;
	return FMath::Max(CalculatedDuration, 1.0f);
}

float UADSDialogueNode::GetAudioDuration() const
{
	if (SoundToPlay) {
		return SoundToPlay->GetDuration() + .5f;
	}

	return 0.0f;
}

void UADSDialogueNode::OnAudioFinished()
{
	// Get the owning dialogue
	UADSDialogue* OwningDialogue = Cast<UADSDialogue>(GetGraph());
	if (!OwningDialogue) {
		return;
	}

	// Auto-progress to next node
	if (OwningDialogue->IsDialogueStarted()) {
		OwningDialogue->MoveToNextNode();

	}
}