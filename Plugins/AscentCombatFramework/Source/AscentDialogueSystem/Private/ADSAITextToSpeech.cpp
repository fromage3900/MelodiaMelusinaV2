#include "ADSAITextToSpeech.h"
#include "ADSDialogueDeveloperSettings.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundWaveProcedural.h"
#include "Engine/Engine.h"
#include "GameFramework/Actor.h"
#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include <Engine/TimerHandle.h>
#include <Components/AudioComponent.h>
#include <TimerManager.h>

DEFINE_LOG_CATEGORY(ADSAITextToSpeechLog);

UADSAITextToSpeech::UADSAITextToSpeech()
{
    PrimaryComponentTick.bCanEverTick = false;
    CurrentTTSState = EAITTSState::Idle;
    bIsProcessing = false;
    LastErrorType = EAITTSErrorType::None;
}

void UADSAITextToSpeech::BeginPlay()
{
    Super::BeginPlay();
    SetTTSState(EAITTSState::Idle);
    ClearLastError();
}

void UADSAITextToSpeech::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // Stop all active audio before ending play
    StopTTSAudio(false, 0.0f);
    
    // Clear cached audio data
    ClearCachedAudioData();
    
    Super::EndPlay(EndPlayReason);
}

void UADSAITextToSpeech::SpeakText(const FString& Text, bool bPlayAudio)
{
    if (IsTTSBusy())
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("TTS is busy - stopping current audio before processing new request"));
        StopTTSAudio(false, 0.0f);
    }

    if (Text.IsEmpty())
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("Text cannot be empty"), Text);
        return;
    }

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    if (!Settings)
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("Cannot access dialogue settings"), Text);
        return;
    }

    // Use component settings with fallback to global settings
    FString ResolvedVoice = GetResolvedSetting(VoiceType, Settings->GetTTSVoice());
    FString ResolvedModel = GetResolvedSetting(LocalAITTSModel, Settings->GetTTSModel());
    FString ResolvedApiKey = GetResolvedSetting(LocalAITTSAPIKey, Settings->GetTTSAPIKey());

    ClearLastError();
    SetTTSState(EAITTSState::Processing);
    GenerateAITTSInternal(Text, ResolvedVoice, ResolvedModel, ResolvedApiKey, bPlayAudio);
}

void UADSAITextToSpeech::SpeakTextAdvanced(const FString& Text, bool bPlayAudio, const FString& Voice, const FString& Model, const FString& ApiKey)
{
    if (IsTTSBusy())
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("TTS is busy - stopping current audio before processing new request"));
        StopTTSAudio(false, 0.0f);
    }

    if (Text.IsEmpty())
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("Text cannot be empty"), Text);
        return;
    }

    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    if (!Settings)
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("Cannot access dialogue settings"), Text);
        return;
    }

    // Use provided parameters with fallback to component then global settings
    FString ResolvedVoice = Voice.IsEmpty() ? GetResolvedSetting(VoiceType, Settings->GetTTSVoice()) : Voice;
    FString ResolvedModel = Model.IsEmpty() ? GetResolvedSetting(LocalAITTSModel, Settings->GetTTSModel()) : Model;
    FString ResolvedApiKey = ApiKey.IsEmpty() ? GetResolvedSetting(LocalAITTSAPIKey, Settings->GetTTSAPIKey()) : ApiKey;

    ClearLastError();
    SetTTSState(EAITTSState::Processing);
    GenerateAITTSInternal(Text, ResolvedVoice, ResolvedModel, ResolvedApiKey, bPlayAudio);
}

void UADSAITextToSpeech::ResetTTSState()
{
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Resetting TTS State to Idle"));
    SetTTSState(EAITTSState::Idle);
    ClearLastError();
}

void UADSAITextToSpeech::ClearLastError()
{
    LastErrorType = EAITTSErrorType::None;
    LastErrorMessage.Empty();
}

