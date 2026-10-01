// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSAIDialoguePartecipantComponent.h"
#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialogueMasterComponent.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Http.h"
#include "Json.h"
#include <Kismet/GameplayStatics.h>
#include <TimerManager.h>

// Constructor
UADSAIDialoguePartecipantComponent::UADSAIDialoguePartecipantComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    ParticipantNameText = FText::FromString("AI NPC");
    CurrentDialogueState = EAIDialogueState::Idle;
    bIsFirstResponse = true;
}

// BeginPlay
void UADSAIDialoguePartecipantComponent::BeginPlay()
{
    Super::BeginPlay();

    // Reset state at begin play
    SetAIDialogueState(EAIDialogueState::Idle);

    if (!IsAIDialogueEnabled()) {
        UE_LOG(LogTemp, Warning, TEXT("AI Dialogue is disabled in project settings"));
        return;
    }

    if (GetAPIKey().IsEmpty()) {
        UE_LOG(LogTemp, Error, TEXT("API Key is missing - please configure in project settings"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("AI Dialogue ready for interaction"));
}

// EndPlay
void UADSAIDialoguePartecipantComponent::EndPlay(EEndPlayReason::Type reason)
{
    Super::EndPlay(reason);
    ConversationHistory.Empty();
    StructuredConversationHistory.Empty();
    SetAIDialogueState(EAIDialogueState::Idle);
    bIsFirstResponse = true;
}

// === AI STATE MANAGEMENT ===
void UADSAIDialoguePartecipantComponent::SetAIDialogueState(EAIDialogueState NewState)
{
    if (CurrentDialogueState != NewState) {
        EAIDialogueState OldState = CurrentDialogueState;
        CurrentDialogueState = NewState;

        UE_LOG(LogTemp, Log, TEXT("AI Dialogue State changed from %d to %d"), (int32)OldState, (int32)NewState);

        // Broadcast state change
        OnAIDialogueStateChanged.Broadcast(NewState);

        // Clear error message when going back to Idle
        if (NewState == EAIDialogueState::Idle) {
            LastErrorMessage.Empty();
        }
    }
}

bool UADSAIDialoguePartecipantComponent::IsAIDialogueBusy() const
{
    return CurrentDialogueState == EAIDialogueState::Processing || CurrentDialogueState == EAIDialogueState::WaitingForResponse;
}

void UADSAIDialoguePartecipantComponent::ResetAIDialogueState()
{
    UE_LOG(LogTemp, Log, TEXT("Resetting AI Dialogue State to Idle"));
    SetAIDialogueState(EAIDialogueState::Idle);
    LastErrorMessage.Empty();
    bIsFirstResponse = true;
}

// Resets the first response flag
void UADSAIDialoguePartecipantComponent::ResetFirstResponseFlag()
{
    bIsFirstResponse = true;
    UE_LOG(LogTemp, Log, TEXT("First response flag reset - next response will be marked as first"));
}

// === MAIN AI DIALOGUE FUNCTION ===
bool UADSAIDialoguePartecipantComponent::StartAIDialogue(const FString& PlayerMessage)
{
    UE_LOG(LogTemp, Log, TEXT("StartAIDialogue called with message: %s"), *PlayerMessage);

    // Check if already busy
    if (IsAIDialogueBusy()) {
        FString ErrorMsg = "AI Dialogue is already processing a request. Please wait.";
        UE_LOG(LogTemp, Warning, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Check configuration
    if (!IsAIDialogueEnabled() || GetAPIKey().IsEmpty()) {
        FString ErrorMsg = "AI Dialogue not properly configured";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Validate input
    if (PlayerMessage.IsEmpty()) {
        FString ErrorMsg = "Player message cannot be empty";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Set state to processing
    SetAIDialogueState(EAIDialogueState::Processing);

    // Create rich context for the AI response
    const FString Context = FString::Printf(TEXT("Player said: '%s'"), *PlayerMessage);

    ConversationHistory.Empty();
    StructuredConversationHistory.Empty();
    bIsFirstResponse = true;
    OnDialogueStarted.Broadcast(nullptr);

    UE_LOG(LogTemp, Log, TEXT("Sending API request for AI response"));
    GenerateAIResponse(PlayerMessage, Context);

    // Set state to waiting for response
    SetAIDialogueState(EAIDialogueState::WaitingForResponse);
    SetDefaultCameraAndPosition();
    return true;
}

// === PROGRESS AI DIALOGUE FUNCTION ===
bool UADSAIDialoguePartecipantComponent::ProgressAIDialogue(const FString& PlayerMessage)
{
    UE_LOG(LogTemp, Log, TEXT("ProgressAIDialogue called with message: %s"), *PlayerMessage);

    // Check if already busy
    if (IsAIDialogueBusy()) {
        FString ErrorMsg = "AI Dialogue is already processing a request. Please wait.";
        UE_LOG(LogTemp, Warning, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Check configuration
    if (!IsAIDialogueEnabled() || GetAPIKey().IsEmpty()) {
        FString ErrorMsg = "AI Dialogue not properly configured";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Validate input
    if (PlayerMessage.IsEmpty()) {
        FString ErrorMsg = "Player message cannot be empty";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return false;
    }

    // Set state to processing
    SetAIDialogueState(EAIDialogueState::Processing);

    // Create rich context for the AI response
    FString Context = FString::Printf(TEXT("Player said: '%s'"), *PlayerMessage);

    // Broadcast conversation progress event
    int32 MessageCount = ConversationHistory.Num() / 2;
    OnConversationProgress.Broadcast(PlayerMessage, MessageCount);

    // This is a continuation, so it's not the first response
    bIsFirstResponse = false;

    UE_LOG(LogTemp, Log, TEXT("Progressing conversation (Message #%d)"), MessageCount + 1);
    UE_LOG(LogTemp, Log, TEXT("Sending API request for AI response"));
    GenerateAIResponse(PlayerMessage, Context);

    // Set state to waiting for response
    SetAIDialogueState(EAIDialogueState::WaitingForResponse);

    return true;
}

// === AI RESPONSE GENERATION ===
void UADSAIDialoguePartecipantComponent::GenerateAIResponse(const FString& PlayerInput, const FString& Context)
{
    // Add player message to conversation history
    AddToConversationHistory(TEXT("Player"), PlayerInput);

    // Build comprehensive SystemPrompt with all AI parameters
    FString SystemPrompt;

    // Basic character information
    SystemPrompt += FString::Printf(TEXT("You are %s.\n"), *GetParticipantName().ToString());

    // Add personality if available (no hardcoded restrictions)
    if (!GetAIPersonality().IsEmpty()) {
        SystemPrompt += FString::Printf(TEXT("Personality: %s\n"), *GetAIPersonality());
    }

    // Add character description if available (no hardcoded restrictions)
    if (!GetAICharacterDescription().IsEmpty()) {
        SystemPrompt += FString::Printf(TEXT("Description: %s\n"), *GetAICharacterDescription());
    }

    // Add behavioral rules if available (no hardcoded restrictions)
    if (!GetAICharacterRules().IsEmpty()) {
        SystemPrompt += FString::Printf(TEXT("Rules:\n%s\n"), *GetAICharacterRules());
    }

    // Add conversation context if we have history
    if (StructuredConversationHistory.Num() > 1) {
        SystemPrompt += TEXT("\nConversation context (recent exchanges):\n");

        // Add the last few exchanges for context (excluding the current player message we just added)
        int32 StartIndex = FMath::Max(0, StructuredConversationHistory.Num() - (MaxConversationHistory * 2));
        for (int32 i = StartIndex; i < StructuredConversationHistory.Num() - 1; i++) {
            const FADSConversationEntry& Entry = StructuredConversationHistory[i];
            SystemPrompt += FString::Printf(TEXT("%s: %s\n"), *Entry.Speaker, *Entry.Message);
        }
        SystemPrompt += TEXT("\n");
    }

    // Add additional context if provided
    if (!Context.IsEmpty()) {
        SystemPrompt += FString::Printf(TEXT("Current context: %s\n"), *Context);
    }

    // Final instruction
    SystemPrompt += TEXT("Respond naturally to the player's message, staying in character and considering the conversation history.");

    UE_LOG(LogTemp, Verbose, TEXT("Generated SystemPrompt with conversation history: %s"), *SystemPrompt);

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    if (!Settings) {
        FString ErrorMsg = "Cannot access dialogue settings";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return;
    }

    TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(GetAPIEndpoint());
    HttpRequest->SetVerb("POST");

    // Process headers template
    TMap<FString, FString> Headers = Settings->ProcessHeadersTemplate(Settings->GetAIAPIKey());
    for (const auto& HeaderPair : Headers) {
        HttpRequest->SetHeader(HeaderPair.Key, HeaderPair.Value);
        UE_LOG(LogTemp, Verbose, TEXT("Setting header: %s = %s"), *HeaderPair.Key, *HeaderPair.Value);
    }

    // Process payload template - use local overrides if available
    FString ModelToUse = !LocalAIModel.IsEmpty() ? LocalAIModel : Settings->GetAIModel();
    int32 MaxTokensToUse = LocalMaxTokens > 0 ? LocalMaxTokens : Settings->GetMaxTokens();

    FString ProcessedPayload = Settings->ProcessPayloadTemplate(
        SystemPrompt,
        PlayerInput,
        ModelToUse,
        MaxTokensToUse);

    UE_LOG(LogTemp, Warning, TEXT("=== DEBUG: AI API Request ==="));
    UE_LOG(LogTemp, Warning, TEXT("URL: %s"), *GetAPIEndpoint());
    UE_LOG(LogTemp, Warning, TEXT("Model: %s"), *ModelToUse);
    UE_LOG(LogTemp, Warning, TEXT("Max Tokens: %d"), MaxTokensToUse);
    UE_LOG(LogTemp, Warning, TEXT("Conversation History Entries: %d"), StructuredConversationHistory.Num());
    UE_LOG(LogTemp, Warning, TEXT("Processed payload: %s"), *ProcessedPayload);

    // Validate JSON before sending
    TSharedPtr<FJsonObject> ValidationJson;
    TSharedRef<TJsonReader<>> ValidationReader = TJsonReaderFactory<>::Create(ProcessedPayload);
    if (!FJsonSerializer::Deserialize(ValidationReader, ValidationJson)) {
        FString ErrorMsg = "Generated JSON payload is invalid - check template configuration";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        UE_LOG(LogTemp, Error, TEXT("Invalid JSON: %s"), *ProcessedPayload);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return;
    }

    HttpRequest->SetContentAsString(ProcessedPayload);
    HttpRequest->OnProcessRequestComplete().BindUObject(this, &UADSAIDialoguePartecipantComponent::OnHTTPResponseReceived);

    if (!HttpRequest->ProcessRequest()) {
        FString ErrorMsg = "Failed to send HTTP request";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
    } else {
        UE_LOG(LogTemp, Warning, TEXT("HTTP request sent successfully with conversation context"));
    }
}

// === HTTP RESPONSE HANDLER ===
void UADSAIDialoguePartecipantComponent::OnHTTPResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    UE_LOG(LogTemp, Log, TEXT("HTTP response received"));

    if (!bWasSuccessful || !Response.IsValid()) {
        FString ErrorMsg = "Connection failed";
        UE_LOG(LogTemp, Error, TEXT("HTTP request failed"));
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return;
    }

    int32 ResponseCode = Response->GetResponseCode();
    FString ResponseContent = Response->GetContentAsString();

    // Log the response content for debugging, especially for 400 errors
    UE_LOG(LogTemp, Warning, TEXT("HTTP Response Code: %d"), ResponseCode);
    UE_LOG(LogTemp, Warning, TEXT("HTTP Response Content: %s"), *ResponseContent);

    if (ResponseCode != 200) {
        FString ErrorMsg;
        if (ResponseCode == 400) {
            ErrorMsg = FString::Printf(TEXT("Bad Request (400) - Invalid JSON or parameters. Server response: %s"), *ResponseContent);
            UE_LOG(LogTemp, Error, TEXT("API Bad Request (400) - Response: %s"), *ResponseContent);
        } else if (ResponseCode == 429) {
            ErrorMsg = "API rate limit exceeded - please wait before trying again";
            UE_LOG(LogTemp, Error, TEXT("API rate limit exceeded"));
        } else if (ResponseCode == 401) {
            ErrorMsg = "Invalid API key - please check your configuration";
            UE_LOG(LogTemp, Error, TEXT("Invalid API key"));
        } else if (ResponseCode == 500) {
            ErrorMsg = "Server error - please try again later";
            UE_LOG(LogTemp, Error, TEXT("Server error"));
        } else {
            ErrorMsg = FString::Printf(TEXT("API error %d - Response: %s"), ResponseCode, *ResponseContent);
            UE_LOG(LogTemp, Error, TEXT("API error %d - Response: %s"), ResponseCode, *ResponseContent);
        }

        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return;
    }

    TSharedPtr<FJsonObject> JsonResponse;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);

    if (!FJsonSerializer::Deserialize(Reader, JsonResponse)) {
        FString ErrorMsg = "Failed to parse JSON response";
        UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
        LastErrorMessage = ErrorMsg;
        SetAIDialogueState(EAIDialogueState::Error);
        OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
        return;
    }

    const TArray<TSharedPtr<FJsonValue>>* ChoicesArray;
    if (JsonResponse->TryGetArrayField(TEXT("choices"), ChoicesArray) && ChoicesArray->Num() > 0) {
        TSharedPtr<FJsonObject> FirstChoice = (*ChoicesArray)[0]->AsObject();
        if (FirstChoice.IsValid()) {
            TSharedPtr<FJsonObject> Message = FirstChoice->GetObjectField(TEXT("message"));
            if (Message.IsValid()) {
                FString AIResponse = Message->GetStringField(TEXT("content"));

                // Add AI response to conversation history
                AddToConversationHistory(GetParticipantName().ToString(), AIResponse);

                ConversationHistory.Add(FString::Printf(TEXT("AI: %s"), *AIResponse));
                LastAIResponse = AIResponse;

                UE_LOG(LogTemp, Log, TEXT("AI response received successfully"));
                UE_LOG(LogTemp, Verbose, TEXT("%s: %s"), *GetParticipantName().ToString(), *AIResponse);

                SetAIDialogueState(EAIDialogueState::Completed);

                // Store the current first response flag before potentially resetting it
                bool CurrentIsFirstResponse = bIsFirstResponse;

                // Broadcast the response with the first response flag
                OnAIResponseReceived.Broadcast(AIResponse, true, CurrentIsFirstResponse);

                // Reset to Idle after a brief moment to allow Blueprint to process the response
                FTimerHandle TimerHandle;
                GetWorld()->GetTimerManager().SetTimer(TimerHandle, [this]() { SetAIDialogueState(EAIDialogueState::Idle); }, 0.1f, false);

                return;
            }
        }
    }

    FString ErrorMsg = "Failed to extract AI response from JSON";
    UE_LOG(LogTemp, Error, TEXT("%s"), *ErrorMsg);
    LastErrorMessage = ErrorMsg;
    SetAIDialogueState(EAIDialogueState::Error);
    OnAIResponseReceived.Broadcast(ErrorMsg, false, false);
}

// === REQUIRED OVERRIDES ===
bool UADSAIDialoguePartecipantComponent::TryStartDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSDialogue* dialogueToStart)
{
    UE_LOG(LogTemp, Log, TEXT("TryStartDialogue called - redirecting to AI dialogue"));
    UE_LOG(LogTemp, Verbose, TEXT("Participants: %d, Dialogue: %s"),
        participants.Num(),
        dialogueToStart ? *dialogueToStart->GetName() : TEXT("NULL"));

    return StartAIDialogue("Hello");
}

bool UADSAIDialoguePartecipantComponent::TryStartDialogueFromActors(const TArray<AActor*>& participants, UADSDialogue* dialogueToStart)
{
    UE_LOG(LogTemp, Log, TEXT("TryStartDialogueFromActors called - redirecting to AI dialogue"));
    return StartAIDialogue("Hello");
}

UADSDialogue* UADSAIDialoguePartecipantComponent::GetDialogue(FGameplayTag dialogueTag, bool& bFound) const
{
    UE_LOG(LogTemp, Verbose, TEXT("GetDialogue called - AI uses dynamic responses"));
    bFound = false;
    return nullptr;
}

// === ANIMATION FUNCTIONS ===
USkeletalMeshComponent* UADSAIDialoguePartecipantComponent::GetOwnerMesh()
{
    if (skeletalMesh) {
        return skeletalMesh;
    }

    const ACharacter* CharacterOwner = Cast<ACharacter>(GetOwner());
    if (CharacterOwner) {
        skeletalMesh = CharacterOwner->GetMesh();
    }

    skeletalMesh = GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
    return skeletalMesh;
}

USkeletalMeshComponent* UADSAIDialoguePartecipantComponent::GetFacialAnimationMesh()
{
    if (facialMesh) {
        return facialMesh;
    }

    TArray<UActorComponent*> Components;
    GetOwner()->GetComponents(USkeletalMeshComponent::StaticClass(), Components);
    for (UActorComponent* Component : Components) {
        USkeletalMeshComponent* SkeletalMeshComp = Cast<USkeletalMeshComponent>(Component);
        if (SkeletalMeshComp && SkeletalMeshComp->ComponentHasTag(FacialSkeletonComponentTag)) {
            facialMesh = SkeletalMeshComp;
            return facialMesh;
        }
    }

    return nullptr;
}

void UADSAIDialoguePartecipantComponent::PlayAnimationOnCharacterOwner(UAnimMontage* animation)
{
    if (GetOwnerMesh()) {
        UAnimInstance* animInstance = skeletalMesh->GetAnimInstance();
        if (animInstance) {
            animInstance->Montage_Play(animation);
        }
    }
}

void UADSAIDialoguePartecipantComponent::PlayFacialAnimationOnCharacterOwner(UAnimMontage* animation)
{
    if (GetFacialAnimationMesh()) {
        UAnimInstance* animInstance = facialMesh->GetAnimInstance();
        if (animInstance) {
            animInstance->Montage_Play(animation);
        }
    }
}

void UADSAIDialoguePartecipantComponent::StopFacialAnimationOnCharacterOwner(UAnimMontage* animation)
{
    if (GetFacialAnimationMesh()) {
        UAnimInstance* animInstance = facialMesh->GetAnimInstance();
        if (animInstance) {
            animInstance->Montage_Stop(AnimationBlendoutTime, animation);
        }
    }
}

void UADSAIDialoguePartecipantComponent::StopAnimationOnCharacterOwner(UAnimMontage* animation)
{
    if (GetOwnerMesh()) {
        UAnimInstance* animInstance = skeletalMesh->GetAnimInstance();
        if (animInstance) {
            animInstance->Montage_Stop(AnimationBlendoutTime, animation);
        }
    }
}



void UADSAIDialoguePartecipantComponent::HandleDialogueStarted()
{
    OnDialogueStartedEvent();
    OnDialogueStarted.Broadcast(nullptr);
}

void UADSAIDialoguePartecipantComponent::HandleDialogueEnded()
{
    APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
    UADSDialogueMasterComponent* dialogueMaster = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(this);
    if (dialogueMaster) {
        dialogueMaster->StopCurrentShot();
    }
    OnDialogueEndedEvent();
    OnDialogueEnded.Broadcast(nullptr);
}

// Ends the AI dialogue manually
void UADSAIDialoguePartecipantComponent::EndAIDialogue()
{
    UE_LOG(LogTemp, Log, TEXT("Manually ending AI dialogue"));

    // Reset state
    SetAIDialogueState(EAIDialogueState::Idle);
    ConversationHistory.Empty();
    StructuredConversationHistory.Empty();
    bIsFirstResponse = true;

    // Trigger the end event with proper broadcast
    HandleDialogueEnded();
}

// === SETTINGS ACCESS ===
UADSDialogueDeveloperSettings* UADSAIDialoguePartecipantComponent::GetDialogueSettings() const
{
    return GetMutableDefault<UADSDialogueDeveloperSettings>();
}

FString UADSAIDialoguePartecipantComponent::GetAPIKey() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return Settings ? Settings->GetAIAPIKey() : FString();
}

FString UADSAIDialoguePartecipantComponent::GetAPIEndpoint() const
{
    // Use local override if available, otherwise use global settings
    if (!LocalAPIEndpoint.IsEmpty()) {
        return LocalAPIEndpoint;
    }

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return Settings ? Settings->GetAIAPIEndpoint() : FString("https://api.openai.com/v1/chat/completions");
}

FString UADSAIDialoguePartecipantComponent::GetAIModel() const
{
    // Use local override if available, otherwise use global settings
    if (!LocalAIModel.IsEmpty()) {
        return LocalAIModel;
    }

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return Settings ? Settings->GetAIModel() : FString("gpt-3.5-turbo");
}

int32 UADSAIDialoguePartecipantComponent::GetMaxTokens() const
{
    // Use local override if available, otherwise use global settings
    if (LocalMaxTokens > 0) {
        return LocalMaxTokens;
    }

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return Settings ? Settings->GetMaxTokens() : 150;
}

bool UADSAIDialoguePartecipantComponent::IsAIDialogueEnabled() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return Settings ? Settings->IsAIDialogueEnabled() : false;
}

// === CONVERSATION HISTORY MANAGEMENT ===

void UADSAIDialoguePartecipantComponent::AddToConversationHistory(const FString& Speaker, const FString& Message)
{
    StructuredConversationHistory.Add(FADSConversationEntry(Speaker, Message));
    TrimConversationHistory();

    UE_LOG(LogTemp, Verbose, TEXT("Added to conversation history: %s: %s"), *Speaker, *Message);
    UE_LOG(LogTemp, Verbose, TEXT("Total conversation entries: %d"), StructuredConversationHistory.Num());
}

void UADSAIDialoguePartecipantComponent::TrimConversationHistory()
{
    // Keep only the last MaxConversationHistory exchanges (each exchange = player + AI message)
    int32 MaxEntries = MaxConversationHistory * 2; // Player + AI = 2 entries per exchange

    if (StructuredConversationHistory.Num() > MaxEntries) {
        int32 EntriesToRemove = StructuredConversationHistory.Num() - MaxEntries;
        StructuredConversationHistory.RemoveAt(0, EntriesToRemove);

        UE_LOG(LogTemp, Log, TEXT("Trimmed conversation history - removed %d old entries"), EntriesToRemove);
    }
}

FString UADSAIDialoguePartecipantComponent::GetConversationHistoryAsJSON() const
{
    FString JsonString = TEXT("{\n  \"conversation_history\": [\n");

    for (int32 i = 0; i < StructuredConversationHistory.Num(); i++) {
        const FADSConversationEntry& Entry = StructuredConversationHistory[i];

        // Escape quotes in the message
        FString EscapedMessage = Entry.Message.Replace(TEXT("\""), TEXT("\\\""));
        EscapedMessage = EscapedMessage.Replace(TEXT("\n"), TEXT("\\n"));
        EscapedMessage = EscapedMessage.Replace(TEXT("\r"), TEXT("\\r"));

        JsonString += FString::Printf(TEXT("    {\n      \"speaker\": \"%s\",\n      \"message\": \"%s\",\n      \"timestamp\": \"%s\"\n    }"),
            *Entry.Speaker,
            *EscapedMessage,
            *Entry.Timestamp.ToString());

        if (i < StructuredConversationHistory.Num() - 1) {
            JsonString += TEXT(",");
        }
        JsonString += TEXT("\n");
    }

    JsonString += TEXT("  ]\n}");
    return JsonString;
}

FString UADSAIDialoguePartecipantComponent::GetConversationHistoryAsText() const
{
    FString TextHistory;

    for (const FADSConversationEntry& Entry : StructuredConversationHistory) {
        TextHistory += FString::Printf(TEXT("[%s] %s: %s\n"),
            *Entry.Timestamp.ToString(TEXT("%H:%M:%S")),
            *Entry.Speaker,
            *Entry.Message);
    }

    return TextHistory;
}

int32 UADSAIDialoguePartecipantComponent::GetConversationExchangeCount() const
{
    // Each exchange consists of a player message followed by an AI response
    // So we count pairs, but handle odd numbers gracefully
    return (StructuredConversationHistory.Num() + 1) / 2;
}

void UADSAIDialoguePartecipantComponent::ClearConversationHistory()
{
    StructuredConversationHistory.Empty();
    ConversationHistory.Empty(); // Also clear the legacy array

    UE_LOG(LogTemp, Log, TEXT("Conversation history cleared"));
}

void UADSAIDialoguePartecipantComponent::SetMaxConversationHistory(int32 NewMaxHistory)
{
    MaxConversationHistory = FMath::Clamp(NewMaxHistory, 1, 50);
    TrimConversationHistory(); // Apply the new limit immediately

    UE_LOG(LogTemp, Log, TEXT("Max conversation history set to %d exchanges"), MaxConversationHistory);
}