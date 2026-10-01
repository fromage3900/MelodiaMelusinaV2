// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "GameplayTagContainer.h"

#include "ADSDialogueDeveloperSettings.generated.h"

class UADSVoiceConfigDataAsset;

UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Dialogue Settings"))
class ASCENTDIALOGUESYSTEM_API UADSDialogueDeveloperSettings : public UDeveloperSettings {

    GENERATED_BODY()

protected:
    UPROPERTY(EditAnywhere, config, Category = "Dialogue", meta = (DisplayPriority = 1))
    FGameplayTag DefaultPlayerResponseTag;

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation", meta = (PasswordField = true))
    FString TTSVoiceGenKey;

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation")
    FString TTSVoiceAPIModel = TEXT("eleven_multilingual_v2");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation")
    FString TTSVoiceSelectionAPIEndPoint = TEXT("https://api.elevenlabs.io/v2/voices");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation")
    FString TTSVoiceGenerationEndPoint = TEXT("https://api.elevenlabs.io/v1/text-to-speech");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation", meta = (RelativeToGameContentDir = true))
    FString DefaultTTSOutputPath = TEXT("Audio/TTS/");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation", meta = (RelativeToGameContentDir = true))
    FString FinalTTSPath = TEXT("Audio/TTS/Generated/");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation", meta = (RelativeToGameContentDir = true))
    FString PreviewSamplesPath = TEXT("Audio/TTS/Samples/");

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation")
    bool bAutoAssignGeneratedAudio = true;

    UPROPERTY(EditAnywhere, config, Category = "Voice Generation", meta = (AllowedClasses = "/Script/AscentDialogueSystem.ADSVoiceConfigDataAsset"))
    FSoftObjectPath VoiceConfigDataAsset;

    // Global API key for AI dialogue generation services (OpenAI, etc.)
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "AI API Key"), meta = (PasswordField = true))
    FString AIAPIKey;

    // Default API endpoint for AI dialogue generation
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "AI API Endpoint"))
    FString AIAPIEndpoint = "https://api.openai.com/v1/chat/completions";

    // Default AI model to use for dialogue generation
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "AI Model"))
    FString AIModel = "gpt-4o-mini";

    // Default maximum tokens for AI responses
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "Max Tokens", ClampMin = "1", ClampMax = "4096"))
    int32 MaxTokens = 150;

    // Customizable payload template with tag substitution
    // Available tags: {MODEL}, {MAX_TOKENS}, {SYSTEM_PROMPT}, {USER_MESSAGE}, {TEMPERATURE}
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "AI Payload Template", MultiLine = true))
    FString AIPayloadTemplate = TEXT("{\n  \"model\": \"{MODEL}\",\n  \"max_tokens\": {MAX_TOKENS},\n  \"temperature\": 0.7,\n  \"messages\": [\n    {\n      \"role\": \"system\",\n      \"content\": \"{SYSTEM_PROMPT}\"\n    },\n    {\n      \"role\": \"user\",\n      \"content\": \"{USER_MESSAGE}\"\n    }\n  ]\n}");

    // Customizable request headers template with tag substitution
    // Available tags: {API_KEY}, {ANTHROPIC_VERSION}
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "AI Request Headers", MultiLine = true))
    FString AIRequestHeaders = TEXT("Content-Type: application/json\nAuthorization: Bearer {API_KEY}");

    // Enable or disable AI dialogue functionality globally
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI", meta = (DisplayName = "Enable AI Dialogue"))
    bool bEnableAIDialogue = false;

    // Global API key for TTS services (OpenAI, etc.)
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS API Key"), meta = (PasswordField = true))
    FString TTSAPIKey;

    // Default API endpoint for TTS generation
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS API Endpoint"))
    FString TTSAPIEndpoint = "https://api.openai.com/v1/audio/speech";

    // Default TTS model to use
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS Model"))
    FString TTSModel = "tts-1";

    // Default TTS voice to use
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS Voice"))
    FString TTSVoice = "alloy";

    // Customizable TTS payload template with tag substitution
    // Available tags: {MODEL}, {INPUT}, {VOICE}, {RESPONSE_FORMAT}, {SPEED}
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS Payload Template", MultiLine = true))
    FString TTSPayloadTemplate = TEXT("{\n  \"model\": \"{MODEL}\",\n  \"input\": \"{INPUT}\",\n  \"voice\": \"{VOICE}\",\n  \"response_format\": \"wav\",\n  \"speed\": 1.0\n}");

    // Customizable TTS request headers template with tag substitution
    // Available tags: {API_KEY}
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "TTS Request Headers", MultiLine = true))
    FString TTSRequestHeaders = TEXT("Content-Type: application/json\nAuthorization: Bearer {API_KEY}");

    // Enable or disable TTS functionality globally
    UPROPERTY(EditAnywhere, config, Category = "Conversational AI|TTS", meta = (DisplayName = "Enable TTS"))
    bool bEnableTTS = false;

    // MetaHuman face SkeletalMesh used as visualization mesh when processing audio-driven animation
    UPROPERTY(EditAnywhere, config, Category = "Facial Animation", meta = (DisplayName = "Visualization Mesh", AllowedClasses = "/Script/Engine.SkeletalMesh"))
    FSoftObjectPath FacialAnimVisualizationMesh;

    // Output path for generated MetaHuman Performance and exported animation assets
    UPROPERTY(EditAnywhere, config, Category = "Facial Animation", meta = (DisplayName = "Output Path", RelativeToGameContentDir = true))
    FString FacialAnimationOutputPath = TEXT("Animation/FacialAnim/Generated/");

    // Existing MetaHumanPerformance asset to reuse for every generation (avoids creating one per node)
    UPROPERTY(EditAnywhere, config, Category = "Facial Animation", meta = (DisplayName = "Default MetaHuman Performance", AllowedClasses = "/Script/MetaHumanPerformance.MetaHumanPerformance"))
    FSoftObjectPath DefaultMetaHumanPerformance;