void UADSAITextToSpeech::SetTTSState(EAITTSState NewState)
{
    if (CurrentTTSState != NewState)
    {
        EAITTSState OldState = CurrentTTSState;
        CurrentTTSState = NewState;

        // Update legacy bIsProcessing flag for backward compatibility
        bIsProcessing = (NewState == EAITTSState::Processing || NewState == EAITTSState::WaitingForResponse);

        UE_LOG(ADSAITextToSpeechLog, Log, TEXT("TTS State changed from %d to %d"), (int32)OldState, (int32)NewState);

        // Broadcast state change
        OnAITTSStateChanged.Broadcast(NewState);

        // Clear error message when going back to Idle
        if (NewState == EAITTSState::Idle)
        {
            LastErrorMessage.Empty();
        }
    }
}

void UADSAITextToSpeech::GenerateAITTSInternal(const FString& Text, const FString& Voice, const FString& Model, const FString& ApiKey, bool bPlayAudio)
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    if (!Settings)
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("Cannot access dialogue settings"), Text);
        return;
    }

    if (!Settings->IsTTSEnabled())
    {
        HandleTTSError(EAITTSErrorType::ConfigError, TEXT("AI TTS is disabled in settings"), Text);
        return;
    }

    if (ApiKey.IsEmpty())
    {
        HandleTTSError(EAITTSErrorType::APIKeyError, TEXT("AI TTS API key is empty"), Text);
        return;
    }

    // Set state to waiting for response
    SetTTSState(EAITTSState::WaitingForResponse);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(GetAITTSAPIEndpoint());
    Request->SetVerb(TEXT("POST"));
    
    // Process AI TTS headers using the settings template
    TMap<FString, FString> Headers = Settings->ProcessTTSHeadersTemplate(ApiKey);
    for (const auto& HeaderPair : Headers)
    {
        Request->SetHeader(HeaderPair.Key, HeaderPair.Value);
    }

    // Process AI TTS payload using the settings template
    FString ProcessedPayload = Settings->ProcessTTSPayloadTemplate(Text, Voice, Model);
    Request->SetContentAsString(ProcessedPayload);

    Request->OnProcessRequestComplete().BindLambda([this, Text, bPlayAudio](FHttpRequestPtr RequestPtr, FHttpResponsePtr Response, bool bSuccess)
    {
        if (!bSuccess)
        {
            HandleTTSError(EAITTSErrorType::NetworkError, TEXT("HTTP request failed - network error"), Text);
            return;
        }

        if (!Response.IsValid())
        {
            HandleTTSError(EAITTSErrorType::NetworkError, TEXT("Invalid HTTP response"), Text);
            return;
        }

        int32 ResponseCode = Response->GetResponseCode();
        
        if (ResponseCode != 200)
        {
            EAITTSErrorType ErrorType = ClassifyHTTPError(ResponseCode);
            FString ErrorMessage = FString::Printf(TEXT("HTTP %d: %s"), ResponseCode, *Response->GetContentAsString());
            HandleTTSError(ErrorType, ErrorMessage, Text);
            return;
        }

        TArray<uint8> AudioData = Response->GetContent();
        
        if (AudioData.Num() == 0)
        {
            HandleTTSError(EAITTSErrorType::AudioError, TEXT("Received empty audio data"), Text);
            return;
        }

        // Success! Cache the audio data and fire the events
        CachedAudioData = AudioData;
        CachedAudioText = Text;
        
        OnAITTSAudioReady.Broadcast(AudioData);
        OnAITTSSuccess.Broadcast(Text);
        OnAITTSCompleted.Broadcast(AudioData, true, EAITTSErrorType::None);
        
        UE_LOG(ADSAITextToSpeechLog, Log, TEXT("AI TTS completed successfully - received %d bytes, cached for future use"), AudioData.Num());

        // Play audio if requested
        if (bPlayAudio)
        {
            SetTTSState(EAITTSState::PlayingAudio);
            PlayAudioFromBuffer(AudioData, 16000, 1, true);
        }
        else
        {
            SetTTSState(EAITTSState::Completed);
        }
        
        // Reset to Idle after a brief moment to allow processing
        if (GetWorld())
        {
            FTimerHandle TimerHandle;
            GetWorld()->GetTimerManager().SetTimer(TimerHandle, [this]() { SetTTSState(EAITTSState::Idle); }, 0.1f, false);
        }
    });
    
    if (!Request->ProcessRequest())
    {
        HandleTTSError(EAITTSErrorType::NetworkError, TEXT("Failed to send HTTP request"), Text);
    }
}

