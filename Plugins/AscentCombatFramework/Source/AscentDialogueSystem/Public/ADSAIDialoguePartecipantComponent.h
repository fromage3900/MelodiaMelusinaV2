// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Graph/ADSDialogue.h"
#include "ADSBaseDialoguePartecipantComponent.h"
#include "CineCameraActor.h"
#include "Engine/TargetPoint.h"
#include "Components/SceneComponent.h"
#include "Engine/Engine.h"
#include "Interfaces/IHttpRequest.h"
#include "ADSAIDialoguePartecipantComponent.generated.h"

class USkeletalMeshComponent;
class UADSDialogue;
class UADSDialogueDeveloperSettings;

// Structured conversation entry for better history management
USTRUCT(BlueprintType)
struct ASCENTDIALOGUESYSTEM_API FADSConversationEntry
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Conversation")
    FString Speaker;

    UPROPERTY(BlueprintReadOnly, Category = "Conversation")
    FString Message;

    UPROPERTY(BlueprintReadOnly, Category = "Conversation")
    FDateTime Timestamp;

    FADSConversationEntry()
    {
        Speaker = TEXT("");
        Message = TEXT("");
        Timestamp = FDateTime::Now();
    }

    FADSConversationEntry(const FString& InSpeaker, const FString& InMessage)
    {
        Speaker = InSpeaker;
        Message = InMessage;
        Timestamp = FDateTime::Now();
    }
};

// Enum for AI dialog state
UENUM(BlueprintType)
enum class EAIDialogueState : uint8
{
    Idle        UMETA(DisplayName = "Idle"),
    Processing  UMETA(DisplayName = "Processing"),
    WaitingForResponse UMETA(DisplayName = "Waiting For Response"),
    Completed   UMETA(DisplayName = "Completed"),
    Error       UMETA(DisplayName = "Error")
};

// Delegate for AI response events
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnAIResponseReceived, FString, Response, bool, bSuccess, bool, bIsFirstResponse);

// Delegate for AI dialog state
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAIDialogueStateChanged, EAIDialogueState, NewState);

// Delegate for conversation progress (continuing an existing conversation)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnConversationProgress, FString, PlayerMessage, int32, MessageCount);

UCLASS(Blueprintable, ClassGroup = (ATS), meta = (BlueprintSpawnableComponent))
class ASCENTDIALOGUESYSTEM_API UADSAIDialoguePartecipantComponent : public UADSBaseDialoguePartecipantComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UADSAIDialoguePartecipantComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    // Called when the game ends
    virtual void EndPlay(EEndPlayReason::Type reason) override;

