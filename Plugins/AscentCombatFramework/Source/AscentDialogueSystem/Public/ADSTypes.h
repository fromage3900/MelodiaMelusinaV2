// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ADSCameraConfigDataAsset.h"
#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include <Engine/DataTable.h>

#include "ADSTypes.generated.h"

class UADSCameraConfigDataAsset;
class ULevelSequence;
class ACineCameraActor;

/**
 *
 */


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueEnded, UADSDialogue*, dialogue);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueStarted, UADSDialogue*, dialogue);

UENUM(BlueprintType)
enum class EDialogueCinematicType : uint8 {
	None, // No cinematic
	CameraConfig, // Procedural system with shot asset
	Sequencer, // Level Sequence
	CameraActor
};

UENUM(BlueprintType)
enum class EDialogueNodeDurationType : uint8
{
	// Automatically calculate duration from audio length
	Auto UMETA(DisplayName = "Auto (From Audio)"),

	// Use custom duration value in seconds
	Custom UMETA(DisplayName = "Custom Duration"),

	// Calculate based on text length (reading speed)
	TextBased UMETA(DisplayName = "Text-Based (Reading Speed)")
};

/** Controls the NODE TYPE used for player lines in AI-generated dialogue.
 *  Branching (multiple options) is NEVER invented by the AI in any mode —
 *  it only happens when the developer explicitly describes a player choice in
 *  the AI Conversation Description. */
UENUM(BlueprintType)
enum class EADSAIPlayerResponseMode : uint8
{
    /** Every player line is a button-answer node (Option format).
     *  1 button per beat by default; multiple buttons only if the description
     *  explicitly says the player can choose between alternatives. */
    OptionButtons UMETA(DisplayName = "Player Answers (button nodes)"),

    /** Every player line is a normal dialogue node (no button answers ever). */
    DialogueNodes UMETA(DisplayName = "Player Nodes (dialogue nodes)"),

    /** AI picks button-answer or dialogue node per beat based on context.
     *  Branching still only when explicitly described. */
    Mixed UMETA(DisplayName = "Mixed (AI picks node type per beat)"),
};

/** Mood expression for MetaHuman facial animation generation.
 *  Converted to the editor-only EAudioDrivenAnimationMood in the editor subsystem. */
UENUM(BlueprintType)
enum class EADSFacialAnimMood : uint8
{
	AutoDetect = 255 UMETA(DisplayName = "Auto Detect"),
	Neutral = 0 UMETA(DisplayName = "Neutral"),
	Happiness = 1 UMETA(DisplayName = "Happy"),
	Sadness = 2 UMETA(DisplayName = "Sad"),
	Disgust = 3 UMETA(DisplayName = "Disgust"),
	Anger = 4 UMETA(DisplayName = "Anger"),
	Surprise = 5 UMETA(DisplayName = "Surprise"),
	Fear = 6 UMETA(DisplayName = "Fear"),
	Confidence = 10 UMETA(DisplayName = "Confident"),
	Excitement = 14 UMETA(DisplayName = "Excited"),
	Boredom = 15 UMETA(DisplayName = "Bored"),
	Playfulness = 17 UMETA(DisplayName = "Playful"),
	Confusion = 19 UMETA(DisplayName = "Confused"),
};

USTRUCT(BlueprintType)
struct FDialogueCinematic {
	GENERATED_BODY()

public:
	FDialogueCinematic()
	{
		CameraConfig = nullptr;
		LevelSequence = nullptr;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	EDialogueCinematicType CinematicType = EDialogueCinematicType::None; // None = use participant default

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF", meta = (EditCondition = "CinematicType == EDialogueCinematicType::CameraConfig"))
	UADSCameraConfigDataAsset* CameraConfig;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF", meta = (EditCondition = "CinematicType == EDialogueCinematicType::Sequencer"))
	ULevelSequence* LevelSequence;

	UPROPERTY(EditAnywhere, Category = "ACF", meta = (EditCondition = "CinematicType == EDialogueCinematicType::CameraActor"))
	TSoftObjectPtr<ACineCameraActor> CameraActor;

	// The time taken to blend smoothly between camera transitions during dialogue
	UPROPERTY(EditAnywhere, Category = "ACF", meta = (EditCondition = "CinematicType == EDialogueCinematicType::CameraActor"))
	float BlendTime = 0.02f;
};

/**
 * Cache used to store voices retrieved from TTS API.
 * Accessible globally via the Dialogue Subsystem.
 */
USTRUCT()
struct FADSVoiceSettings : public FTableRowBase {
	GENERATED_BODY()

public:
	FADSVoiceSettings() {};



	/** Voice display name selected from the available ElevenLabs voices */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS", meta = (GetOptions = "GetAvailableVoiceNames"))
	FString SelectedVoiceName = "James - Professional British Male";

	/** Voice ID automatically retrieved from the ElevenLabs service for the selected voice */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS")
	FString VoiceID = "lUTamkMw7gOzZbFIwmq4";

	/** Optional manual override of the Voice ID */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS")
	FString ManualVoiceID;

	/** Free-form description of this character's personality, used as context when
	 *  generating an entire dialogue with AI (e.g. "Gruff, battle-worn mercenary who distrusts strangers"). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS", meta = (MultiLine = true))
	FString Personality;

	TArray<FString> GetAvailableVoiceNames() const;

	FString GetSelectedVoiceID() const
	{
		return !ManualVoiceID.IsEmpty() ? ManualVoiceID : VoiceID;
	}
};

/**
 * Cache used to store voices retrieved from TTS API.
 * Accessible globally via the Dialogue Subsystem.
 */
USTRUCT()
struct FADSVoiceCache {
	GENERATED_BODY()

	/** Cached list of available voice display names */
	TArray<FString> VoiceNames;

	/** Mapping from voice display name to internal voice ID */
	TMap<FString, FString> VoiceNameToID;

	/** Last API key used for fetching voices */
	FString LastAPIKey;

	/** Time when the cache was last updated */
	FDateTime LastCacheTime = FDateTime::MinValue();

	/** Cache expiry threshold in hours */
	static constexpr double CACHE_EXPIRY_HOURS = 1.0;

	bool IsValid(const FString& CurrentAPIKey) const
	{
		return LastAPIKey == CurrentAPIKey && (FDateTime::Now() - LastCacheTime).GetTotalHours() < CACHE_EXPIRY_HOURS && VoiceNames.Num() > 0;
	}

	void Clear()
	{
		VoiceNames.Empty();
		VoiceNameToID.Empty();
		LastAPIKey.Empty();
		LastCacheTime = FDateTime::MinValue();
	}

	void Update(const TArray<FString>& NewVoiceNames, const TMap<FString, FString>& NewVoiceNameToID, const FString& APIKey)
	{
		VoiceNames = NewVoiceNames;
		VoiceNameToID = NewVoiceNameToID;
		LastAPIKey = APIKey;
		LastCacheTime = FDateTime::Now();
	}
};

UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSTypes : public UObject {
	GENERATED_BODY()
};