void UADSAITextToSpeech::PlayAudioFromBuffer(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels, bool bIsWav)
{
    const uint8* PCMData = AudioData.GetData();
    int32 PCMSize = AudioData.Num();
    int32 ParsedSampleRate = SampleRate;
    int32 ParsedNumChannels = NumChannels;
    
    if (bIsWav)
    {
        int32 DataOffset = ParseWAVHeader(AudioData, ParsedSampleRate, ParsedNumChannels);
        if (DataOffset > 0 && DataOffset < AudioData.Num())
        {
            PCMData += DataOffset;
            PCMSize -= DataOffset;
            SampleRate = ParsedSampleRate;
            NumChannels = ParsedNumChannels;
        }
        else
        {
            UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("Failed to parse WAV header, using fallback"));
            PCMData += 44;
            PCMSize -= 44;
        }
    }
    
    if (PCMSize <= 0)
    {
        UE_LOG(ADSAITextToSpeechLog, Error, TEXT("Invalid audio data size after parsing"));
        return;
    }

    USoundWaveProcedural* SoundWave = NewObject<USoundWaveProcedural>();
    if (!SoundWave)
    {
        UE_LOG(ADSAITextToSpeechLog, Error, TEXT("Failed to create SoundWave object"));
        return;
    }

    SoundWave->SetSampleRate(SampleRate);
    SoundWave->NumChannels = NumChannels;
    SoundWave->Duration = (float)PCMSize / (2 * NumChannels * SampleRate);
    SoundWave->bLooping = false;
    SoundWave->SoundGroup = SOUNDGROUP_Voice;
    SoundWave->bProcedural = true;
    SoundWave->VirtualizationMode = EVirtualizationMode::PlayWhenSilent;
    
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Creating SoundWave: SampleRate=%d, Channels=%d, Duration=%.2fs, PCMSize=%d"), 
        SampleRate, NumChannels, SoundWave->Duration, PCMSize);
    
    SoundWave->QueueAudio(PCMData, PCMSize);
    
    // Stop and cleanup any existing audio component
    if (CurrentAudioComponent.Get())
    {
        CurrentAudioComponent->Stop();
        CurrentAudioComponent->OnAudioFinished.RemoveDynamic(this, &UADSAITextToSpeech::OnAudioFinished);
    }
    
    // Create new audio component
    CurrentAudioComponent = NewObject<UAudioComponent>(GetOwner());
    if (!CurrentAudioComponent)
    {
        UE_LOG(ADSAITextToSpeechLog, Error, TEXT("Failed to create AudioComponent"));
        return;
    }

    CurrentAudioComponent->RegisterComponent();
    CurrentAudioComponent->SetSound(SoundWave);
    
    // Set up completion callback
    CurrentAudioComponent->OnAudioFinished.AddDynamic(this, &UADSAITextToSpeech::OnAudioFinished);
    
    CurrentAudioComponent->Play();
    
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Started playing TTS audio"));
}

void UADSAITextToSpeech::OnAudioFinished()
{
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Audio finished playing"));
    
    // Clean up the current audio component
    if (CurrentAudioComponent.Get())
    {
        CurrentAudioComponent->OnAudioFinished.RemoveDynamic(this, &UADSAITextToSpeech::OnAudioFinished);
        CurrentAudioComponent = nullptr;
    }
    
    // If we were playing audio, transition to completed
    if (CurrentTTSState == EAITTSState::PlayingAudio)
    {
        SetTTSState(EAITTSState::Completed);
        
        // Reset to Idle after a brief moment
        if (GetWorld())
        {
            FTimerHandle TimerHandle;
            GetWorld()->GetTimerManager().SetTimer(TimerHandle, [this]() { SetTTSState(EAITTSState::Idle); }, 0.1f, false);
        }
    }
}