public:
    // === BLUEPRINT AI DIALOGUE FUNCTIONS ===
    
    // Starts an AI dialogue with the given player message (Blueprint safe version)
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    bool StartAIDialogue(const FString& PlayerMessage);

    // Progresses an ongoing AI dialogue with a new player message (for continuing conversations)
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    bool ProgressAIDialogue(const FString& PlayerMessage);

    // Checks if the AI dialogue is currently busy (processing or waiting for response)
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    bool IsAIDialogueBusy() const;

    // Gets the current state of the AI dialogue
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    EAIDialogueState GetAIDialogueState() const { return CurrentDialogueState; }

    // Resets the AI dialogue state to Idle (use in case of errors)
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void ResetAIDialogueState();

    // Resets the first response flag (useful when starting a new conversation from Blueprint)
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void ResetFirstResponseFlag();

    // Checks if the next response will be the first response of a new conversation
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    bool IsNextResponseFirst() const { return bIsFirstResponse; }

    // Gets the last AI response received
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetLastAIResponse() const { return LastAIResponse; }

    // Gets the last error message (if any)
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetLastErrorMessage() const { return LastErrorMessage; }

    // Event triggered when AI response is received
    UPROPERTY(BlueprintAssignable, Category = "ADS|AI")
    FOnAIResponseReceived OnAIResponseReceived;

    // Event triggered when AI dialogue state changes
    UPROPERTY(BlueprintAssignable, Category = "ADS|AI")
    FOnAIDialogueStateChanged OnAIDialogueStateChanged;

    // Event triggered when conversation progresses (for continuing conversations)
    UPROPERTY(BlueprintAssignable, Category = "ADS|AI")
    FOnConversationProgress OnConversationProgress;

    // Attempts to start a dialogue given an array of dialogue participant components and a dialogue object
    virtual bool TryStartDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSDialogue* dialogueToStart) override;

    // Attempts to start a dialogue using actors instead of participant components
    virtual bool TryStartDialogueFromActors(const TArray<AActor*>& participants, UADSDialogue* dialogueToStart) override;

    // Returns the name of the participant (override to use base properties with AI logging)
    FText GetParticipantName() const override {
        UE_LOG(LogTemp, Log, TEXT("AI GetParticipantName called for %s, returning: %s"), 
            GetOwner() ? *GetOwner()->GetName() : TEXT("NULL"), 
            *ParticipantNameText.ToString());
        if (ParticipantNameText.IsEmpty()) {
            UE_LOG(LogTemp, Error, TEXT("AI ParticipantNameText is empty for %s!"), *GetOwner()->GetName());
            return FText::FromString(TEXT("AI NPC"));
        }
        return ParticipantNameText;
    }

    // Returns the tag associated with the participant (override to use base properties)
    FGameplayTag GetParticipantTag() const override { return PartecipantTag; }

    // Retrieves a dialogue by tag, setting bFound to true if found (AI version always returns false)
    virtual UADSDialogue* GetDialogue(FGameplayTag dialogueTag, bool& bFound) const override;

    // Retrieves the skeletal mesh component of the owner
    UFUNCTION(BlueprintPure, Category = ADS)
    USkeletalMeshComponent* GetOwnerMesh();

    // Retrieves the skeletal mesh component used for facial animations
    UFUNCTION(BlueprintPure, Category = ADS)
    USkeletalMeshComponent* GetFacialAnimationMesh();

    // Sets the skeletal mesh for the participant
    UFUNCTION(BlueprintCallable, Category = ADS)
    void SetParticipantSkeletalMesh(class USkeletalMeshComponent* mesh)
    {
        skeletalMesh = mesh;
    }

    // Plays an animation montage on the character that owns this participant
    UFUNCTION(BlueprintCallable, Category = ADS)
    virtual void PlayAnimationOnCharacterOwner(UAnimMontage* animation);

    // Plays a facial animation montage on the character that owns this participant
    UFUNCTION(BlueprintCallable, Category = ADS)
    virtual void PlayFacialAnimationOnCharacterOwner(UAnimMontage* animation);

    // Stops a facial animation montage on the character that owns this participant
    UFUNCTION(BlueprintCallable, Category = ADS)
    virtual void StopFacialAnimationOnCharacterOwner(UAnimMontage* animation);

    // Stops an animation montage on the character that owns this participant
    UFUNCTION(BlueprintCallable, Category = ADS)
    virtual void StopAnimationOnCharacterOwner(UAnimMontage* animation);

    // Returns the name of the participant (interactable name)
    FText GetInteractableName() const override {
        FText name = GetParticipantName();
        UE_LOG(LogTemp, Log, TEXT("AI GetInteractableName called for %s, returning: %s"), 
            GetOwner() ? *GetOwner()->GetName() : TEXT("NULL"), 
            *name.ToString());
        if (name.IsEmpty() || name.ToString().Equals(TEXT("Unknown"))) {
            UE_LOG(LogTemp, Error, TEXT("AI Interactable name is unknown for %s!"), *GetOwner()->GetName());
        }
        return name;
    }

    // Sets the AI personality description for API calls
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void SetAIPersonality(const FString& personality) { AIPersonality = personality; }

    // Gets the AI personality description
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAIPersonality() const { return AIPersonality; }

    // Gets the AI character description
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAICharacterDescription() const { return AICharacterDescription; }

    // Gets the AI character rules and behavioral guidelines
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAICharacterRules() const { return AICharacterRules; }

    // Sets the AI character description
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void SetAICharacterDescription(const FString& description) { AICharacterDescription = description; }

    // Sets the AI character rules and behavioral guidelines
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void SetAICharacterRules(const FString& rules) { AICharacterRules = rules; }

    // Gets the API key from global settings
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAPIKey() const;

    // Gets the API endpoint from global settings (can be overridden locally)
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAPIEndpoint() const;

    // Gets the AI model from settings with local override support
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetAIModel() const;

    // Gets the max tokens from settings with local override support
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    int32 GetMaxTokens() const;

    // Checks if AI dialogue is enabled globally
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    bool IsAIDialogueEnabled() const;

    // Generates an AI response based on conversation context
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void GenerateAIResponse(const FString& PlayerInput, const FString& Context = "");

    // Ends the AI dialogue manually (callable from widgets)
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void EndAIDialogue();

    // Gets the conversation history as a JSON formatted string
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetConversationHistoryAsJSON() const;

    // Gets the conversation history as a simple text format
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    FString GetConversationHistoryAsText() const;

    // Gets the conversation history as an array of entries (Blueprint accessible)
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    TArray<FADSConversationEntry> GetConversationHistory() const { return StructuredConversationHistory; }

    // Gets the number of conversation exchanges (pairs of player/AI messages)
    UFUNCTION(BlueprintPure, Category = "ADS|AI")
    int32 GetConversationExchangeCount() const;

    // Clears the conversation history
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void ClearConversationHistory();

    // Sets the maximum conversation history size
    UFUNCTION(BlueprintCallable, Category = "ADS|AI")
    void SetMaxConversationHistory(int32 NewMaxHistory);

