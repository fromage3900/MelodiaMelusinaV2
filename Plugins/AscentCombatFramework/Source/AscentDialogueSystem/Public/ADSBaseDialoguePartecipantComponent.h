// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/TargetPoint.h"
#include "GameplayTagContainer.h"
#include <Components/SceneComponent.h>
#include "ADSTypes.h"

#include "ADSBaseDialoguePartecipantComponent.generated.h"

class UADSDialogue;
class ACineCameraActor;
class UCineCameraComponent;


/**
 * Base class for dialogue participant components in Ascent Dialogue System.
 * Provides common interface for all participant types.
 */
UCLASS(Blueprintable, ClassGroup = (ATS), meta = (BlueprintSpawnableComponent))
class ASCENTDIALOGUESYSTEM_API UADSBaseDialoguePartecipantComponent : public USceneComponent {
	GENERATED_BODY()
public:
	UADSBaseDialoguePartecipantComponent();

	// Virtual methods for dialogue start
	UFUNCTION(BlueprintCallable, Category = ADS)
	virtual bool TryStartDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSDialogue* dialogueToStart);

	UFUNCTION(BlueprintCallable, Category = ADS)
	virtual bool TryStartDialogueFromActors(const TArray<AActor*>& participants, UADSDialogue* dialogueToStart);

	// Retrieves a dialogue by tag, setting bFound to true if found
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual UADSDialogue* GetDialogue(FGameplayTag dialogueTag, bool& bFound) const;

	// Event triggered when a dialogue starts
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueStarted OnDialogueStarted;

	// Event triggered when a dialogue ends
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueEnded OnDialogueEnded;

	// Event called when a dialogue starts
	UFUNCTION(BlueprintNativeEvent, Category = ADS)
	void OnDialogueStartedEvent();

	// Event called when a dialogue ends.
	UFUNCTION(BlueprintNativeEvent, Category = ADS)
	void OnDialogueEndedEvent();

	// Gets the participant tag
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual FGameplayTag GetParticipantTag() const
	{
		return PartecipantTag;
	}

	// Gets the interactable name
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual FText GetInteractableName() const
	{
		return ParticipantNameText.IsEmpty() ? FText::FromString(TEXT("Unknown")) : ParticipantNameText;
	}

	// Gets the participant name
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual FText GetParticipantName() const
	{
		return ParticipantNameText.IsEmpty() ? FText::FromString(TEXT("Unknown")) : ParticipantNameText;
	}

	// Returns the icon associated with the participant
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual UTexture2D* GetParticipantIcon() const
	{
		return PartecipantIcon;
	}

	// Returns the socket name where the participant's voice is spawned
	UFUNCTION(BlueprintPure, Category = ADS)
	virtual FName GetVoiceSpawningSocketName() const
	{
		return VoiceSpawningSocketName;
	}

	// Returns the default camera actor as a hard reference
	UFUNCTION(BlueprintPure, Category = "ADS|Camera")
	UADSCameraConfigDataAsset* GetDefaultCameraAsset() const;

	// Getter for DefaultEnforcedPlayerPosition that converts soft reference to hard reference
	UFUNCTION(BlueprintPure, Category = "ADS|Camera")
	FVector GetDefaultEnforcedPlayerPosition() const
	{
		return DefaultEnforcedPlayerPosition;
	}

	// Changes the participant's icon
	UFUNCTION(BlueprintCallable, Category = ADS)
	virtual void ChangeParticipantIcon(class UTexture2D* icon)
	{
		PartecipantIcon = icon;
	}

	// Changes the participant's name
	UFUNCTION(BlueprintCallable, Category = ADS)
	virtual void SetParticipantName(const FText& newName)
	{
		ParticipantNameText = newName;
	}

	// Changes the participant's name
	UFUNCTION(BlueprintCallable, Category = ADS)
	virtual void SetParticipantTag(const FGameplayTag& newTag)
	{
		PartecipantTag = newTag;
	}

	// Blueprint helper function to get dialogue participant component with proper casting
	UFUNCTION(BlueprintCallable, Category = ADS)
	static class UADSBaseDialoguePartecipantComponent* GetDialogueComponentFromActor(AActor* InActor);

	UFUNCTION(BlueprintCallable, Category = ADS)
	void SetCamera(const FDialogueCinematic& CameraSettings);

	UFUNCTION(BlueprintCallable, Category = ADS)
	void SetDefaultCameraAndPosition();

	UFUNCTION(BlueprintCallable, Category = ADS)
	void SetPosition(const FVector& EnforcedPlayerPosition);

	UFUNCTION(BlueprintPure, Category = ADS)
	UADSCameraConfigDataAsset* GetDefaultCameraConfig() const { return DefaultCameraConfig; }

	UFUNCTION(BlueprintCallable, Category = ADS)
	void SetDefaultCameraConfig(UADSCameraConfigDataAsset* val) { DefaultCameraConfig = val; }

	UFUNCTION(BlueprintPure, Category = ADS)
	bool IsInDialogue() const { return bIsInDialogue; }

protected:

	UPROPERTY(BlueprintReadOnly, Replicated, Category = "ADS")
	bool bIsInDialogue = false;
	/** The unique name identifying this participant. */
	UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category = "ADS")
	FText ParticipantNameText;

	/** Gameplay tag used to group or identify this participant in dialogues. */
	UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, meta = (Categories = "Character"), Category = "ADS")
	FGameplayTag PartecipantTag;

	/** Icon representing this participant in dialogue UIs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS")
	class UTexture2D* PartecipantIcon;

	/** Socket name for voice or effect spawning during dialogues (e.g., 'head'). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS")
	FName VoiceSpawningSocketName = "head";

	// Tag for identifying the facial skeleton component
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS")
	FName FacialSkeletonComponentTag = "head";

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|Position")
	bool bShouldMovePlayer = false;

	/*If not specified in the dialogue start node, this position will be used to place the Player in a conversation
	with this character*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (MakeEditWidget), meta = (EditCondition = "bShouldMovePlayer"), Category = "ADS|Position")
	FVector DefaultEnforcedPlayerPosition;

	// If not specified in the dialogue node, the camera used to frame the speaking character during dialogue
	// All the options in the current dialogue node will override this
	UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category = "ADS|Camera")
	UADSCameraConfigDataAsset* DefaultCameraConfig;


	void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const;

};