int32 UADSAITextToSpeech::ParseWAVHeader(const TArray<uint8>& AudioData, int32& OutSampleRate, int32& OutNumChannels)
{
    if (AudioData.Num() < 44)
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("Audio data too small for WAV header"));
        return 0;
    }
    
    // Check WAV signature
    if (AudioData[0] != 'R' || AudioData[1] != 'I' || AudioData[2] != 'F' || AudioData[3] != 'F')
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("Invalid WAV signature"));
        return 0;
    }
    
    // Read parameters from WAV header
    OutNumChannels = *(int16*)(AudioData.GetData() + 22);
    OutSampleRate = *(int32*)(AudioData.GetData() + 24);
    int16 BitsPerSample = *(int16*)(AudioData.GetData() + 34);
    
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("WAV Header: Channels=%d, SampleRate=%d, BitsPerSample=%d"), OutNumChannels, OutSampleRate, BitsPerSample);
    
    // Find PCM data start (search for "data" chunk)
    int32 DataOffset = 44; // Default
    for (int32 i = 12; i < AudioData.Num() - 8; i++)
    {
        if (AudioData[i] == 'd' && AudioData[i+1] == 'a' && AudioData[i+2] == 't' && AudioData[i+3] == 'a')
        {
            DataOffset = i + 8; // Skip "data" + size (4 bytes)
            break;
        }
    }
    
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("PCM data starts at offset: %d"), DataOffset);
    return DataOffset;
}

void UADSAITextToSpeech::HandleTTSError(EAITTSErrorType ErrorType, const FString& ErrorMessage, const FString& OriginalText)
{
    LastErrorType = ErrorType;
    LastErrorMessage = ErrorMessage;

    UE_LOG(ADSAITextToSpeechLog, Error, TEXT("TTS Error [%d]: %s (Original text: %s)"), 
        (int32)ErrorType, *ErrorMessage, *OriginalText);

    // Set state to error
    SetTTSState(EAITTSState::Error);

    // Create empty audio data for error case
    TArray<uint8> EmptyAudioData;

    // Broadcast error events
    OnAITTSError.Broadcast(ErrorType, ErrorMessage, OriginalText);
    OnAITTSCompleted.Broadcast(EmptyAudioData, false, ErrorType);
}

EAITTSErrorType UADSAITextToSpeech::ClassifyHTTPError(int32 ResponseCode) const
{
    switch (ResponseCode)
    {
        case 401:
        case 403:
            return EAITTSErrorType::APIKeyError;
        case 429:
            return EAITTSErrorType::RateLimitError;
        case 400:
        case 422:
            return EAITTSErrorType::ConfigError;
        case 500:
        case 502:
        case 503:
        case 504:
            return EAITTSErrorType::ServerError;
        default:
            return EAITTSErrorType::UnknownError;
    }
}

void UADSAITextToSpeech::SetLocalAITTSVoice(const FString& Voice)
{
    VoiceType = Voice;
}

void UADSAITextToSpeech::SetLocalAITTSModel(const FString& Model)
{
    LocalAITTSModel = Model;
}

void UADSAITextToSpeech::SetLocalAITTSAPIEndpoint(const FString& Endpoint)
{
    LocalAITTSAPIEndpoint = Endpoint;
}

void UADSAITextToSpeech::SetLocalAITTSAPIKey(const FString& ApiKey)
{
    LocalAITTSAPIKey = ApiKey;
}

FString UADSAITextToSpeech::GetAITTSVoice() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return GetResolvedSetting(VoiceType, Settings ? Settings->GetTTSVoice() : TEXT("alloy"));
}