public:
    // Gets the default player response tag
    FGameplayTag GetDefaultPlayerResponseTag() const
    {
        return DefaultPlayerResponseTag;
    }

    FString GetTTSVoiceGenAPIKey() const
    {
        return TTSVoiceGenKey;
    }

    FString GetTTSVoiceModel() const
    {
        return TTSVoiceAPIModel;
    }

    FString GetTTSVoiceSelectionAPIEndPoint() const { return TTSVoiceSelectionAPIEndPoint; }
    FString GetTTSVoiceGenerationEndPoint() const { return TTSVoiceGenerationEndPoint; }

    UADSVoiceConfigDataAsset* GetVoiceConfigDataAsset() const;


    FString GetDefaultOutputPath() const
    {
        return DefaultTTSOutputPath;
    }

    FString GetFinalTTSPath() const
    {
        return FinalTTSPath;
    }

    FString GetPreviewSamplesPath() const
    {
        return PreviewSamplesPath;
    }

    bool GetAutoAssignGeneratedAudio() const
    {
        return bAutoAssignGeneratedAudio;
    }

    // Gets the global AI API key for dialogue generation
    FString GetAIAPIKey() const
    {
        return AIAPIKey;
    }

    // Gets the default AI API endpoint for dialogue generation
    FString GetAIAPIEndpoint() const
    {
        return AIAPIEndpoint;
    }

    // Gets the AI payload template with tag substitution
    FString GetAIPayloadTemplate() const
    {
        return AIPayloadTemplate;
    }

    // Gets the AI request headers template
    FString GetAIRequestHeaders() const
    {
        return AIRequestHeaders;
    }

    // Gets the default AI model to use
    FString GetAIModel() const
    {
        return AIModel;
    }

    // Gets the default maximum tokens for AI responses
    int32 GetMaxTokens() const
    {
        return MaxTokens;
    }

    // Gets whether AI dialogue is enabled globally
    bool IsAIDialogueEnabled() const
    {
        return bEnableAIDialogue;
    }

    // Gets the global TTS API key
    FString GetTTSAPIKey() const
    {
        return TTSAPIKey;
    }

    // Gets the default TTS API endpoint
    FString GetTTSAPIEndpoint() const
    {
        return TTSAPIEndpoint;
    }

    // Gets the TTS payload template with tag substitution
    FString GetTTSPayloadTemplate() const
    {
        return TTSPayloadTemplate;
    }

    // Gets the TTS request headers template
    FString GetTTSRequestHeaders() const
    {
        return TTSRequestHeaders;
    }

    // Gets the default TTS voice
    FString GetTTSVoice() const
    {
        return TTSVoice;
    }

    // Gets the default TTS model
    FString GetTTSModel() const
    {
        return TTSModel;
    }

    // Gets whether TTS is enabled globally
    bool IsTTSEnabled() const
    {
        return bEnableTTS;
    }

    FSoftObjectPath GetFacialAnimVisualizationMesh() const { return FacialAnimVisualizationMesh; }
    FString GetFacialAnimationOutputPath() const { return FacialAnimationOutputPath; }
    FSoftObjectPath GetDefaultMetaHumanPerformance() const { return DefaultMetaHumanPerformance; }

    // Processes the payload template by replacing tags with actual values
    UFUNCTION(BlueprintCallable, Category = "Conversational AI")
    FString ProcessPayloadTemplate(const FString& SystemPrompt, const FString& UserMessage, const FString& Model, int32 InMaxTokens) const;

    // Processes the headers template by replacing tags with actual values
    UFUNCTION(BlueprintCallable, Category = "Conversational AI")
    TMap<FString, FString> ProcessHeadersTemplate(const FString& APIKey) const;

    // Processes the TTS payload template by replacing tags with actual values
    UFUNCTION(BlueprintCallable, Category = "Conversational AI|TTS")
    FString ProcessTTSPayloadTemplate(const FString& Text, const FString& Voice, const FString& Model) const;

    // Processes the TTS headers template by replacing tags with actual values
    UFUNCTION(BlueprintCallable, Category = "Conversational AI|TTS")
    TMap<FString, FString> ProcessTTSHeadersTemplate(const FString& APIKey) const;


private:
    // Helper function to replace tags in templates
    FString ReplaceTags(const FString& Template, const TMap<FString, FString>& TagValues) const;
};
