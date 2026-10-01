#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Sound/SoundWave.h"
#include <Components/AudioComponent.h>
#include "ADSAITextToSpeech.generated.h"

DECLARE_LOG_CATEGORY_EXTERN(ADSAITextToSpeechLog, Log, All);

// Enum for AI TTS state
UENUM(BlueprintType)
enum class EAITTSState : uint8
{
    Idle                UMETA(DisplayName = "Idle"),
    Processing          UMETA(DisplayName = "Processing"),
    WaitingForResponse  UMETA(DisplayName = "Waiting For Response"),
    PlayingAudio        UMETA(DisplayName = "Playing Audio"),
    Completed           UMETA(DisplayName = "Completed"),
    Error               UMETA(DisplayName = "Error")
};

// Enum for TTS error types
UENUM(BlueprintType)
enum class EAITTSErrorType : uint8
{
    None            UMETA(DisplayName = "None"),
    NetworkError    UMETA(DisplayName = "Network Error"),
    APIKeyError     UMETA(DisplayName = "API Key Error"),
    AudioError      UMETA(DisplayName = "Audio Processing Error"),
    ConfigError     UMETA(DisplayName = "Configuration Error"),
    RateLimitError  UMETA(DisplayName = "Rate Limit Error"),
    ServerError     UMETA(DisplayName = "Server Error"),
    UnknownError    UMETA(DisplayName = "Unknown Error")
};

// Delegate to notify when AI TTS audio is ready
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAITTSAudioReady, const TArray<uint8>&, AudioData);

// Delegate to notify when AI TTS fails
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnAITTSError, EAITTSErrorType, ErrorType, const FString&, ErrorMessage, const FString&, OriginalText);

// Delegate to notify when AI TTS completes (success or failure)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnAITTSCompleted, const TArray<uint8>&, AudioData, bool, bSuccess, EAITTSErrorType, ErrorType);

// Delegate to notify when AI TTS succeeds (kept for backward compatibility)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAITTSSuccess, const FString&, SpokenText);

// Delegate for AI TTS state changes
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAITTSStateChanged, EAITTSState, NewState);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class ASCENTDIALOGUESYSTEM_API UADSAITextToSpeech : public UActorComponent
{
    GENERATED_BODY()

public:
    UADSAITextToSpeech();

    // Generate AI TTS audio from text and optionally play it (uses component settings)
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void SpeakText(const FString& Text, bool bPlayAudio = true);

    // Check if any TTS audio is currently playing
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsAudioPlaying() const;

    // Manually stop all currently playing TTS audio
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void StopTTSAudio(bool bFadeOut = false, float FadeOutDuration = 0.5f);

    // Advanced version with full parameter control (C++ only)
    void SpeakTextAdvanced(const FString& Text, bool bPlayAudio = true, const FString& Voice = TEXT(""), const FString& Model = TEXT(""), const FString& ApiKey = TEXT(""));

    // Check if TTS is currently processing
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsTTSProcessing() const { return CurrentTTSState == EAITTSState::Processing || CurrentTTSState == EAITTSState::WaitingForResponse; }

    // Check if TTS is currently busy (processing, waiting, or playing audio)
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsTTSBusy() const { return CurrentTTSState != EAITTSState::Idle && CurrentTTSState != EAITTSState::Error; }

    // Gets the current state of the AI TTS
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    EAITTSState GetTTSState() const { return CurrentTTSState; }

    // Resets the AI TTS state to Idle (use in case of errors)
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void ResetTTSState();

    // Get the last error that occurred
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    EAITTSErrorType GetLastErrorType() const { return LastErrorType; }

    // Get the last error message
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetLastErrorMessage() const { return LastErrorMessage; }

    // Clear the last error
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void ClearLastError();

    // Set local AI TTS voice override
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void SetLocalAITTSVoice(const FString& Voice);

    // Set local AI TTS model override
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void SetLocalAITTSModel(const FString& Model);

    // Set local AI TTS API endpoint override
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void SetLocalAITTSAPIEndpoint(const FString& Endpoint);

    // Set local AI TTS API key override
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void SetLocalAITTSAPIKey(const FString& ApiKey);

    // Get current AI TTS voice (local override or global setting)
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetAITTSVoice() const;

    // Get current AI TTS model (local override or global setting)
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetAITTSModel() const;

    // Get current AI TTS API endpoint (local override or global setting)
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetAITTSAPIEndpoint() const;

    // Get current AI TTS API key (local override or global setting)
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetAITTSAPIKey() const;

    // Check if local voice override is being used
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsUsingLocalVoiceOverride() const { return !VoiceType.IsEmpty(); }

    // Check if local model override is being used
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsUsingLocalModelOverride() const { return !LocalAITTSModel.IsEmpty(); }

    // Check if local API endpoint override is being used
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsUsingLocalAPIEndpointOverride() const { return !LocalAITTSAPIEndpoint.IsEmpty(); }

    // Check if local API key override is being used
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool IsUsingLocalAPIKeyOverride() const { return !LocalAITTSAPIKey.IsEmpty(); }

    // Clear all local overrides (will use global settings)
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void ClearAllLocalOverrides();

    // Get cached audio data from last successful TTS generation
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    const TArray<uint8>& GetCachedAudioData() const { return CachedAudioData; }

    // Get the cached audio text
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    FString GetCachedAudioText() const { return CachedAudioText; }

    // Check if there is cached audio data available
    UFUNCTION(BlueprintPure, Category = "ADS AI TTS")
    bool HasCachedAudioData() const { return CachedAudioData.Num() > 0; }

    // Clear cached audio data
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    void ClearCachedAudioData();

    // Play the cached audio data (if any)
    UFUNCTION(BlueprintCallable, Category = "ADS AI TTS")
    bool PlayCachedAudioData();

    // === EVENTS ===
    
    // Delegate to notify when AI TTS audio is ready
    UPROPERTY(BlueprintAssignable, Category = "ADS AI TTS")
    FOnAITTSAudioReady OnAITTSAudioReady;
    
    // Delegate to notify when AI TTS fails
    UPROPERTY(BlueprintAssignable, Category = "ADS AI TTS")
    FOnAITTSError OnAITTSError;
    
    // Delegate to notify when AI TTS completes (success or failure)
    UPROPERTY(BlueprintAssignable, Category = "ADS AI TTS")
    FOnAITTSCompleted OnAITTSCompleted;
    
    // Delegate to notify when AI TTS succeeds (kept for backward compatibility)
    UPROPERTY(BlueprintAssignable, Category = "ADS AI TTS")
    FOnAITTSSuccess OnAITTSSuccess;
    
    // Delegate for AI TTS state changes
    UPROPERTY(BlueprintAssignable, Category = "ADS AI TTS")
    FOnAITTSStateChanged OnAITTSStateChanged;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    // === LOCAL TTS SETTINGS OVERRIDES ===
    
    // Local override for TTS voice (leave empty to use global settings)
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Local TTS Overrides", 
        meta = (DisplayName = "Voice Override", ToolTip = "Local TTS voice override. Leave empty to use global settings."))
    FString VoiceType;
    
    // Local override for TTS model (leave empty to use global settings)
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Local TTS Overrides", 
        meta = (DisplayName = "Model Override", ToolTip = "Local TTS model override. Leave empty to use global settings."))
    FString LocalAITTSModel;
    
    // Local override for TTS API endpoint (leave empty to use global settings)
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Local TTS Overrides", 
        meta = (DisplayName = "API Endpoint Override", ToolTip = "Local TTS API endpoint override. Leave empty to use global settings."))
    FString LocalAITTSAPIEndpoint;
    
    // Local override for TTS API key (leave empty to use global settings)
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Local TTS Overrides", 
        meta = (DisplayName = "API Key Override", ToolTip = "Local TTS API key override. Leave empty to use global settings.", PasswordField = true))
    FString LocalAITTSAPIKey;