FString UADSAITextToSpeech::GetAITTSModel() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return GetResolvedSetting(LocalAITTSModel, Settings ? Settings->GetTTSModel() : TEXT("tts-1"));
}

FString UADSAITextToSpeech::GetAITTSAPIEndpoint() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return GetResolvedSetting(LocalAITTSAPIEndpoint, Settings ? Settings->GetTTSAPIEndpoint() : TEXT("https://api.openai.com/v1/audio/speech"));
}

FString UADSAITextToSpeech::GetAITTSAPIKey() const
{
    UADSDialogueDeveloperSettings* Settings = GetDialogueSettings();
    return GetResolvedSetting(LocalAITTSAPIKey, Settings ? Settings->GetTTSAPIKey() : TEXT(""));
}

FString UADSAITextToSpeech::GetResolvedSetting(const FString& LocalValue, const FString& GlobalValue) const
{
    return LocalValue.IsEmpty() ? GlobalValue : LocalValue;
}

UADSDialogueDeveloperSettings* UADSAITextToSpeech::GetDialogueSettings() const
{
    return GetMutableDefault<UADSDialogueDeveloperSettings>();
}

void UADSAITextToSpeech::StopTTSAudio(bool bFadeOut, float FadeOutDuration)
{
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Stopping TTS audio (%s)"), bFadeOut ? TEXT("with fade out") : TEXT("immediately"));

    // Stop current audio component if active
    if (CurrentAudioComponent.Get() && CurrentAudioComponent->IsPlaying())
    {
        if (bFadeOut && FadeOutDuration > 0.0f)
        {
            CurrentAudioComponent->FadeOut(FadeOutDuration, 0.0f);
            UE_LOG(ADSAITextToSpeechLog, Verbose, TEXT("Fading out audio component over %.2f seconds"), FadeOutDuration);
        }
        else
        {
            CurrentAudioComponent->Stop();
            UE_LOG(ADSAITextToSpeechLog, Verbose, TEXT("Stopped audio component immediately"));
        }
    }
    
    // Clean up the audio component reference
    if (CurrentAudioComponent.Get())
    {
        CurrentAudioComponent->OnAudioFinished.RemoveDynamic(this, &UADSAITextToSpeech::OnAudioFinished);
        CurrentAudioComponent = nullptr;
    }

    // If we were in PlayingAudio state, transition to Idle
    if (CurrentTTSState == EAITTSState::PlayingAudio)
    {
        SetTTSState(EAITTSState::Idle);
    }
}

bool UADSAITextToSpeech::IsAudioPlaying() const
{
    return CurrentAudioComponent.Get() && CurrentAudioComponent->IsPlaying();
}

void UADSAITextToSpeech::ClearCachedAudioData()
{
    CachedAudioData.Empty();
    CachedAudioText.Empty();
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Cleared cached audio data"));
}

bool UADSAITextToSpeech::PlayCachedAudioData()
{
    if (!HasCachedAudioData())
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("No cached audio data available to play"));
        return false;
    }

    if (IsTTSBusy())
    {
        UE_LOG(ADSAITextToSpeechLog, Warning, TEXT("TTS is busy - stopping current audio before playing cached data"));
        StopTTSAudio(false, 0.0f);
    }

    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Playing cached audio data (%d bytes) for text: %s"), 
        CachedAudioData.Num(), *CachedAudioText);

    SetTTSState(EAITTSState::PlayingAudio);
    PlayAudioFromBuffer(CachedAudioData, 16000, 1, true);
    
    return true;
}

void UADSAITextToSpeech::ClearAllLocalOverrides()
{
    VoiceType.Empty();
    LocalAITTSModel.Empty();
    LocalAITTSAPIEndpoint.Empty();
    LocalAITTSAPIKey.Empty();
    
    UE_LOG(ADSAITextToSpeechLog, Log, TEXT("Cleared all local TTS overrides - will now use global settings"));
}