protected:
     
    // BlendoutTime for stopped animations
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ADS)
    float AnimationBlendoutTime = .2f;

    // Skeletal mesh for the participant
    TObjectPtr<USkeletalMeshComponent> skeletalMesh;

    // Facial skeletal mesh for the participant
    TObjectPtr<USkeletalMeshComponent> facialMesh;

    // AI personality description for API calls (local override)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI")
    FString AIPersonality = "Friendly NPC";

    // Detailed description of the AI character for context generation
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (MultiLine = true))
    FString AICharacterDescription = "A helpful NPC character who provides assistance to players.";

    // Character background rules and behavioral guidelines for the AI to follow during conversations
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (MultiLine = true))
    FString AICharacterRules = "- Always stay in character\n- Be helpful and courteous\n- Respond based on your role and knowledge\n- Keep responses concise and relevant\n- Never use Emoji\n- Never break the fourth wall";

    // Local override for API endpoint (if empty, uses global settings)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI")
    FString LocalAPIEndpoint;

    // Local override for AI model (if empty, uses global settings)  
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI")
    FString LocalAIModel;

    // Local override for max tokens (if 0, uses global settings)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (ClampMin = "0", ClampMax = "4096"))
    int32 LocalMaxTokens = 0;

    // Local override for payload template (if empty, uses global settings)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (MultiLine = true))
    FString LocalPayloadTemplate;

    // Local override for headers template (if empty, uses global settings)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (MultiLine = true))
    FString LocalHeadersTemplate;

    // Maximum number of conversation exchanges to keep in memory
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ADS|AI", meta = (ClampMin = "1", ClampMax = "50"))
    int32 MaxConversationHistory = 10;

    // Structured conversation history using the new format
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS|AI", meta = (AllowPrivateAccess = "true"))
    TArray<FADSConversationEntry> StructuredConversationHistory;

private:
    // === AI STATE MANAGEMENT ===
    
    // Current state of the AI dialogue
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS|AI", meta = (AllowPrivateAccess = "true"))
    EAIDialogueState CurrentDialogueState = EAIDialogueState::Idle;

    // Last AI response received
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS|AI", meta = (AllowPrivateAccess = "true"))
    FString LastAIResponse;

    // Last error message
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS|AI", meta = (AllowPrivateAccess = "true"))
    FString LastErrorMessage;

    // Tracks if the next response will be the first response of a new conversation
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS|AI", meta = (AllowPrivateAccess = "true"))
    bool bIsFirstResponse = true;

    // === PRIVATE FUNCTIONS ===

    // Sets the AI dialogue state and broadcasts the change
    void SetAIDialogueState(EAIDialogueState NewState);

    // HTTP response handler for AI API calls
    void OnHTTPResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    // Handles dialogue started events
    UFUNCTION()
    void HandleDialogueStarted();

    // Handles dialogue ended events
    UFUNCTION()
    void HandleDialogueEnded();

    // Gets the developer settings instance
    UADSDialogueDeveloperSettings* GetDialogueSettings() const;

    // Conversation history for AI context management (legacy)
    TArray<FString> ConversationHistory;

    // Adds an entry to the structured conversation history
    void AddToConversationHistory(const FString& Speaker, const FString& Message);

    // Maintains the conversation history size within limits
    void TrimConversationHistory();
};