private:
    // === ORIGINAL PRIVATE VARIABLES ===

    // Current TTS state
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS AI TTS", meta = (AllowPrivateAccess = "true"))
    EAITTSState CurrentTTSState = EAITTSState::Idle;

    // Legacy processing state for backward compatibility
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS AI TTS", meta = (AllowPrivateAccess = "true"))
    bool bIsProcessing = false;

    // Last error type that occurred
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS AI TTS", meta = (AllowPrivateAccess = "true"))
    EAITTSErrorType LastErrorType = EAITTSErrorType::None;

    // Last error message
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ADS AI TTS", meta = (AllowPrivateAccess = "true"))
    FString LastErrorMessage;

    // Single audio component for TTS playback
    UPROPERTY()
    TObjectPtr<UAudioComponent> CurrentAudioComponent;

    // Cached audio data from last successful TTS generation
    UPROPERTY()
    TArray<uint8> CachedAudioData;

    // Text associated with cached audio data
    UPROPERTY()
    FString CachedAudioText;

    // Callback when audio finishes playing
    UFUNCTION()
    void OnAudioFinished();

    // Internal AI TTS generation function
    void GenerateAITTSInternal(const FString& Text, const FString& Voice, const FString& Model, const FString& ApiKey, bool bPlayAudio);

    // Play audio from buffer
    void PlayAudioFromBuffer(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels, bool bIsWav);

    // Correct WAV header parsing
    int32 ParseWAVHeader(const TArray<uint8>& AudioData, int32& OutSampleRate, int32& OutNumChannels);

    // Handle TTS error with proper classification
    void HandleTTSError(EAITTSErrorType ErrorType, const FString& ErrorMessage, const FString& OriginalText);

    // Sets the TTS state and broadcasts the change
    void SetTTSState(EAITTSState NewState);

    // Get dialogue settings
    class UADSDialogueDeveloperSettings* GetDialogueSettings() const;

    // Helper function to resolve settings with fallback to global
    FString GetResolvedSetting(const FString& LocalValue, const FString& GlobalValue) const;

    // Classify HTTP error code to TTS error type
    EAITTSErrorType ClassifyHTTPError(int32 ResponseCode) const;
};