// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSEditorSubsystem.h"

#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialoguePartecipantComponent.h"
#include "ADSDialogueSubsystem.h"
#include "ADSVoiceConfigDataAsset.h"
#include "ADSTypes.h"
#include "Widgets/SWindow.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSDialogueResponseNode.h"
#include "Graph/ADSStartDialogueNode.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "TimerManager.h"
#include "EditorAssetLibrary.h"
#include "Factories/SoundFactory.h"
#include "FileHelpers.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Graph/ADSGraphNode.h"
#include "HAL/PlatformFilemanager.h"
#include "HttpModule.h"
#include "IAssetTools.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Widgets/Notifications/SNotificationList.h"
#include <HttpFwd.h>
#include <Interfaces/IHttpRequest.h>
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundCue.h>
#include <Sound/SoundNodeWavePlayer.h>
#include <Sound/SoundWave.h>
#include "AGSGraph.h"
#include "EdNode_AGSGraphNode.h"
#include "EdGraph_AGSGraph.h"
#include "AssetGraphSchema_AGSGraph.h"
#include "Graph/ADSDialogueNode.h"
#include "DesktopPlatformModule.h"
#include "IDesktopPlatform.h"
#include "Framework/Application/SlateApplication.h"
#include "GameplayTagsManager.h"
#include "ScopedTransaction.h"
#include "Misc/MessageDialog.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "AssetRegistry/AssetRegistryModule.h"
#if WITH_ADS_METAHUMAN
#include "MetaHumanPerformance.h"
#include "MetaHumanPerformanceExportUtils.h"
#include "AudioDrivenAnimationConfig.h"
#include "AudioDrivenAnimationMood.h"
#endif // WITH_ADS_METAHUMAN

static FString SanitizeAssetName(const FString& Input, int32 MaxWords = 3, int32 MaxLen = 30)
{
    FString Result;
    int32 WordCount = 0;
    bool bPrevWasSpace = true;

    for (int32 i = 0; i < Input.Len(); ++i)
    {
        const TCHAR Ch = Input[i];
        if (FChar::IsWhitespace(Ch))
        {
            if (!bPrevWasSpace && WordCount < MaxWords)
            {
                Result += TEXT("_");
            }
            bPrevWasSpace = true;
            WordCount++;
            continue;
        }
        if (bPrevWasSpace)
        {
            bPrevWasSpace = false;
        }
        if (WordCount >= MaxWords) break;
        if (FChar::IsAlnum(Ch))
        {
            Result += Ch;
        }
    }
    if (Result.EndsWith(TEXT("_")))
    {
        Result.LeftChopInline(1);
    }
    if (Result.Len() > MaxLen)
    {
        Result.LeftInline(MaxLen);
    }
    return Result.IsEmpty() ? TEXT("FacialAnim") : Result;
}

UADSEditorSubsystem::UADSEditorSubsystem()
{
}

USoundWave* UADSEditorSubsystem::CreateSoundWaveAsset(const TArray<uint8>& AudioData, const FString& AssetName, const FString& PackagePath)
{
    if (AudioData.Num() == 0) {
        UE_LOG(LogTemp, Error, TEXT("Cannot create sound wave from empty audio data"));
        return nullptr;
    }

    // Create temporary file path
    const FString TempDir = FPaths::ProjectIntermediateDir() / TEXT("VoiceTTS");
    const FString TempFilePath = TempDir / (AssetName + TEXT(".mp3"));

    // Ensure directory exists
    IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
    if (!PlatformFile.DirectoryExists(*TempDir)) {
        PlatformFile.CreateDirectoryTree(*TempDir);
    }

    // Save MP3 data to temporary file
    if (!FFileHelper::SaveArrayToFile(AudioData, *TempFilePath)) {
        UE_LOG(LogTemp, Error, TEXT("Failed to save audio data to temp file: %s"), *TempFilePath);
        return nullptr;
    }

    // Create the full package path
    const FString FullPackagePath = PackagePath + AssetName;

    // Ensure the target directory exists in the content browser
    const FString ContentPath = FPaths::ProjectContentDir() + PackagePath.RightChop(6); // Remove "/Game/"
    if (!PlatformFile.DirectoryExists(*ContentPath)) {
        PlatformFile.CreateDirectoryTree(*ContentPath);
    }

    // Import using AssetTools with automated import data
    IAssetTools& AssetTools = FModuleManager::GetModuleChecked<FAssetToolsModule>("AssetTools").Get();

    UAutomatedAssetImportData* ImportData = NewObject<UAutomatedAssetImportData>();
    ImportData->bReplaceExisting = true;
    ImportData->Filenames.Add(TempFilePath);
    ImportData->DestinationPath = FPackageName::GetLongPackagePath(FullPackagePath);

    TArray<UObject*> ImportedAssets = AssetTools.ImportAssetsAutomated(ImportData);

    USoundWave* ImportedSoundWave = nullptr;
    if (ImportedAssets.Num() > 0) {
        ImportedSoundWave = Cast<USoundWave>(ImportedAssets[0]);
    }

    if (ImportedSoundWave) {
        UE_LOG(LogTemp, Log, TEXT("Successfully imported TTS audio as USoundWave: %s"), *FullPackagePath);

        // Clean up temporary file
        PlatformFile.DeleteFile(*TempFilePath);

        // Configure the sound wave properties
        ImportedSoundWave->bLooping = false;
        ImportedSoundWave->Volume = 1.0f;
        ImportedSoundWave->Pitch = 1.0f;

        return ImportedSoundWave;
    } else {
        UE_LOG(LogTemp, Error, TEXT("Failed to import audio file as USoundWave: %s"), *TempFilePath);

        // Clean up temporary file on failure
        PlatformFile.DeleteFile(*TempFilePath);

        return nullptr;
    }

    return nullptr;
}

USoundCue* UADSEditorSubsystem::CreateSoundCueFromWave(USoundWave* SoundWave, const FString& CueName)
{
    if (!SoundWave) {
        UE_LOG(LogTemp, Error, TEXT("Cannot create SoundCue: SoundWave is null"));
        return nullptr;
    }

    // Get the package path from the SoundWave
    const FString SoundWavePackagePath = SoundWave->GetPackage()->GetName();
    const FString CuePackagePath = SoundWavePackagePath + TEXT("_Cue");

    // Create the sound cue asset
    IAssetTools& AssetTools = FModuleManager::GetModuleChecked<FAssetToolsModule>("AssetTools").Get();

    USoundCue* SoundCue = Cast<USoundCue>(AssetTools.CreateAsset(CueName, FPackageName::GetLongPackagePath(CuePackagePath), USoundCue::StaticClass(), nullptr));

    if (!SoundCue) {
        UE_LOG(LogTemp, Error, TEXT("Failed to create USoundCue asset: %s"), *CueName);
        return nullptr;
    }

    // Create a USoundNodeWavePlayer node
    USoundNodeWavePlayer* WavePlayer = NewObject<USoundNodeWavePlayer>(SoundCue);
    if (!WavePlayer) {
        UE_LOG(LogTemp, Error, TEXT("Failed to create USoundNodeWavePlayer"));
        return nullptr;
    }

    WavePlayer->SetSoundWave(SoundWave);

    // Set up the sound cue properties
    SoundCue->FirstNode = WavePlayer;
    SoundCue->MaxDistance = 10000.0f;
    SoundCue->VolumeMultiplier = 1.0f;
    SoundCue->PitchMultiplier = 1.0f;

    // Reconstruct the cue safely without calling LinkGraphNodesFromSoundNodes
    SoundCue->PostEditChange();
    SoundCue->MarkPackageDirty();

    UE_LOG(LogTemp, Log, TEXT("Successfully created USoundCue: %s"), *SoundCue->GetName());

    return SoundCue;
}

void UADSEditorSubsystem::ShowNotification(const FString& Message, bool bSuccess /*= true*/) const
{
    FNotificationInfo Info(FText::FromString(Message));
    Info.ExpireDuration = 7.0f;
    Info.bFireAndForget = true;

    if (!bSuccess) {
        Info.Image = FCoreStyle::Get().GetBrush("NotificationList.FailImage");
    } else {
        Info.Image = FCoreStyle::Get().GetBrush("NotificationList.SuccessImage");
    }

    FSlateNotificationManager::Get().AddNotification(Info);
}

USoundWave* UADSEditorSubsystem::CreateSoundWaveFromAudioData(const TArray<uint8>& AudioData, const FString& SoundName)
{
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString PackagePath = TEXT("/Game/") + Settings->GetDefaultOutputPath();
    return CreateSoundWaveAsset(AudioData, SoundName, PackagePath);
}

void UADSEditorSubsystem::RefreshVoicesFromAPI()
{
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString APIKey = Settings->GetTTSVoiceGenAPIKey();

    if (APIKey.IsEmpty()) {
        UE_LOG(LogTemp, Warning, TEXT("No TTS Voice API key set - cannot refresh voices"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Refreshing voices from TTS Voice API..."));

    // Clear current cache
    if (UADSDialogueSubsystem* DialogueSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()) {
        // Clear current cache
        DialogueSubsystem->ClearVoiceCache();
    }

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(Settings->GetTTSVoiceSelectionAPIEndPoint());
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("xi-api-key"), APIKey);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindLambda([this, APIKey](FHttpRequestPtr HttpRequest, FHttpResponsePtr HttpResponse, bool bWasSuccessful) {
        if (bWasSuccessful && HttpResponse.IsValid() && HttpResponse->GetResponseCode() == 200) {
            FString ResponseString = HttpResponse->GetContentAsString();
            TSharedPtr<FJsonObject> JsonObject;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

            if (FJsonSerializer::Deserialize(Reader, JsonObject)) {
                const TArray<TSharedPtr<FJsonValue>>* VoicesArray;
                if (JsonObject->TryGetArrayField(TEXT("voices"), VoicesArray)) {
                    // Populate cache with real API data
                    TArray<FString> NewVoiceNames;
                    TMap<FString, FString> NewVoiceNameToID;

                    for (const auto& VoiceValue : *VoicesArray) {
                        const TSharedPtr<FJsonObject> VoiceObj = VoiceValue->AsObject();
                        if (VoiceObj.IsValid()) {
                            FString VoiceName;
                            FString VoiceId;

                            if (VoiceObj->TryGetStringField(TEXT("name"), VoiceName) && VoiceObj->TryGetStringField(TEXT("voice_id"), VoiceId)) {

                                NewVoiceNames.Add(VoiceName);
                                NewVoiceNameToID.Add(VoiceName, VoiceId);
                            }
                        }
                    }

                    if (UADSDialogueSubsystem* DialogueSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()) {
                        // Clear current cache
                        DialogueSubsystem->UpdateVoiceCache(NewVoiceNames, NewVoiceNameToID, APIKey);
                    }

                    UE_LOG(LogTemp, Log, TEXT("Successfully refreshed %d voices from TTS Voice API"), NewVoiceNames.Num());
                    UE_LOG(LogTemp, Log, TEXT("Reopen the Details Panel to see updated voice dropdown"));
                    ShowNotification("Voice Refreshed!", true);

                } else {
                    UE_LOG(LogTemp, Error, TEXT("No 'voices' array found in API response"));
                }
            } else {
                UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON response from TTS Voice API"));
            }
        } else {
            const FString ErrorMsg = HttpResponse.IsValid() ? FString::Printf(TEXT("HTTP %d"), HttpResponse->GetResponseCode()) : TEXT("Request failed");
            UE_LOG(LogTemp, Error, TEXT("Failed to refresh voices from TTS Voice API: %s"), *ErrorMsg);
            ShowNotification(ErrorMsg, false);
        }
    });

    // Start the async request
    Request->ProcessRequest();
}

void UADSEditorSubsystem::ClearVoiceCache()
{
    if (UADSDialogueSubsystem* DialogueSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()) {
        // Clear current cache
        DialogueSubsystem->ClearVoiceCache();
    }
    UE_LOG(LogTemp, Log, TEXT("TTS voice cache cleared"));
    ShowNotification("Voice cache cleared. Click 'Refresh Voices' to reload.", true);
}

void UADSEditorSubsystem::PreviewSelectedVoice(const FString& voiceId)
{
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString APIKey = Settings->GetTTSVoiceGenAPIKey();

    if (APIKey.IsEmpty()) {
        UE_LOG(LogTemp, Warning, TEXT("TTS Voice API Key not set in Project Settings"));
        return;
    }

    if (voiceId.IsEmpty()) {
        UE_LOG(LogTemp, Warning, TEXT("No Voice ID specified"));
        return;
    }

    // Make HTTP request to get voice preview
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(Settings->GetTTSVoiceSelectionAPIEndPoint());
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("xi-api-key"), APIKey);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindLambda([this, voiceId](FHttpRequestPtr HttpRequest, FHttpResponsePtr HttpResponse, bool bWasSuccessful) {
        if (bWasSuccessful && HttpResponse.IsValid() && HttpResponse->GetResponseCode() == 200) {
            const FString ResponseString = HttpResponse->GetContentAsString();
            TSharedPtr<FJsonObject> JsonObject;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

            if (FJsonSerializer::Deserialize(Reader, JsonObject)) {
                // Find the voice and get preview URL
                const TArray<TSharedPtr<FJsonValue>>* VoicesArray;
                if (JsonObject->TryGetArrayField(TEXT("voices"), VoicesArray)) {
                    for (const auto& VoiceValue : *VoicesArray) {
                        const TSharedPtr<FJsonObject> VoiceObj = VoiceValue->AsObject();
                        FString VoiceIdFromAPI;
                        if (VoiceObj->TryGetStringField(TEXT("voice_id"), VoiceIdFromAPI) && VoiceIdFromAPI == voiceId) {
                            FString PreviewURL;
                            if (VoiceObj->TryGetStringField(TEXT("preview_url"), PreviewURL)) {
                                // Download and play preview audio
                                DownloadAndPlayPreviewAudio(PreviewURL, voiceId);
                            } else {
                                UE_LOG(LogTemp, Warning, TEXT("No preview URL found for voice ID: %s"), *voiceId);
                            }
                            return;
                        }
                    }
                    UE_LOG(LogTemp, Warning, TEXT("Voice ID not found: %s"), *voiceId);
                }
            }
        } else {
            UE_LOG(LogTemp, Error, TEXT("Failed to fetch voice data for preview"));
            ShowNotification("Failed to fetch voice data for preview", false);
        }
    });

    Request->ProcessRequest();
}

void UADSEditorSubsystem::DownloadAndPlayPreviewAudio(const FString& PreviewURL, const FString& voiceID)
{
    // Generate cache file path based on voice ID

    const FString CachedFilePath = FPaths::ProjectIntermediateDir() / TEXT("TTSCache") / FString::Printf(TEXT("Preview_%s.mp3"), *voiceID);

    // First check if USoundWave asset already exists in samples folder
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    FString AssetName = FString::Printf(TEXT("Preview_%s"), *voiceID);
    FString AssetPath = FString::Printf(TEXT("/Game/%s%s"), *Settings->GetPreviewSamplesPath(), *AssetName);

    if (UObject* ExistingAsset = StaticLoadObject(USoundWave::StaticClass(), nullptr, *AssetPath)) {
        USoundWave* ExistingSoundWave = Cast<USoundWave>(ExistingAsset);
        if (ExistingSoundWave) {
            UE_LOG(LogTemp, Log, TEXT("Playing existing preview asset: %s"), *AssetPath);

            // Play existing asset directly
            if (UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr) {
                UGameplayStatics::PlaySound2D(World, ExistingSoundWave);
            }

            ShowNotification("Playing voice preview..", true);
            return;
        }
    }

    // Check if cached preview file exists
    if (FPaths::FileExists(CachedFilePath)) {
        UE_LOG(LogTemp, Log, TEXT("Playing cached voice preview from: %s"), *CachedFilePath);

        // Play cached file directly in Unreal
        PlayAudioFileInUnreal(CachedFilePath);
        ShowNotification("Playing voice preview..", true);
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Downloading voice preview from API..."));

    // Create HTTP request to download preview audio
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(PreviewURL);
    Request->SetVerb(TEXT("GET"));

    Request->OnProcessRequestComplete().BindLambda([this, CachedFilePath](FHttpRequestPtr HttpRequest, FHttpResponsePtr HttpResponse, bool bWasSuccessful) {
        if (bWasSuccessful && HttpResponse.IsValid() && HttpResponse->GetResponseCode() == 200) {
            TArray<uint8> AudioData = HttpResponse->GetContent();
            UE_LOG(LogTemp, Log, TEXT("Downloaded preview audio: %d bytes"), AudioData.Num());

            // Ensure cache directory exists
            FString CacheDir = FPaths::GetPath(CachedFilePath);
            IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
            if (!PlatformFile.DirectoryExists(*CacheDir)) {
                PlatformFile.CreateDirectoryTree(*CacheDir);
            }

            // Save to cached file path
            if (FFileHelper::SaveArrayToFile(AudioData, *CachedFilePath)) {
                UE_LOG(LogTemp, Log, TEXT("Cached and playing voice preview from: %s"), *CachedFilePath);

                // Play downloaded file in Unreal
                PlayAudioFileInUnreal(CachedFilePath);

                // Show notification

                ShowNotification("Playing voice preview..", true);

            } else {
                UE_LOG(LogTemp, Error, TEXT("Failed to save preview audio to cache file"));
            }
        } else {
            UE_LOG(LogTemp, Error, TEXT("Failed to download preview audio"));
            ShowNotification("Failed to download preview audio", false);
        }
    });

    Request->ProcessRequest();
}

void UADSEditorSubsystem::PlayAudioFileInUnreal(const FString& FilePath)
{
    // Load audio data from file
    TArray<uint8> AudioData;
    if (!FFileHelper::LoadFileToArray(AudioData, *FilePath)) {
        UE_LOG(LogTemp, Error, TEXT("Failed to load audio file: %s"), *FilePath);
        return;
    }

    // Create asset name for preview
    const FString FileName = FPaths::GetBaseFilename(FilePath);
    const FString AssetName = FString::Printf(TEXT("Preview_%s"), *FileName);

    // Use configurable preview samples path
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString PackagePath = TEXT("/Game/") + Settings->GetPreviewSamplesPath();

    // Create USoundWave asset
    USoundWave* PreviewSoundWave = CreateSoundWaveAsset(AudioData, AssetName, PackagePath);

    if (PreviewSoundWave) {
        // Play in editor world
        if (const UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr) {
            UGameplayStatics::PlaySound2D(World, PreviewSoundWave);
            UE_LOG(LogTemp, Log, TEXT("Playing preview audio in Unreal Engine: %s"), *PreviewSoundWave->GetName());
        }
    } else {
        UE_LOG(LogTemp, Error, TEXT("Failed to create preview audio asset from: %s"), *FilePath);
    }
}

void UADSEditorSubsystem::GenerateTTSAudio(UADSGraphNode* dialogueNode)
{
    // Thin wrapper around the shared core: surface every result (success or failure) as a notification.
    RequestTTSForNode(dialogueNode, [this](bool bSuccess, const FString& Message) {
        ShowNotification(Message, bSuccess);
    });
}

void UADSEditorSubsystem::RequestTTSForNode(UADSGraphNode* DialogueNode, TFunction<void(bool, const FString&)> OnComplete)
{
    // Guarantee the callback is always invoked exactly once, even on early-out paths.
    auto Fail = [&OnComplete](const FString& Message) {
        UE_LOG(LogTemp, Warning, TEXT("Generate TTS: %s"), *Message);
        if (OnComplete) {
            OnComplete(false, Message);
        }
    };

    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    if (!Settings) {
        Fail(TEXT("Dialogue developer settings are unavailable."));
        return;
    }

    const FString APIKey = Settings->GetTTSVoiceGenAPIKey();
    if (APIKey.IsEmpty()) {
        Fail(TEXT("TTS API Key not set in Project Settings."));
        return;
    }

    if (!DialogueNode) {
        Fail(TEXT("Dialogue node is null - cannot generate TTS audio."));
        return;
    }

    FADSVoiceSettings VoiceConfig;
    if (!DialogueNode->TryGetParticipantVoiceConfig(VoiceConfig)) {
        Fail(TEXT("Dialogue node has no voice config - assign a participant voice first."));
        return;
    }

    const FString UseVoiceID = VoiceConfig.GetSelectedVoiceID();
    if (UseVoiceID.IsEmpty()) {
        Fail(TEXT("No Voice ID specified for this node's participant."));
        return;
    }

    const FText Text = DialogueNode->GetDialogueText();
    if (Text.IsEmpty()) {
        Fail(TEXT("Node has no dialogue text to convert to speech."));
        return;
    }

    // Create JSON payload
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField(TEXT("text"), Text.ToString());
    JsonObject->SetStringField(TEXT("model_id"), Settings->GetTTSVoiceModel());

    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    const FString finalEndpoint = Settings->GetTTSVoiceGenerationEndPoint() + "/" + UseVoiceID;

    // Make HTTP request to generate TTS
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(finalEndpoint);
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("xi-api-key"), APIKey);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(JsonString);

    TWeakObjectPtr<UADSGraphNode> WeakNode(DialogueNode);

    Request->OnProcessRequestComplete().BindLambda([this, Settings, WeakNode, OnComplete](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful) {
        auto Report = [&OnComplete](bool bSuccess, const FString& Message) {
            if (bSuccess) {
                UE_LOG(LogTemp, Log, TEXT("Generate TTS: %s"), *Message);
            } else {
                UE_LOG(LogTemp, Error, TEXT("Generate TTS: %s"), *Message);
            }
            if (OnComplete) {
                OnComplete(bSuccess, Message);
            }
        };

        if (!(bWasSuccessful && Response.IsValid() && Response->GetResponseCode() == 200)) {
            const FString ErrorMsg = Response.IsValid()
                ? FString::Printf(TEXT("HTTP %d: %s"), Response->GetResponseCode(), *Response->GetContentAsString())
                : TEXT("Request failed (no response from TTS service).");
            Report(false, ErrorMsg);
            return;
        }

        UADSGraphNode* DialogueNode = WeakNode.Get();
        if (!DialogueNode) {
            Report(false, TEXT("Dialogue node was destroyed before TTS audio could be assigned."));
            return;
        }

        TArray<uint8> AudioData = Response->GetContent();
        if (AudioData.Num() == 0) {
            Report(false, TEXT("TTS service returned empty audio data."));
            return;
        }
        UE_LOG(LogTemp, Log, TEXT("Generated TTS audio: %d bytes"), AudioData.Num());

        const FGameplayTag PartecipantTag = DialogueNode->GetParticipantTag();
        FString ParticipantName = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(PartecipantTag);
        if (ParticipantName.IsEmpty() || ParticipantName == TEXT("None")) {
            ParticipantName = TEXT("Dialogue");
        }
        const FString TextSnippet = SanitizeAssetName(DialogueNode->GetDialogueText().ToString());
        const FString AssetName = FString::Printf(TEXT("TTS_%s_%s"), *ParticipantName, *TextSnippet);
        const FString PackagePath = TEXT("/Game/") + Settings->GetFinalTTSPath();

        USoundWave* NewSoundWave = CreateSoundWaveAsset(AudioData, AssetName, PackagePath);
        if (!NewSoundWave) {
            // Fallback: save to temp file so the generated audio isn't lost.
            const FString TempFilePath = FPaths::ProjectDir() / TEXT("Temp") / (AssetName + TEXT(".mp3"));
            if (FFileHelper::SaveArrayToFile(AudioData, *TempFilePath)) {
                UE_LOG(LogTemp, Log, TEXT("TTS audio saved to fallback file: %s"), *TempFilePath);
            }
            Report(false, FString::Printf(TEXT("Failed to import TTS audio as a SoundWave asset (%s)."), *AssetName));
            return;
        }

        if (Settings->GetAutoAssignGeneratedAudio()) {
            DialogueNode->SetSoundToPlay(NewSoundWave);
            // Mark the dialogue (the node's owning package) dirty so "Save All" picks up the change.
            DialogueNode->MarkPackageDirty();
        }
        if (NewSoundWave->GetPackage()) {
            NewSoundWave->GetPackage()->SetDirtyFlag(true);
        }

        Report(true, FString::Printf(TEXT("TTS Audio Generated: %s"), *AssetName));
    });

    Request->ProcessRequest();
}

void UADSEditorSubsystem::GenerateTTSAudioForAllNodes(UADSDialogue* Dialogue, bool bForceRegenerate)
{
    if (!Dialogue) {
        ShowNotification(TEXT("No dialogue selected."), false);
        UE_LOG(LogTemp, Warning, TEXT("Generate All TTS: dialogue is null."));
        return;
    }

    if (bIsBatchGeneratingVoices) {
        ShowNotification(TEXT("Voice generation already in progress. Please wait for it to finish."), false);
        return;
    }

    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    if (!Settings || Settings->GetTTSVoiceGenAPIKey().IsEmpty()) {
        ShowNotification(TEXT("TTS API Key not set in Project Settings."), false);
        UE_LOG(LogTemp, Warning, TEXT("Generate All TTS: missing API key or settings."));
        return;
    }

    // Collect every dialogue node that actually has text to voice (skipping already-voiced ones
    // unless the caller forces regeneration).
    TArray<TWeakObjectPtr<UADSGraphNode>> NodesToProcess;
    const int32 Skipped = CollectVoiceNodes({ Dialogue }, NodesToProcess, !bForceRegenerate);

    if (NodesToProcess.Num() == 0) {
        const FString Msg = Skipped > 0
            ? FString::Printf(TEXT("All %d dialogue nodes already have a voice. Use 'Force' to regenerate."), Skipped)
            : FString(TEXT("No dialogue nodes with text were found to generate voices for."));
        ShowNotification(Msg, false);
        UE_LOG(LogTemp, Warning, TEXT("Generate All TTS: no eligible nodes in '%s' (%d already set)."), *Dialogue->GetName(), Skipped);
        return;
    }

    // Warn the user that this can be expensive (one API call per node) before proceeding.
    FString ConfirmMsg = FString::Printf(
        TEXT("Generate TTS voices for %d dialogue node(s)%s?\n\n"
             "This sends one request per node to the TTS service and may take a while "
             "and consume API credits.\n\n"),
        NodesToProcess.Num(), bForceRegenerate ? TEXT(" (FORCE: regenerating already-voiced nodes)") : TEXT(""));
    if (Skipped > 0) {
        ConfirmMsg += FString::Printf(TEXT("%d node(s) already voiced will be skipped.\n\n"), Skipped);
    }
    ConfirmMsg += TEXT("Continue?");

    if (FMessageDialog::Open(EAppMsgType::YesNo, FText::FromString(ConfirmMsg)) != EAppReturnType::Yes) {
        return;
    }

    StartVoiceBatch(MoveTemp(NodesToProcess));
}

void UADSEditorSubsystem::GenerateAnimationsForAllNodes(UADSDialogue* Dialogue, bool bForceRegenerate)
{
    if (!Dialogue) {
        ShowNotification(TEXT("No dialogue selected."), false);
        UE_LOG(LogTemp, Warning, TEXT("Generate All Facial: dialogue is null."));
        return;
    }

    // Reuse the multi-dialogue batch path with a single-element selection.
    GenerateFacialAnimationForDialogues({ Dialogue }, bForceRegenerate);
}

int32 UADSEditorSubsystem::CollectVoiceNodes(const TArray<UADSDialogue*>& Dialogues, TArray<TWeakObjectPtr<UADSGraphNode>>& OutNodes, bool bSkipAlreadySet)
{
    int32 SkippedAlreadySet = 0;
    TSet<UADSGraphNode*> Seen;
    for (UADSDialogue* Dialogue : Dialogues) {
        if (!Dialogue) {
            continue;
        }
        for (UAGSGraphNode* Node : Dialogue->GetAllNodes()) {
            UADSGraphNode* DialogueNode = Cast<UADSGraphNode>(Node);
            if (!DialogueNode || DialogueNode->GetDialogueText().IsEmpty() || Seen.Contains(DialogueNode)) {
                continue;
            }
            Seen.Add(DialogueNode);
            if (bSkipAlreadySet && DialogueNode->GetSoundToPlay() != nullptr) {
                SkippedAlreadySet++;
                continue;
            }
            OutNodes.Add(DialogueNode);
        }
    }
    return SkippedAlreadySet;
}

void UADSEditorSubsystem::GenerateTTSForDialogues(const TArray<UADSDialogue*>& Dialogues, bool bForceRegenerate)
{
    if (bIsBatchGeneratingVoices) {
        ShowNotification(TEXT("Voice generation already in progress. Please wait for it to finish."), false);
        return;
    }

    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    if (!Settings || Settings->GetTTSVoiceGenAPIKey().IsEmpty()) {
        ShowNotification(TEXT("TTS API Key not set in Project Settings."), false);
        UE_LOG(LogTemp, Warning, TEXT("Generate TTS (selection): missing API key or settings."));
        return;
    }

    int32 ValidDialogues = 0;
    for (const UADSDialogue* Dialogue : Dialogues) {
        if (Dialogue) {
            ValidDialogues++;
        }
    }

    if (ValidDialogues == 0) {
        ShowNotification(TEXT("No valid dialogues selected."), false);
        return;
    }

    TArray<TWeakObjectPtr<UADSGraphNode>> NodesToProcess;
    const int32 Skipped = CollectVoiceNodes(Dialogues, NodesToProcess, !bForceRegenerate);

    if (NodesToProcess.Num() == 0) {
        const FString Msg = Skipped > 0
            ? FString::Printf(TEXT("All %d dialogue nodes in the selection already have a voice. Use 'Force' to regenerate."), Skipped)
            : FString(TEXT("No dialogue nodes with text were found in the selected dialogues."));
        ShowNotification(Msg, false);
        UE_LOG(LogTemp, Warning, TEXT("Generate TTS (selection): no eligible nodes (%d already set)."), Skipped);
        return;
    }

    FString ConfirmMsg = FString::Printf(
        TEXT("Generate TTS voices for %d dialogue node(s) across %d selected dialogue(s)%s?\n\n"
             "This sends one request per node to the TTS service and may take a while "
             "and consume API credits.\n\n"),
        NodesToProcess.Num(), ValidDialogues, bForceRegenerate ? TEXT(" (FORCE: regenerating already-voiced nodes)") : TEXT(""));
    if (Skipped > 0) {
        ConfirmMsg += FString::Printf(TEXT("%d node(s) already voiced will be skipped.\n\n"), Skipped);
    }
    ConfirmMsg += TEXT("Continue?");

    if (FMessageDialog::Open(EAppMsgType::YesNo, FText::FromString(ConfirmMsg)) != EAppReturnType::Yes) {
        return;
    }

    StartVoiceBatch(MoveTemp(NodesToProcess));
}

void UADSEditorSubsystem::StartVoiceBatch(TArray<TWeakObjectPtr<UADSGraphNode>> NodesToProcess)
{
    if (NodesToProcess.Num() == 0) {
        return;
    }

    // Persistent "In Progress" notification with throbber, updated as the batch runs.
    FNotificationInfo ProgressInfo(FText::FromString(TEXT("Generating voices... (0 / ") + FString::FromInt(NodesToProcess.Num()) + TEXT(")")));
    ProgressInfo.bFireAndForget = false;
    ProgressInfo.bUseThrobber = true;
    ProgressInfo.FadeOutDuration = 0.5f;
    ProgressInfo.ExpireDuration = 0.0f;
    TSharedPtr<SNotificationItem> ProgressNotification = FSlateNotificationManager::Get().AddNotification(ProgressInfo);
    if (ProgressNotification.IsValid()) {
        ProgressNotification->SetCompletionState(SNotificationItem::CS_Pending);
    }

    bIsBatchGeneratingVoices = true;

    // Shared state carried across the sequential async chain. The Step closure is stored here
    // and captures the state weakly to avoid a reference cycle; the per-request completion
    // callbacks capture the state strongly, which keeps it alive across each async HTTP wait.
    struct FBatchState
    {
        TArray<TWeakObjectPtr<UADSGraphNode>> Nodes;
        int32 Index = 0;
        int32 SuccessCount = 0;
        int32 FailCount = 0;
        int32 SkippedAnswerCount = 0; // answer (button) nodes without a voice config — not an error
        TSharedPtr<SNotificationItem> Notification;
        TFunction<void()> Step;
    };

    TSharedRef<FBatchState> State = MakeShared<FBatchState>();
    State->Nodes = MoveTemp(NodesToProcess);
    State->Notification = ProgressNotification;

    TWeakPtr<FBatchState> WeakState = State;

    // Processes exactly one node, then schedules itself again from the completion callback.
    State->Step = [this, WeakState]() {
        TSharedPtr<FBatchState> S = WeakState.Pin();
        if (!S.IsValid()) {
            return;
        }

        const int32 Total = S->Nodes.Num();

        if (S->Index >= Total) {
            // Batch finished: report a summary and clear the in-progress state.
            bIsBatchGeneratingVoices = false;

            const bool bAllOk = (S->FailCount == 0);
            FString Summary = FString::Printf(
                TEXT("Voice generation complete: %d succeeded, %d failed (of %d)."),
                S->SuccessCount, S->FailCount, Total);
            if (S->SkippedAnswerCount > 0) {
                Summary += FString::Printf(TEXT(" %d answer node(s) without voice config skipped."), S->SkippedAnswerCount);
            }

            if (S->Notification.IsValid()) {
                S->Notification->SetCompletionState(bAllOk ? SNotificationItem::CS_Success : SNotificationItem::CS_Fail);
                S->Notification->SetText(FText::FromString(Summary));
                S->Notification->ExpireAndFadeout();
            }
            // Separate persistent notification so the summary stays readable after the throbber fades.
            ShowNotification(Summary, bAllOk);
            UE_LOG(LogTemp, Log, TEXT("Generate All TTS: %s"), *Summary);
            return;
        }

        if (S->Notification.IsValid()) {
            S->Notification->SetText(FText::FromString(
                FString::Printf(TEXT("Generating voices... (%d / %d)"), S->Index + 1, Total)));
        }

        UADSGraphNode* Node = S->Nodes[S->Index].Get();
        if (!Node) {
            // Node went away between collection and processing - count as failure and continue.
            S->FailCount++;
            const FString Msg = FString::Printf(TEXT("Voice batch (%d/%d): node was destroyed before processing — skipped."), S->Index + 1, Total);
            UE_LOG(LogTemp, Warning, TEXT("Generate All TTS: %s"), *Msg);
            ShowNotification(Msg, false);
            S->Index++;
            S->Step();
            return;
        }

        // Answer (button) nodes without a voice config are not an error: they are
        // player choice buttons and simply don't need audio. Skip them silently.
        if (Node->IsA<UADSDialogueResponseNode>()) {
            FADSVoiceSettings AnswerVoiceCfg;
            if (!Node->TryGetParticipantVoiceConfig(AnswerVoiceCfg) || AnswerVoiceCfg.GetSelectedVoiceID().IsEmpty()) {
                UE_LOG(LogTemp, Log, TEXT("Generate All TTS: answer node (%d/%d) has no voice config — skipped (not an error)."), S->Index + 1, Total);
                S->SkippedAnswerCount++;
                S->Index++;
                S->Step();
                return;
            }
        }

        // Identify the node in error messages (participant + text snippet)
        FString NodeLabel = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(Node->GetParticipantTag());
        const FString NodeText = Node->GetDialogueText().ToString().Left(40);
        if (NodeLabel.IsEmpty() || NodeLabel == TEXT("None")) {
            NodeLabel = TEXT("Unknown");
        }

        // Strong capture of S keeps the batch state alive while the request is in flight.
        RequestTTSForNode(Node, [this, S, NodeLabel, NodeText](bool bSuccess, const FString& Message) {
            if (bSuccess) {
                S->SuccessCount++;
            } else {
                S->FailCount++;
                const FString Msg = FString::Printf(TEXT("Voice batch (%d/%d) failed — %s: \"%s...\"\n%s"),
                    S->Index + 1, S->Nodes.Num(), *NodeLabel, *NodeText, *Message);
                UE_LOG(LogTemp, Warning, TEXT("Generate All TTS: %s"), *Msg);
                ShowNotification(Msg, false);
            }
            S->Index++;
            S->Step();
        });
    };

    State->Step();
}

void UADSEditorSubsystem::FetchVoicesAsync() const
{
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString APIKey = Settings->GetTTSVoiceGenAPIKey();

    if (APIKey.IsEmpty()) {
        UE_LOG(LogTemp, Warning, TEXT("No TTS Voice API key set - cannot fetch voices"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Starting async voice fetch from TTS Voice API..."));

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(Settings->GetTTSVoiceSelectionAPIEndPoint());
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("xi-api-key"), APIKey);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindLambda([](FHttpRequestPtr HttpRequest, FHttpResponsePtr HttpResponse, bool bWasSuccessful) {
        if (bWasSuccessful && HttpResponse.IsValid() && HttpResponse->GetResponseCode() == 200) {
            FString ResponseString = HttpResponse->GetContentAsString();
            TSharedPtr<FJsonObject> JsonObject;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

            if (FJsonSerializer::Deserialize(Reader, JsonObject)) {
                // Get access to the global cache (same statics as in GetAvailableVoiceNames)
                const TArray<TSharedPtr<FJsonValue>>* VoicesArray;
                if (JsonObject->TryGetArrayField(TEXT("voices"), VoicesArray)) {

                    UE_LOG(LogTemp, Log, TEXT("Successfully fetched %d voices from TTS Voice API"), VoicesArray->Num());

                    // Note: The cache update needs to happen in GetAvailableVoiceNames function
                    // since that's where the static variables are declared
                    // For now, just log success - user will need to reopen Details Panel to see voices

                } else {
                    UE_LOG(LogTemp, Error, TEXT("No 'voices' array found in API response"));
                }
            } else {
                UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON response from TTS Voice API"));
            }
        } else {
            const FString ErrorMsg = HttpResponse.IsValid() ? FString::Printf(TEXT("HTTP %d"), HttpResponse->GetResponseCode()) : TEXT("Request failed");
            UE_LOG(LogTemp, Error, TEXT("Failed to fetch voices from TTS Voice API: %s"), *ErrorMsg);
        }
    });

    // Start the async request
    Request->ProcessRequest();
}

void UADSEditorSubsystem::FetchVoicesFromAPI(TArray<FString>& OutVoiceNames, TMap<FString, FString>& OutVoiceNameToID) const
{
    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString APIKey = Settings->GetTTSVoiceGenAPIKey();

    if (APIKey.IsEmpty()) {
        UE_LOG(LogTemp, Warning, TEXT("No TTS Voice API key set - cannot fetch voices"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Fetching voices from TTS Voice API..."));

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();

    Request->SetURL(Settings->GetTTSVoiceSelectionAPIEndPoint());
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("xi-api-key"), APIKey);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    // Keep request alive with shared pointer
    TSharedPtr<IHttpRequest> RequestPtr = Request;

    Request->OnProcessRequestComplete().BindLambda([&OutVoiceNames, &OutVoiceNameToID, RequestPtr](FHttpRequestPtr HttpRequest, FHttpResponsePtr HttpResponse, bool bWasSuccessful) {
        if (bWasSuccessful && HttpResponse.IsValid() && HttpResponse->GetResponseCode() == 200) {
            FString ResponseString = HttpResponse->GetContentAsString();
            TSharedPtr<FJsonObject> JsonObject;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

            if (FJsonSerializer::Deserialize(Reader, JsonObject)) {
                const TArray<TSharedPtr<FJsonValue>>* VoicesArray;
                if (JsonObject->TryGetArrayField(TEXT("voices"), VoicesArray)) {
                    for (const auto& VoiceValue : *VoicesArray) {
                        const TSharedPtr<FJsonObject> VoiceObj = VoiceValue->AsObject();
                        if (VoiceObj.IsValid()) {
                            FString VoiceName;
                            FString VoiceId;

                            if (VoiceObj->TryGetStringField(TEXT("name"), VoiceName) && VoiceObj->TryGetStringField(TEXT("voice_id"), VoiceId)) {

                                OutVoiceNames.Add(VoiceName);
                                OutVoiceNameToID.Add(VoiceName, VoiceId);
                            }
                        }
                    }
                    UE_LOG(LogTemp, Log, TEXT("Successfully fetched %d voices from TTS Voice API"), OutVoiceNames.Num());
                } else {
                    UE_LOG(LogTemp, Error, TEXT("No 'voices' array found in API response"));
                }
            } else {
                UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON response from TTS Voice API"));
            }
        } else {
            FString ErrorMsg = HttpResponse.IsValid() ? FString::Printf(TEXT("HTTP %d"), HttpResponse->GetResponseCode()) : TEXT("Request failed");
            UE_LOG(LogTemp, Error, TEXT("Failed to fetch voices from TTS Voice API: %s"), *ErrorMsg);
        }
    });

    // Start the request
    Request->ProcessRequest();

    // For now, provide some fallback voices so the dropdown isn't empty while request processes
    if (OutVoiceNames.Num() == 0) {
        UE_LOG(LogTemp, Warning, TEXT("Using fallback voices while API request processes..."));
        OutVoiceNames.Add(TEXT("Loading voices from TTS..."));
        OutVoiceNameToID.Add(TEXT("Loading voices from TTS..."), TEXT(""));
    }
}

// ============================================================================
// Facial Animation Generation (MetaHuman Animator)
// ============================================================================

#if WITH_ADS_METAHUMAN
bool UADSEditorSubsystem::GenerateFacialAnimationForNode(UADSGraphNode* DialogueNode, FString& OutMessage)
{
    if (!DialogueNode)
    {
        OutMessage = TEXT("No dialogue node selected");
        return false;
    }

    USoundWave* SoundWave = Cast<USoundWave>(DialogueNode->GetSoundToPlay());
    if (!SoundWave)
    {
        OutMessage = TEXT("Node has no SoundWave assigned. Generate TTS audio first.");
        return false;
    }

    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
    const FString OutputPath = TEXT("/Game/") + Settings->GetFacialAnimationOutputPath();

    IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
    const FString ContentPath = FPaths::ProjectContentDir() + Settings->GetFacialAnimationOutputPath();
    if (!PlatformFile.DirectoryExists(*ContentPath))
    {
        PlatformFile.CreateDirectoryTree(*ContentPath);
    }

    FString ParticipantName = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(DialogueNode->GetParticipantTag());
    if (ParticipantName.IsEmpty() || ParticipantName == TEXT("None"))
    {
        ParticipantName = TEXT("Dialogue");
    }

    const FString TextSnippet = SanitizeAssetName(DialogueNode->GetDialogueText().ToString());
    const FString BaseName = FString::Printf(TEXT("%s_%s"), *ParticipantName, *TextSnippet);

    UMetaHumanPerformance* Performance = Cast<UMetaHumanPerformance>(
        Settings->GetDefaultMetaHumanPerformance().TryLoad());

    const bool bIsReused = (Performance != nullptr);
    if (!Performance)
    {
        Performance = NewObject<UMetaHumanPerformance>(
            GetTransientPackage(), NAME_None, RF_Transient);
    }

    Performance->InputType = EDataInputType::Audio;
    Performance->Audio = SoundWave;
    Performance->bGenerateBlinks = DialogueNode->GetGenerateBlink();

    static const TMap<EADSFacialAnimMood, EAudioDrivenAnimationMood> MoodMapping = {
        { EADSFacialAnimMood::AutoDetect,  EAudioDrivenAnimationMood::AutoDetect },
        { EADSFacialAnimMood::Neutral,     EAudioDrivenAnimationMood::Neutral },
        { EADSFacialAnimMood::Happiness,   EAudioDrivenAnimationMood::Happiness },
        { EADSFacialAnimMood::Sadness,     EAudioDrivenAnimationMood::Sadness },
        { EADSFacialAnimMood::Disgust,     EAudioDrivenAnimationMood::Disgust },
        { EADSFacialAnimMood::Anger,       EAudioDrivenAnimationMood::Anger },
        { EADSFacialAnimMood::Surprise,    EAudioDrivenAnimationMood::Surprise },
        { EADSFacialAnimMood::Fear,        EAudioDrivenAnimationMood::Fear },
        { EADSFacialAnimMood::Confidence,  EAudioDrivenAnimationMood::Confidence },
        { EADSFacialAnimMood::Excitement,  EAudioDrivenAnimationMood::Excitement },
        { EADSFacialAnimMood::Boredom,     EAudioDrivenAnimationMood::Boredom },
        { EADSFacialAnimMood::Playfulness, EAudioDrivenAnimationMood::Playfulness },
        { EADSFacialAnimMood::Confusion,   EAudioDrivenAnimationMood::Confusion },
    };

    FAudioDrivenAnimationSolveOverrides& SolveOverrides = Performance->AudioDrivenAnimationSolveOverrides;
    const EAudioDrivenAnimationMood* FoundMood = MoodMapping.Find(DialogueNode->GetFacialAnimMood());
    SolveOverrides.Mood = FoundMood ? *FoundMood : EAudioDrivenAnimationMood::AutoDetect;
    SolveOverrides.MoodIntensity = DialogueNode->GetFacialAnimMoodIntensity();

    USkeletalMesh* VisMesh = Cast<USkeletalMesh>(Settings->GetFacialAnimVisualizationMesh().TryLoad());
    if (VisMesh)
    {
        Performance->VisualizationMesh = VisMesh;
    }

    // Trigger internal frame range recalculation by simulating Audio property change
    {
        FProperty* AudioProp = UMetaHumanPerformance::StaticClass()->FindPropertyByName(
            GET_MEMBER_NAME_CHECKED(UMetaHumanPerformance, Audio));
        FPropertyChangedEvent AudioChangedEvent(AudioProp);
        Performance->PostEditChangeProperty(AudioChangedEvent);
    }

    UE_LOG(LogTemp, Log, TEXT("MetaHuman Animator: Audio duration=%.2fs, FrameRange=[%u, %u], Audio=%s, VisMesh=%s"),
        SoundWave->Duration,
        Performance->StartFrameToProcess,
        Performance->EndFrameToProcess,
        *SoundWave->GetName(),
        VisMesh ? *VisMesh->GetName() : TEXT("null"));

    Performance->SetBlockingProcessing(true);

    if (!Performance->CanProcess())
    {
        const FText Reason = Performance->GetCannotProcessTooltipText();
        OutMessage = FString::Printf(TEXT("MetaHuman Animator cannot process: %s"), *Reason.ToString());
        UE_LOG(LogTemp, Error, TEXT("MetaHuman Animator CanProcess() == false: %s"), *Reason.ToString());
        return false;
    }

    const EStartPipelineErrorType StartError = Performance->StartPipeline(true);

    if (StartError != EStartPipelineErrorType::None)
    {
        OutMessage = TEXT("MetaHuman Animator: Pipeline failed");
        UE_LOG(LogTemp, Error, TEXT("MetaHuman Animator StartPipeline failed with error %d"), static_cast<int32>(StartError));
        return false;
    }

    if (!Performance->ContainsAnimationData())
    {
        OutMessage = TEXT("MetaHuman Animator: No animation data generated");
        return false;
    }

    if (bIsReused)
    {
        Performance->MarkPackageDirty();
    }

    UMetaHumanPerformanceExportAnimationSettings* ExportSettings =
        NewObject<UMetaHumanPerformanceExportAnimationSettings>();

    ExportSettings->bShowExportDialog = false;
    ExportSettings->bAutoSaveAnimSequence = true;
    ExportSettings->PackagePath = OutputPath;
    ExportSettings->AssetName = FString::Printf(TEXT("FacialAnim_%s"), *BaseName);

    if (VisMesh)
    {
        ExportSettings->TargetSkeletonOrSkeletalMesh = VisMesh;
    }

    UAnimSequence* ExportedSequence = UMetaHumanPerformanceExportUtils::ExportAnimationSequence(Performance, ExportSettings);

    if (ExportedSequence)
    {
        DialogueNode->SetFacialAnimation(nullptr);

        const FString MontageName = FString::Printf(TEXT("FacialAnim_%s_Montage"), *BaseName);
        const FString MontagePackagePath = OutputPath + MontageName;
        UPackage* MontagePackage = CreatePackage(*MontagePackagePath);
        MontagePackage->FullyLoad();

        UAnimMontage* Montage = NewObject<UAnimMontage>(
            MontagePackage, FName(*MontageName), RF_Public | RF_Standalone);
        Montage->SetSkeleton(ExportedSequence->GetSkeleton());

        Montage->SlotAnimTracks.Empty();
        FSlotAnimationTrack& SlotTrack = Montage->SlotAnimTracks.AddDefaulted_GetRef();
        SlotTrack.SlotName = FName("DefaultSlot");

        FAnimSegment& Segment = SlotTrack.AnimTrack.AnimSegments.AddDefaulted_GetRef();
        Segment.SetAnimReference(ExportedSequence, true);
        Segment.AnimStartTime = 0.0f;
        Segment.AnimEndTime = ExportedSequence->GetPlayLength();
        Segment.AnimPlayRate = 1.0f;
        Segment.StartPos = 0.0f;
        Segment.LoopingCount = 1;

        Montage->CompositeSections.Empty();
        FCompositeSection& Section = Montage->CompositeSections.AddDefaulted_GetRef();
        Section.SectionName = FName("Default");

        Montage->InvalidateRecursiveAsset();
        Montage->PostEditChange();
        Montage->MarkPackageDirty();
        FAssetRegistryModule::AssetCreated(Montage);

        DialogueNode->SetFacialAnimation(Montage);
        // Mark the dialogue (the node's owning package) dirty so "Save All" picks up the change.
        DialogueNode->MarkPackageDirty();

        OutMessage = FString::Printf(TEXT("Facial Animation Generated: %s"), *MontageName);
        UE_LOG(LogTemp, Log, TEXT("MetaHuman Animator: Generated facial animation %s"), *MontageName);
        return true;
    }

    OutMessage = TEXT("MetaHuman Animator: Export failed");
    return false;
}

void UADSEditorSubsystem::GenerateFacialAnimation(UADSGraphNode* DialogueNode)
{
    // Show a pending notification, run the (blocking) core, then resolve the notification.
    FNotificationInfo LoadingInfo(FText::FromString(TEXT("MetaHuman Animator: Generating facial animation...")));
    LoadingInfo.bFireAndForget = false;
    LoadingInfo.bUseThrobber = true;
    LoadingInfo.FadeOutDuration = 0.5f;
    LoadingInfo.ExpireDuration = 0.0f;
    TSharedPtr<SNotificationItem> LoadingNotification = FSlateNotificationManager::Get().AddNotification(LoadingInfo);
    if (LoadingNotification.IsValid())
    {
        LoadingNotification->SetCompletionState(SNotificationItem::CS_Pending);
    }

    FString Message;
    const bool bSuccess = GenerateFacialAnimationForNode(DialogueNode, Message);

    if (LoadingNotification.IsValid())
    {
        LoadingNotification->SetCompletionState(bSuccess ? SNotificationItem::CS_Success : SNotificationItem::CS_Fail);
        LoadingNotification->SetText(FText::FromString(Message));
        LoadingNotification->ExpireAndFadeout();
    }
}

void UADSEditorSubsystem::GenerateFacialAnimationForDialogues(const TArray<UADSDialogue*>& Dialogues, bool bForceRegenerate)
{
    if (bIsBatchGeneratingFacialAnims)
    {
        ShowNotification(TEXT("Facial animation generation already in progress. Please wait for it to finish."), false);
        return;
    }

    // Collect every node that already has a SoundWave assigned (facial anim is audio-driven).
    // Nodes that already have a facial animation are skipped unless regeneration is forced.
    TArray<TWeakObjectPtr<UADSGraphNode>> NodesToProcess;
    int32 ValidDialogues = 0;
    int32 NodesMissingAudio = 0;
    int32 SkippedAlreadySet = 0;
    {
        TSet<UADSGraphNode*> Seen;
        for (UADSDialogue* Dialogue : Dialogues)
        {
            if (!Dialogue)
            {
                continue;
            }
            ValidDialogues++;
            for (UAGSGraphNode* Node : Dialogue->GetAllNodes())
            {
                UADSGraphNode* DialogueNode = Cast<UADSGraphNode>(Node);
                if (!DialogueNode || Seen.Contains(DialogueNode))
                {
                    continue;
                }
                Seen.Add(DialogueNode);
                if (Cast<USoundWave>(DialogueNode->GetSoundToPlay()))
                {
                    if (!bForceRegenerate && DialogueNode->GetFacialAnimation() != nullptr)
                    {
                        SkippedAlreadySet++;
                        continue;
                    }
                    NodesToProcess.Add(DialogueNode);
                }
                else if (!DialogueNode->GetDialogueText().IsEmpty())
                {
                    NodesMissingAudio++;
                }
            }
        }
    }

    if (ValidDialogues == 0)
    {
        ShowNotification(TEXT("No valid dialogues selected."), false);
        return;
    }

    if (NodesToProcess.Num() == 0)
    {
        const FString Msg = SkippedAlreadySet > 0
            ? FString::Printf(TEXT("All %d eligible node(s) already have a facial animation. Use 'Force' to regenerate."), SkippedAlreadySet)
            : FString(TEXT("No nodes with a SoundWave were found. Generate TTS audio first."));
        ShowNotification(Msg, false);
        UE_LOG(LogTemp, Warning, TEXT("Generate Facial (selection): no eligible nodes (%d missing audio, %d already set)."), NodesMissingAudio, SkippedAlreadySet);
        return;
    }

    FString ConfirmMsg = FString::Printf(
        TEXT("Generate MetaHuman facial animation for %d node(s) across %d selected dialogue(s)%s?\n\n"
             "Each node is processed sequentially (the MetaHuman pipeline is blocking) and the "
             "editor may be unresponsive while it runs.\n\n"),
        NodesToProcess.Num(), ValidDialogues, bForceRegenerate ? TEXT(" (FORCE: regenerating existing animations)") : TEXT(""));
    if (SkippedAlreadySet > 0)
    {
        ConfirmMsg += FString::Printf(TEXT("%d node(s) already animated will be skipped.\n\n"), SkippedAlreadySet);
    }
    if (NodesMissingAudio > 0)
    {
        ConfirmMsg += FString::Printf(TEXT("%d node(s) without audio will be skipped.\n\n"), NodesMissingAudio);
    }
    ConfirmMsg += TEXT("Continue?");

    if (FMessageDialog::Open(EAppMsgType::YesNo, FText::FromString(ConfirmMsg)) != EAppReturnType::Yes)
    {
        return;
    }

    // Progress notification, advanced one node per editor tick so the UI stays responsive
    // between (blocking) solves.
    FNotificationInfo ProgressInfo(FText::FromString(
        FString::Printf(TEXT("Generating facial animations... (0 / %d)"), NodesToProcess.Num())));
    ProgressInfo.bFireAndForget = false;
    ProgressInfo.bUseThrobber = true;
    ProgressInfo.FadeOutDuration = 0.5f;
    ProgressInfo.ExpireDuration = 0.0f;
    TSharedPtr<SNotificationItem> ProgressNotification = FSlateNotificationManager::Get().AddNotification(ProgressInfo);
    if (ProgressNotification.IsValid())
    {
        ProgressNotification->SetCompletionState(SNotificationItem::CS_Pending);
    }

    bIsBatchGeneratingFacialAnims = true;

    struct FFacialBatchState
    {
        TArray<TWeakObjectPtr<UADSGraphNode>> Nodes;
        int32 Index = 0;
        int32 SuccessCount = 0;
        int32 FailCount = 0;
        TSharedPtr<SNotificationItem> Notification;
        TFunction<void()> Step;
    };

    TSharedRef<FFacialBatchState> State = MakeShared<FFacialBatchState>();
    State->Nodes = MoveTemp(NodesToProcess);
    State->Notification = ProgressNotification;

    TWeakPtr<FFacialBatchState> WeakState = State;

    State->Step = [this, WeakState]()
    {
        TSharedPtr<FFacialBatchState> S = WeakState.Pin();
        if (!S.IsValid())
        {
            return;
        }

        const int32 Total = S->Nodes.Num();

        if (S->Index >= Total)
        {
            bIsBatchGeneratingFacialAnims = false;

            const bool bAllOk = (S->FailCount == 0);
            const FString Summary = FString::Printf(
                TEXT("Facial animation complete: %d succeeded, %d failed (of %d)."),
                S->SuccessCount, S->FailCount, Total);

            if (S->Notification.IsValid())
            {
                S->Notification->SetCompletionState(bAllOk ? SNotificationItem::CS_Success : SNotificationItem::CS_Fail);
                S->Notification->SetText(FText::FromString(Summary));
                S->Notification->ExpireAndFadeout();
            }
            UE_LOG(LogTemp, Log, TEXT("Generate Facial (selection): %s"), *Summary);
            return;
        }

        if (S->Notification.IsValid())
        {
            S->Notification->SetText(FText::FromString(
                FString::Printf(TEXT("Generating facial animations... (%d / %d)"), S->Index + 1, Total)));
        }

        UADSGraphNode* Node = S->Nodes[S->Index].Get();
        FString Message;
        const bool bSuccess = Node ? GenerateFacialAnimationForNode(Node, Message) : false;
        if (bSuccess)
        {
            S->SuccessCount++;
        }
        else
        {
            S->FailCount++;
            UE_LOG(LogTemp, Warning, TEXT("Generate Facial (selection): node %d failed: %s"), S->Index, *Message);
        }
        S->Index++;

        // Defer the next (blocking) node to the next tick so the progress notification repaints.
        // The timer lambda captures the shared state strongly so it stays alive across ticks
        // (the kick-off TSharedRef in GenerateFacialAnimationForDialogues is gone by now). Once
        // the batch finishes it stops rescheduling, so the last lambda releases the final ref.
        if (GEditor)
        {
            GEditor->GetTimerManager()->SetTimerForNextTick([S]()
            {
                S->Step();
            });
        }
        else
        {
            S->Step();
        }
    };

    State->Step();
}
#else
void UADSEditorSubsystem::GenerateFacialAnimation(UADSGraphNode* DialogueNode)
{
    ShowNotification(TEXT("Facial animation generation requires the MetaHuman plugin, which is only available on Windows/Linux."), false);
}

void UADSEditorSubsystem::GenerateFacialAnimationForDialogues(const TArray<UADSDialogue*>& Dialogues, bool bForceRegenerate)
{
    ShowNotification(TEXT("Facial animation generation requires the MetaHuman plugin, which is only available on Windows/Linux."), false);
}
#endif // WITH_ADS_METAHUMAN

// ============================================================================
// Dialogue Export/Import
// ============================================================================

namespace ADSExportHelper
{
    /**
     * Recursively traverses dialogue nodes in DFS order and appends screenplay-formatted text.
     * Response nodes (player choices) are output as "(Option N)" variants.
     */
    static void ExportNodeRecursive(UADSGraphNode* Node, TSet<UAGSGraphNode*>& Visited, FString& Output)
    {
        if (!Node || Visited.Contains(Node))
        {
            return;
        }
        Visited.Add(Node);

        // Get participant name from the tag
        FString ParticipantName = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(Node->GetParticipantTag());
        if (ParticipantName.IsEmpty() || ParticipantName == TEXT("None"))
        {
            ParticipantName = TEXT("NARRATOR");
        }

        const FString DialogueText = Node->GetDialogueText().ToString();
        const FGuid NodeId = Node->GetNodeId();

        // Gather response children vs regular dialogue children
        TArray<UADSDialogueResponseNode*> ResponseChildren;
        TArray<UADSGraphNode*> RegularChildren;

        for (UAGSGraphNode* Child : Node->ChildrenNodes)
        {
            if (UADSDialogueResponseNode* Response = Cast<UADSDialogueResponseNode>(Child))
            {
                ResponseChildren.Add(Response);
            }
            else if (UADSGraphNode* RegularChild = Cast<UADSGraphNode>(Child))
            {
                RegularChildren.Add(RegularChild);
            }
        }

        // Output current node: [Node:GUID] \n ParticipantName: \n Text \n\n
        Output += FString::Printf(TEXT("[Node:%s]\n"), *NodeId.ToString());
        Output += FString::Printf(TEXT("%s:\n"), *ParticipantName);
        Output += FString::Printf(TEXT("%s\n\n"), *DialogueText);

        // If there are response (option) children, output each one
        if (ResponseChildren.Num() > 0)
        {
            for (int32 i = 0; i < ResponseChildren.Num(); i++)
            {
                UADSDialogueResponseNode* Response = ResponseChildren[i];
                if (Visited.Contains(Response))
                {
                    continue;
                }
                Visited.Add(Response);

                FString ResponseParticipant = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(Response->GetParticipantTag());
                if (ResponseParticipant.IsEmpty() || ResponseParticipant == TEXT("None"))
                {
                    ResponseParticipant = TEXT("PLAYER");
                }

                const FString ResponseText = Response->GetDialogueText().ToString();

                Output += FString::Printf(TEXT("[Node:%s]\n"), *Response->GetNodeId().ToString());
                Output += FString::Printf(TEXT("%s (Option %d):\n"), *ResponseParticipant, i + 1);
                Output += FString::Printf(TEXT("%s\n\n"), *ResponseText);

                // Follow each response's children
                for (UAGSGraphNode* ResponseChild : Response->ChildrenNodes)
                {
                    UADSGraphNode* NextNode = Cast<UADSGraphNode>(ResponseChild);
                    if (NextNode)
                    {
                        ExportNodeRecursive(NextNode, Visited, Output);
                    }
                }
            }
        }
        else
        {
            // Follow regular children
            for (UADSGraphNode* Child : RegularChildren)
            {
                ExportNodeRecursive(Child, Visited, Output);
            }
        }
    }
}

void UADSEditorSubsystem::ExportDialogueToFile(UADSDialogue* Dialogue)
{
    if (!Dialogue)
    {
        ShowNotification(TEXT("No dialogue selected"), false);
        return;
    }

#if WITH_EDITORONLY_DATA
    FString Directory = Dialogue->ExportImportDirectory.Path;
    if (Directory.IsEmpty())
    {
        ShowNotification(TEXT("Please set the Export/Import Directory on the Dialogue asset first."), false);
        return;
    }

    // Resolve relative paths
    if (FPaths::IsRelative(Directory))
    {
        Directory = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), Directory);
    }

    // Ensure directory exists
    IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
    if (!PlatformFile.DirectoryExists(*Directory))
    {
        PlatformFile.CreateDirectoryTree(*Directory);
    }

    // Generate file path
    const FString DialogueName = Dialogue->GetName();
    const FString FilePath = FPaths::Combine(Directory, DialogueName + TEXT(".txt"));

    // Confirmation dialog
    const FString ExportConfirmMsg = FString::Printf(
        TEXT("Export dialogue '%s' to:\n%s\n\nAny existing file will be overwritten."),
        *DialogueName, *FilePath);

    if (FMessageDialog::Open(EAppMsgType::OkCancel, FText::FromString(ExportConfirmMsg)) != EAppReturnType::Ok)
    {
        return;
    }

    // Build screenplay header
    FString Output;
    Output += TEXT("# ============================================\n");
    Output += TEXT("# Ascent Dialogue System - Screenplay Export\n");
    Output += FString::Printf(TEXT("# Dialogue: %s\n"), *DialogueName);
    Output += FString::Printf(TEXT("# Exported: %s\n"), *FDateTime::Now().ToString(TEXT("%Y-%m-%d %H:%M")));
    Output += TEXT("# ============================================\n");
    Output += TEXT("#\n");
    Output += TEXT("# FORMAT:\n");
    Output += TEXT("#   [Node:GUID]          <- Do NOT modify this line\n");
    Output += TEXT("#   PARTICIPANT NAME:     <- Speaker name\n");
    Output += TEXT("#   Dialogue text here    <- Editable text\n");
    Output += TEXT("#\n");
    Output += TEXT("# For player choices:\n");
    Output += TEXT("#   PARTICIPANT (Option N):\n");
    Output += TEXT("#   Choice text here\n");
    Output += TEXT("#\n");
    Output += TEXT("# Lines starting with # are comments (ignored during import)\n");
    Output += TEXT("# You may freely edit dialogue text. Do NOT change [Node:...] lines.\n");
    Output += TEXT("# ============================================\n\n");

    // DFS traversal from root nodes
    TSet<UAGSGraphNode*> Visited;
    for (UAGSGraphNode* Root : Dialogue->RootNodes)
    {
        UADSGraphNode* DialogueRoot = Cast<UADSGraphNode>(Root);
        if (DialogueRoot)
        {
            ADSExportHelper::ExportNodeRecursive(DialogueRoot, Visited, Output);
        }
    }

    // Save to file (UTF-8 without BOM for maximum compatibility)
    if (FFileHelper::SaveStringToFile(Output, *FilePath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        const FString SuccessMsg = FString::Printf(TEXT("Dialogue exported to: %s"), *FilePath);
        ShowNotification(SuccessMsg, true);
        UE_LOG(LogTemp, Log, TEXT("%s"), *SuccessMsg);
    }
    else
    {
        ShowNotification(FString::Printf(TEXT("Failed to save file: %s"), *FilePath), false);
    }
#endif
}

// ============================================================================
// Import Helper Functions
// ============================================================================

namespace ADSImportHelper
{
    /** Parsed entry from a screenplay file */
    struct FParsedDialogueEntry
    {
        FString ParticipantName;
        FString Text;
        int32 OptionNumber = 0; // 0 = regular dialogue, >0 = player choice
        FGuid NodeId;           // Optional - from [Node:GUID] tags in exported files
        bool bHasNodeId = false;
    };

    /** Parse a screenplay-formatted text file into dialogue entries */
    static TArray<FParsedDialogueEntry> ParseScreenplay(const FString& FileContent)
    {
        TArray<FParsedDialogueEntry> Entries;
        TArray<FString> Lines;
        FileContent.ParseIntoArrayLines(Lines);

        int32 CurrentEntry = -1;
        bool bReadingText = false;

        // [Node:GUID] lines appear BEFORE the participant header,
        // so we store them as "pending" and assign to the next entry
        FGuid PendingGuid;
        bool bHasPendingGuid = false;

        for (const FString& Line : Lines)
        {
            FString TrimmedStart = Line.TrimStart();

            // Skip comment lines
            if (TrimmedStart.StartsWith(TEXT("#")))
            {
                continue;
            }

            // Capture [Node:GUID] lines (store as pending for the next entry)
            if (TrimmedStart.StartsWith(TEXT("[Node:")) && TrimmedStart.TrimEnd().EndsWith(TEXT("]")))
            {
                FString GuidStr = TrimmedStart.TrimEnd();
                GuidStr = GuidStr.Mid(6, GuidStr.Len() - 7);
                bHasPendingGuid = FGuid::Parse(GuidStr, PendingGuid);
                continue;
            }

            // Check for header line: "Name:" or "Name (Option N):"
            bool bIsHeader = false;
            FString Trimmed = Line.TrimEnd();
            if (Trimmed.EndsWith(TEXT(":")) && Trimmed.Len() > 1)
            {
                FString Content = Trimmed.LeftChop(1).TrimEnd();

                if (!Content.IsEmpty())
                {
                    // Check for "(Option N)" pattern
                    int32 OptionNum = 0;
                    int32 OpenParen = Content.Find(TEXT("(Option "), ESearchCase::IgnoreCase, ESearchDir::FromEnd);
                    if (OpenParen != INDEX_NONE)
                    {
                        int32 CloseParen = Content.Find(TEXT(")"), ESearchCase::IgnoreCase, ESearchDir::FromStart, OpenParen);
                        if (CloseParen != INDEX_NONE && CloseParen == Content.Len() - 1)
                        {
                            FString OptionStr = Content.Mid(OpenParen + 8, CloseParen - OpenParen - 8);
                            OptionNum = FCString::Atoi(*OptionStr);
                            Content = Content.Left(OpenParen).TrimEnd();
                        }
                    }

                    // Trim previous entry's text
                    if (CurrentEntry >= 0)
                    {
                        Entries[CurrentEntry].Text = Entries[CurrentEntry].Text.TrimStartAndEnd();
                    }

                    // Create new entry
                    FParsedDialogueEntry NewEntry;
                    NewEntry.ParticipantName = Content;
                    NewEntry.OptionNumber = OptionNum;

                    // Assign pending GUID if available
                    if (bHasPendingGuid)
                    {
                        NewEntry.NodeId = PendingGuid;
                        NewEntry.bHasNodeId = true;
                        bHasPendingGuid = false;
                    }

                    Entries.Add(NewEntry);
                    CurrentEntry = Entries.Num() - 1;
                    bReadingText = true;
                    bIsHeader = true;
                }
            }

            // Accumulate text lines (if not a header)
            if (!bIsHeader && bReadingText && CurrentEntry >= 0)
            {
                FParsedDialogueEntry& Entry = Entries[CurrentEntry];
                if (!Entry.Text.IsEmpty())
                {
                    Entry.Text += TEXT("\n");
                }
                Entry.Text += Line;
            }
        }

        // Trim last entry
        if (CurrentEntry >= 0)
        {
            Entries[CurrentEntry].Text = Entries[CurrentEntry].Text.TrimStartAndEnd();
        }

        return Entries;
    }

    /** Try to find a GameplayTag matching a participant name */
    static FGameplayTag FindTagForParticipant(const FString& ParticipantName, const FGameplayTagContainer& AllTags)
    {
        if (ParticipantName.IsEmpty())
        {
            return FGameplayTag();
        }

        // Try direct match: Character.Name
        FGameplayTag DirectTag = FGameplayTag::RequestGameplayTag(
            FName(*(TEXT("Character.") + ParticipantName)), false);
        if (DirectTag.IsValid())
        {
            return DirectTag;
        }

        // Search all tags for one ending with .ParticipantName (case-insensitive)
        for (const FGameplayTag& Tag : AllTags)
        {
            FString TagString = Tag.ToString();
            if (TagString.EndsWith(TEXT(".") + ParticipantName, ESearchCase::IgnoreCase))
            {
                return Tag;
            }
        }

        // Try matching just the last segment of any tag
        for (const FGameplayTag& Tag : AllTags)
        {
            FString TagString = Tag.ToString();
            FString LastSegment;
            TagString.Split(TEXT("."), nullptr, &LastSegment, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
            if (LastSegment.Equals(ParticipantName, ESearchCase::IgnoreCase))
            {
                return Tag;
            }
        }

        UE_LOG(LogTemp, Warning, TEXT("Import: No GameplayTag found for participant '%s'. Expected tag like 'Character.%s'."),
            *ParticipantName, *ParticipantName);

        return FGameplayTag();
    }

    /** Create an editor graph node wrapping a runtime node */
    static UEdNode_AGSGraphNode* CreateEditorNode(UEdGraph_AGSGraph* EdGraph, UAGSGraphNode* RuntimeNode, float PosX, float PosY)
    {
        UEdNode_AGSGraphNode* EdNode = NewObject<UEdNode_AGSGraphNode>(EdGraph);
        EdNode->AGSGraphNode = RuntimeNode;

        EdNode->Rename(nullptr, EdGraph);
        EdGraph->AddNode(EdNode, true, false);

        EdNode->CreateNewGuid();
        EdNode->PostPlacedNewNode();
        EdNode->AllocateDefaultPins();

        EdNode->NodePosX = PosX;
        EdNode->NodePosY = PosY;

        RuntimeNode->SetFlags(RF_Transactional);
        EdNode->SetFlags(RF_Transactional);
        RuntimeNode->SetNodePosition(FVector2D(PosX, PosY));

        return EdNode;
    }

    /** Connect output pin of FromNode to input pin of ToNode */
    static void ConnectEditorNodes(UEdNode_AGSGraphNode* FromNode, UEdNode_AGSGraphNode* ToNode)
    {
        if (FromNode && ToNode && FromNode->Pins.Num() >= 2 && ToNode->Pins.Num() >= 2)
        {
            UEdGraphPin* OutputPin = FromNode->Pins[1]; // Output
            UEdGraphPin* InputPin = ToNode->Pins[0];    // Input
            OutputPin->MakeLinkTo(InputPin);
        }
    }
}

void UADSEditorSubsystem::ImportDialogueFromFile(UADSDialogue* Dialogue)
{
    if (!Dialogue)
    {
        ShowNotification(TEXT("No dialogue selected"), false);
        return;
    }

#if WITH_EDITORONLY_DATA

    // ----------------------------------------------------------------
    // 1. Open file dialog to select the screenplay file
    // ----------------------------------------------------------------
    FString InitialDirectory = Dialogue->ExportImportDirectory.Path;
    if (!InitialDirectory.IsEmpty() && FPaths::IsRelative(InitialDirectory))
    {
        InitialDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), InitialDirectory);
    }

    IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
    if (!DesktopPlatform)
    {
        ShowNotification(TEXT("Desktop platform not available"), false);
        return;
    }

    TArray<FString> OpenFilenames;
    const bool bOpened = DesktopPlatform->OpenFileDialog(
        FSlateApplication::Get().FindBestParentWindowHandleForDialogs(nullptr),
        TEXT("Select Screenplay File to Import"),
        InitialDirectory,
        TEXT(""),
        TEXT("Text Files (*.txt)|*.txt|All Files (*.*)|*.*"),
        EFileDialogFlags::None,
        OpenFilenames
    );

    if (!bOpened || OpenFilenames.Num() == 0)
    {
        return; // User cancelled
    }

    const FString FilePath = OpenFilenames[0];

    // ----------------------------------------------------------------
    // 2. Read the screenplay file and delegate to the text-based importer
    // ----------------------------------------------------------------
    FString FileContent;
    if (!FFileHelper::LoadFileToString(FileContent, *FilePath))
    {
        ShowNotification(FString::Printf(TEXT("Failed to read file: %s"), *FilePath), false);
        return;
    }

    ImportDialogueFromText(Dialogue, FileContent, FPaths::GetCleanFilename(FilePath), /*bConfirm*/ true);

#endif
}

void UADSEditorSubsystem::ImportDialogueFromText(UADSDialogue* Dialogue, const FString& ScreenplayText, const FString& SourceName, bool bConfirm)
{
    if (!Dialogue)
    {
        ShowNotification(TEXT("No dialogue selected"), false);
        return;
    }

#if WITH_EDITORONLY_DATA
    // ----------------------------------------------------------------
    // Parse the screenplay text
    // ----------------------------------------------------------------
    TArray<ADSImportHelper::FParsedDialogueEntry> ParsedEntries = ADSImportHelper::ParseScreenplay(ScreenplayText);

    if (ParsedEntries.Num() == 0)
    {
        ShowNotification(TEXT("No dialogue entries found in the text. Check the screenplay format."), false);
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Parsed %d dialogue entries from: %s"), ParsedEntries.Num(), *SourceName);

    // ----------------------------------------------------------------
    // 3. Cache all existing GameplayTags for participant matching
    // ----------------------------------------------------------------
    FGameplayTagContainer AllTags;
    UGameplayTagsManager::Get().RequestAllGameplayTags(AllTags, true);

    // ----------------------------------------------------------------
    // 4. Determine import mode: UPDATE (file has GUIDs matching existing nodes) or CREATE (plain screenplay)
    // ----------------------------------------------------------------
    int32 MatchedGuidCount = 0;
    int32 TotalWithGuids = 0;

    for (const ADSImportHelper::FParsedDialogueEntry& Entry : ParsedEntries)
    {
        if (Entry.bHasNodeId)
        {
            TotalWithGuids++;
            if (Dialogue->GetNodeById(Entry.NodeId) != nullptr)
            {
                MatchedGuidCount++;
            }
        }
    }

    const bool bUseUpdateMode = (MatchedGuidCount > 0);

    // ----------------------------------------------------------------
    // 5. Confirmation dialog
    // ----------------------------------------------------------------
    if (bConfirm && bUseUpdateMode)
    {
        const int32 NewEntries = ParsedEntries.Num() - MatchedGuidCount;
        FString ConfirmMsg = FString::Printf(
            TEXT("Update Mode\n\n"
                 "Found %d entries matching existing nodes (will update text and participant).\n"
                 "%d entries have no matching node (will be skipped).\n\n"
                 "Source: %s\n\nContinue?"),
            MatchedGuidCount, NewEntries, *SourceName);

        if (FMessageDialog::Open(EAppMsgType::YesNo, FText::FromString(ConfirmMsg)) != EAppReturnType::Yes)
        {
            return;
        }
    }
    else if (bConfirm)
    {
        int32 RegularEntries = 0;
        int32 OptionEntries = 0;
        for (const auto& E : ParsedEntries)
        {
            if (E.OptionNumber > 0) OptionEntries++;
            else RegularEntries++;
        }

        FString ConfirmMsg = FString::Printf(
            TEXT("Create Mode - New Dialogue Graph\n\n"
                 "This will REPLACE the current dialogue with:\n"
                 "  %d dialogue nodes\n"
                 "  %d response options\n\n"
                 "Source: %s\n\nContinue?"),
            RegularEntries, OptionEntries, *SourceName);

        if (FMessageDialog::Open(EAppMsgType::YesNo, FText::FromString(ConfirmMsg)) != EAppReturnType::Yes)
        {
            return;
        }
    }

    // ================================================================
    // UPDATE MODE: Update text/tags on existing nodes matched by GUID
    // ================================================================
    if (bUseUpdateMode)
    {
        const FScopedTransaction Transaction(FText::FromString(TEXT("Update Dialogue from Screenplay")));
        Dialogue->Modify();

        int32 UpdatedCount = 0;
        int32 SkippedCount = 0;

        for (const ADSImportHelper::FParsedDialogueEntry& Entry : ParsedEntries)
        {
            if (!Entry.bHasNodeId)
            {
                SkippedCount++;
                continue;
            }

            UAGSGraphNode* Node = Dialogue->GetNodeById(Entry.NodeId);
            if (!Node)
            {
                SkippedCount++;
                UE_LOG(LogTemp, Warning, TEXT("Import: Node ID not found: %s (participant: %s)"),
                    *Entry.NodeId.ToString(), *Entry.ParticipantName);
                continue;
            }

            UADSGraphNode* DialogueNode = Cast<UADSGraphNode>(Node);
            if (DialogueNode)
            {
                DialogueNode->Modify();
                DialogueNode->SetText(FText::FromString(Entry.Text));

                FGameplayTag Tag = ADSImportHelper::FindTagForParticipant(Entry.ParticipantName, AllTags);
                if (Tag.IsValid())
                {
                    DialogueNode->SetParticipantTag(Tag);
                }
                UpdatedCount++;
            }
        }

        Dialogue->MarkPackageDirty();

        FString ResultMsg = FString::Printf(TEXT("Updated %d dialogue entries."), UpdatedCount);
        if (SkippedCount > 0)
        {
            ResultMsg += FString::Printf(TEXT(" (%d entries skipped - no matching node)"), SkippedCount);
        }
        ShowNotification(ResultMsg, true);
        UE_LOG(LogTemp, Log, TEXT("%s"), *ResultMsg);
    }
    // ================================================================
    // CREATE MODE: Build entire dialogue graph from screenplay
    // ================================================================
    else
    {
        const FScopedTransaction Transaction(FText::FromString(TEXT("Import Dialogue from Screenplay")));
        Dialogue->Modify();

        // Ensure EdGraph exists
        UEdGraph_AGSGraph* EdGraph = Cast<UEdGraph_AGSGraph>(Dialogue->EdGraph);
        if (!EdGraph)
        {
            Dialogue->EdGraph = NewObject<UEdGraph_AGSGraph>(Dialogue, UEdGraph_AGSGraph::StaticClass(), NAME_None, RF_Transactional);
            Dialogue->EdGraph->Schema = UAssetGraphSchema_AGSGraph::StaticClass();
            EdGraph = Cast<UEdGraph_AGSGraph>(Dialogue->EdGraph);
        }

        EdGraph->Modify();

        // Clear existing graph nodes
        {
            TArray<UEdGraphNode*> NodesToRemove;
            for (UEdGraphNode* Node : EdGraph->Nodes)
            {
                NodesToRemove.Add(Node);
            }
            for (UEdGraphNode* Node : NodesToRemove)
            {
                EdGraph->RemoveNode(Node);
            }
        }

        Dialogue->AllNodes.Empty();
        Dialogue->RootNodes.Empty();

        // Create nodes from parsed entries
        struct FCreatedNodeInfo
        {
            UEdNode_AGSGraphNode* EdNode = nullptr;
            bool bIsOption = false;
        };

        TArray<FCreatedNodeInfo> CreatedNodes;
        bool bFirstRegularNode = true;
        float PosY = 0.0f;
        bool bPrevWasOption = false;
        float OptionGroupStartY = 0.0f;

        for (int32 i = 0; i < ParsedEntries.Num(); i++)
        {
            const ADSImportHelper::FParsedDialogueEntry& Entry = ParsedEntries[i];

            // Determine the runtime node type
            UADSGraphNode* RuntimeNode = nullptr;
            const bool bIsOption = (Entry.OptionNumber > 0);

            if (bFirstRegularNode && !bIsOption)
            {
                RuntimeNode = NewObject<UADSStartDialogueNode>(Dialogue);
                bFirstRegularNode = false;
            }
            else if (bIsOption)
            {
                RuntimeNode = NewObject<UADSDialogueResponseNode>(Dialogue);
            }
            else
            {
                RuntimeNode = NewObject<UADSDialogueNode>(Dialogue);
                bFirstRegularNode = false;
            }

            // Configure the runtime node
            RuntimeNode->GenerateNewID();
            RuntimeNode->Graph = Dialogue;
            RuntimeNode->SetText(FText::FromString(Entry.Text));

            // Match participant tag
            FGameplayTag ParticipantTag = ADSImportHelper::FindTagForParticipant(Entry.ParticipantName, AllTags);
            if (ParticipantTag.IsValid())
            {
                RuntimeNode->SetParticipantTag(ParticipantTag);
            }

            // Calculate position for layout
            float PosX = 0.0f;

            if (bIsOption)
            {
                if (!bPrevWasOption)
                {
                    OptionGroupStartY = PosY;
                }
                PosX = (Entry.OptionNumber - 1) * 400.0f;
                bPrevWasOption = true;
            }
            else
            {
                if (bPrevWasOption)
                {
                    PosY += 300.0f;
                }
                PosX = 0.0f;
                bPrevWasOption = false;
            }

            // Create the editor graph node
            UEdNode_AGSGraphNode* EdNode = ADSImportHelper::CreateEditorNode(
                EdGraph, RuntimeNode, PosX, bIsOption ? OptionGroupStartY : PosY);

            FCreatedNodeInfo Info;
            Info.EdNode = EdNode;
            Info.bIsOption = bIsOption;
            CreatedNodes.Add(Info);

            if (!bIsOption)
            {
                PosY += 300.0f;
            }
        }

        // Connect nodes via pins
        UEdNode_AGSGraphNode* LastRegularNode = nullptr;
        TArray<UEdNode_AGSGraphNode*> PendingOptionNodes;

        for (int32 i = 0; i < CreatedNodes.Num(); i++)
        {
            const FCreatedNodeInfo& Info = CreatedNodes[i];

            if (Info.bIsOption)
            {
                if (LastRegularNode)
                {
                    ADSImportHelper::ConnectEditorNodes(LastRegularNode, Info.EdNode);
                }
                PendingOptionNodes.Add(Info.EdNode);
            }
            else
            {
                if (PendingOptionNodes.Num() > 0)
                {
                    for (UEdNode_AGSGraphNode* OptionNode : PendingOptionNodes)
                    {
                        ADSImportHelper::ConnectEditorNodes(OptionNode, Info.EdNode);
                    }
                    PendingOptionNodes.Empty();
                }
                else if (LastRegularNode)
                {
                    ADSImportHelper::ConnectEditorNodes(LastRegularNode, Info.EdNode);
                }

                LastRegularNode = Info.EdNode;
            }
        }

        // Rebuild the runtime graph from the EdGraph
        EdGraph->RebuildAGSGraph();
        EdGraph->NotifyGraphChanged();

        Dialogue->MarkPackageDirty();

        // Report results
        int32 RegularCount = 0;
        int32 OptionCount = 0;
        for (const FCreatedNodeInfo& Info : CreatedNodes)
        {
            if (Info.bIsOption) OptionCount++;
            else RegularCount++;
        }

        const FString ResultMsg = FString::Printf(
            TEXT("Created dialogue graph: %d dialogue nodes, %d response options from '%s'"),
            RegularCount, OptionCount, *SourceName);
        ShowNotification(ResultMsg, true);
        UE_LOG(LogTemp, Log, TEXT("%s"), *ResultMsg);
    }

#endif
}

// ============================================================================
// AI Dialogue Generation (OpenAI-compatible)
// ============================================================================

void UADSEditorSubsystem::GenerateDialogueWithAI(UADSDialogue* Dialogue)
{
#if WITH_EDITORONLY_DATA
    if (!Dialogue)
    {
        ShowNotification(TEXT("No dialogue selected"), false);
        return;
    }

    const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();

    const FString APIKey = Settings->GetAIAPIKey();
    if (APIKey.IsEmpty())
    {
        ShowNotification(TEXT("AI API Key is not set. Configure it in Project Settings > Ascent Dialogue Settings > Conversational AI."), false);
        return;
    }

    const FString Description = Dialogue->AIConversationDescription;
    if (Description.IsEmpty())
    {
        ShowNotification(TEXT("Please fill the 'AI Conversation Description' field on the dialogue asset first."), false);
        return;
    }

    // ----------------------------------------------------------------
    // Build participant list from AIParticipantTags on the dialogue asset.
    // Personalities are looked up from the Voice Config data asset when available.
    // ----------------------------------------------------------------
    if (Dialogue->AIParticipantTags.Num() == 0)
    {
        ShowNotification(TEXT("No AI Participant Tags set on this dialogue. Add at least one character tag (e.g. Character.Guard) in the AI Generation section."), false);
        return;
    }

    UADSVoiceConfigDataAsset* VoiceConfig = Settings->GetVoiceConfigDataAsset();
    if (!VoiceConfig)
    {
        ShowNotification(TEXT("No Voice Config Data Asset set in Project Settings > Ascent Dialogue Settings. "
                              "Character personalities cannot be sent to the AI."), false);
        return;
    }

    FString ParticipantsBlock;
    TArray<FString> ParticipantNames;
    FString PlayerName; // name of the character tag that contains "Player"

    for (const FGameplayTag& Tag : Dialogue->AIParticipantTags)
    {
        const FString Name = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(Tag);
        if (Name.IsEmpty() || Name == TEXT("None"))
        {
            const FString Msg = FString::Printf(TEXT("AI Generation: skipping tag '%s' — could not extract a valid character name."), *Tag.ToString());
            UE_LOG(LogTemp, Warning, TEXT("%s"), *Msg);
            ShowNotification(Msg, false);
            continue;
        }

        ParticipantNames.Add(Name);

        // Detect player character (tag leaf contains "player", case-insensitive)
        if (PlayerName.IsEmpty() && Name.ToLower().Contains(TEXT("player")))
        {
            PlayerName = Name;
        }

        // Personality is always read from the Voice Config Data Asset
        const FADSVoiceSettings* FoundSettings = VoiceConfig->VoiceConfigs.Find(Tag);
        const FString Personality = (FoundSettings && !FoundSettings->Personality.IsEmpty())
            ? FoundSettings->Personality
            : TEXT("(no personality set in Voice Config for this character)");

        ParticipantsBlock += FString::Printf(TEXT("- %s: %s\n"), *Name, *Personality);
    }

    if (ParticipantNames.Num() == 0)
    {
        ShowNotification(TEXT("AI Participant Tags are set but no valid character names could be resolved. Check the tags."), false);
        return;
    }

    // ----------------------------------------------------------------
    // Build the dialogue context
    // ----------------------------------------------------------------
    FString DialogueContext;
    DialogueContext += FString::Printf(TEXT("Dialogue asset name: %s\n"), *Dialogue->GetName());
    if (Dialogue->GetDialogueTag().IsValid())
    {
        DialogueContext += FString::Printf(TEXT("Dialogue tag: %s\n"), *Dialogue->GetDialogueTag().ToString());
    }
    if (Dialogue->GetDefaultParticipantTag().IsValid())
    {
        const FString DefaultName = UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(Dialogue->GetDefaultParticipantTag());
        DialogueContext += FString::Printf(TEXT("Primary speaker: %s\n"), *DefaultName);
    }

    // ----------------------------------------------------------------
    // Build the prompt
    // ----------------------------------------------------------------
    const EADSAIPlayerResponseMode ResponseMode = Dialogue->AIPlayerResponseMode;
    const FString ParticipantNamesCsv = FString::Join(ParticipantNames, TEXT(", "));

    // The name used for the player character in the screenplay (empty = no player in this dialogue)
    const FString EffectivePlayerName = PlayerName.IsEmpty() ? TEXT("Player") : PlayerName;

    // Build NPC name list (everyone except the player)
    TArray<FString> NpcNames;
    if (!PlayerName.IsEmpty())
    {
        NpcNames = ParticipantNames.FilterByPredicate(
            [&PlayerName](const FString& N){ return !N.Equals(PlayerName, ESearchCase::IgnoreCase); });
    }
    const FString NpcNamesCsv = FString::Join(NpcNames, TEXT(", "));

    FString SystemPrompt;
    SystemPrompt += TEXT("You are a professional video game dialogue writer.\n");
    SystemPrompt += TEXT("Generate a complete dialogue as a screenplay using EXACTLY the following plain-text format and nothing else:\n\n");
    SystemPrompt += TEXT("CHARACTER_NAME:\n");
    SystemPrompt += TEXT("Line of dialogue text.\n\n");

    // ---- BRANCHING RULE (applies to ALL modes) ----
    SystemPrompt += FString::Printf(
        TEXT("BRANCHING RULE (mandatory in every mode):\n"
             "NEVER invent branches or multiple options on your own.\n"
             "Add multiple %s options (branching) ONLY when the conversation description below\n"
             "EXPLICITLY states that the player must choose between alternatives\n"
             "(e.g. 'the player can decide whether to help or refuse').\n"
             "When branching IS described, use the numbered option format:\n"
             "%s (Option 1):\nFirst choice text.\n\n"
             "%s (Option 2):\nSecond choice text.\n\n"
             "When branching is NOT described, write exactly ONE %s response per beat.\n\n"),
        *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName);

    // ---- NODE TYPE per mode ----
    if (ResponseMode == EADSAIPlayerResponseMode::OptionButtons)
    {
        SystemPrompt += FString::Printf(
            TEXT("NODE TYPE — Player Answers mode:\n"
                 "Every %s line (whether a single response or a branch) MUST use the numbered option format:\n"
                 "%s (Option 1):\nLine of dialogue.\n\n"
                 "Even when there is only one response, still write it as '%s (Option 1):'.\n"
                 "NEVER write a plain '%s:' line.\n\n"),
            *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName);
    }
    else if (ResponseMode == EADSAIPlayerResponseMode::DialogueNodes)
    {
        SystemPrompt += FString::Printf(
            TEXT("NODE TYPE — Player Nodes mode:\n"
                 "Every %s line MUST use the plain dialogue format:\n"
                 "%s:\nLine of dialogue.\n\n"
                 "NEVER use the '%s (Option N):' format — not even for branches.\n"
                 "When branching is described, write each option as a separate plain '%s:' block.\n\n"),
            *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName);
    }
    else // Mixed
    {
        SystemPrompt += FString::Printf(
            TEXT("NODE TYPE — Mixed mode:\n"
                 "For each %s beat, choose the most appropriate node type:\n"
                 "  - Use '%s (Option N):' when the beat is a selectable choice for the player.\n"
                 "  - Use plain '%s:' when the beat is a natural dialogue line.\n"
                 "The choice of node type is independent of branching — a single option button\n"
                 "('%s (Option 1):') is valid when the beat calls for a button but no real branch.\n\n"),
            *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName, *EffectivePlayerName);
    }

    // ---- Hard rules ----
    SystemPrompt += TEXT("RULES:\n");
    SystemPrompt += TEXT("- Use ONLY the following character names as speakers: ") + ParticipantNamesCsv + TEXT(". Do NOT invent any other character names.\n");
    if (NpcNames.Num() > 0)
    {
        SystemPrompt += FString::Printf(
            TEXT("- %s are NPCs: they NEVER use the '(Option N)' format. Only %s can have option buttons.\n"),
            *NpcNamesCsv, *EffectivePlayerName);
    }
    SystemPrompt += TEXT("- The speaker name line MUST end with a colon ':'.\n");
    SystemPrompt += TEXT("- Put the dialogue text on the line(s) directly beneath the speaker line.\n");
    SystemPrompt += TEXT("- Separate each entry with a single blank line.\n");
    SystemPrompt += TEXT("- Do NOT include any markdown, headers, numbering, stage directions in brackets, or commentary.\n");
    SystemPrompt += TEXT("- Keep each line of dialogue natural, in-character and concise.\n");

    FString UserMessage;
    UserMessage += FString::Printf(
        TEXT("Target dialogue length: approximately %d speaker turns total (all characters combined). "
             "Adjust naturally if the description requires slightly more or fewer beats.\n\n"),
        Dialogue->AIDialogueTreeLength);
    UserMessage += TEXT("Conversation description / constraints:\n");
    UserMessage += Description + TEXT("\n\n");
    UserMessage += TEXT("Dialogue context:\n");
    UserMessage += DialogueContext + TEXT("\n");
    UserMessage += TEXT("Participants and their personalities:\n");
    UserMessage += ParticipantsBlock;

    const FString Model = Settings->GetAIModel();
    // Allow a larger response budget than a single line, since we are generating a whole dialogue
    const int32 MaxTok = FMath::Max(Settings->GetMaxTokens(), 1024);

    const FString Payload = Settings->ProcessPayloadTemplate(SystemPrompt, UserMessage, Model, MaxTok);

    // Validate JSON payload before sending
    {
        TSharedPtr<FJsonObject> ValidationJson;
        TSharedRef<TJsonReader<>> ValidationReader = TJsonReaderFactory<>::Create(Payload);
        if (!FJsonSerializer::Deserialize(ValidationReader, ValidationJson))
        {
            ShowNotification(TEXT("Generated AI payload is invalid JSON. Check the AI Payload Template in settings."), false);
            UE_LOG(LogTemp, Error, TEXT("Invalid AI payload: %s"), *Payload);
            return;
        }
    }

    const FString APIEndpoint = Settings->GetAIAPIEndpoint();
    if (APIEndpoint.IsEmpty())
    {
        ShowNotification(TEXT("AI API Endpoint is not set. Configure it in Project Settings > Ascent Dialogue Settings > Conversational AI."), false);
        return;
    }

    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(APIEndpoint);
    Request->SetVerb(TEXT("POST"));

    const TMap<FString, FString> Headers = Settings->ProcessHeadersTemplate(APIKey);
    for (const auto& HeaderPair : Headers)
    {
        Request->SetHeader(HeaderPair.Key, HeaderPair.Value);
    }
    Request->SetContentAsString(Payload);

    // Loading notification with throbber
    FNotificationInfo LoadingInfo(FText::FromString(TEXT("Generating dialogue with AI...")));
    LoadingInfo.bFireAndForget = false;
    LoadingInfo.bUseThrobber = true;
    LoadingInfo.FadeOutDuration = 0.5f;
    LoadingInfo.ExpireDuration = 0.0f;
    TSharedPtr<SNotificationItem> LoadingNotification = FSlateNotificationManager::Get().AddNotification(LoadingInfo);
    if (LoadingNotification.IsValid())
    {
        LoadingNotification->SetCompletionState(SNotificationItem::CS_Pending);
    }

    TWeakObjectPtr<UADSDialogue> WeakDialogue(Dialogue);

    Request->OnProcessRequestComplete().BindLambda(
        [this, WeakDialogue, LoadingNotification](FHttpRequestPtr Req, FHttpResponsePtr Response, bool bWasSuccessful)
        {
            // Dismiss the loading throbber and also spawn a persistent error notification widget.
            auto FailNotify = [this, LoadingNotification](const FString& Msg)
            {
                if (LoadingNotification.IsValid())
                {
                    LoadingNotification->SetCompletionState(SNotificationItem::CS_Fail);
                    LoadingNotification->SetText(FText::FromString(Msg));
                    LoadingNotification->ExpireAndFadeout();
                }
                // Spawn a separate error notification with a readable duration so the
                // user is guaranteed to see the message even if the throbber fades fast.
                ShowNotification(Msg, false);
            };

            if (!bWasSuccessful || !Response.IsValid())
            {
                FailNotify(TEXT("AI request failed (connection error)"));
                return;
            }

            const int32 Code = Response->GetResponseCode();
            const FString Content = Response->GetContentAsString();
            if (Code != 200)
            {
                FailNotify(FString::Printf(TEXT("AI request failed (HTTP %d)"), Code));
                UE_LOG(LogTemp, Error, TEXT("AI generation failed %d: %s"), Code, *Content);
                return;
            }

            TSharedPtr<FJsonObject> Json;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Content);
            if (!FJsonSerializer::Deserialize(Reader, Json) || !Json.IsValid())
            {
                FailNotify(TEXT("Failed to parse AI response JSON"));
                return;
            }

            FString GeneratedText;
            const TArray<TSharedPtr<FJsonValue>>* Choices;
            if (Json->TryGetArrayField(TEXT("choices"), Choices) && Choices->Num() > 0)
            {
                const TSharedPtr<FJsonObject> FirstChoice = (*Choices)[0]->AsObject();
                if (FirstChoice.IsValid())
                {
                    const TSharedPtr<FJsonObject> Message = FirstChoice->GetObjectField(TEXT("message"));
                    if (Message.IsValid())
                    {
                        GeneratedText = Message->GetStringField(TEXT("content"));
                    }
                }
            }

            if (GeneratedText.TrimStartAndEnd().IsEmpty())
            {
                FailNotify(TEXT("AI response did not contain any dialogue text"));
                return;
            }

            if (LoadingNotification.IsValid())
            {
                LoadingNotification->SetCompletionState(SNotificationItem::CS_Success);
                LoadingNotification->SetText(FText::FromString(TEXT("AI dialogue generated")));
                LoadingNotification->ExpireAndFadeout();
            }

            if (!WeakDialogue.IsValid())
            {
                FailNotify(TEXT("Dialogue asset was unloaded before the AI response arrived. Please try again."));
                return;
            }

            ShowGeneratedDialoguePreview(WeakDialogue.Get(), GeneratedText);
        });

    Request->ProcessRequest();
#else
    ShowNotification(TEXT("AI dialogue generation is editor-only."), false);
#endif
}

void UADSEditorSubsystem::ShowGeneratedDialoguePreview(UADSDialogue* Dialogue, const FString& GeneratedText)
{
#if WITH_EDITORONLY_DATA
    TWeakObjectPtr<UADSDialogue> WeakDialogue(Dialogue);

    TSharedRef<SWindow> Window = SNew(SWindow)
        .Title(FText::FromString(TEXT("AI Generated Dialogue - Preview")))
        .ClientSize(FVector2D(720.f, 620.f))
        .SupportsMaximize(true)
        .SupportsMinimize(false);

    TSharedRef<SMultiLineEditableTextBox> TextBox = SNew(SMultiLineEditableTextBox)
        .Text(FText::FromString(GeneratedText))
        .AutoWrapText(true);

    UADSEditorSubsystem* Self = this;
    TWeakPtr<SWindow> WeakWindow = Window;

    Window->SetContent(
        SNew(SVerticalBox)

        + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(8.f)
            [SNew(STextBlock)
                    .Text(FText::FromString(TEXT("Review and edit the AI-generated dialogue below, then click 'Import Dialogue' to build the graph.\nWARNING: importing REPLACES the current dialogue graph.")))
                    .AutoWrapText(true)]

        + SVerticalBox::Slot()
            .FillHeight(1.f)
            .Padding(8.f)
            [SNew(SScrollBox)
                + SScrollBox::Slot()
                    [TextBox]]

        + SVerticalBox::Slot()
            .AutoHeight()
            .HAlign(HAlign_Right)
            .Padding(8.f)
            [SNew(SHorizontalBox)

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.f, 0.f)
                        [SNew(SButton)
                                .Text(FText::FromString(TEXT("Import Dialogue")))
                                .ToolTipText(FText::FromString(TEXT("Build the dialogue graph from the text above. This replaces the current dialogue.")))
                                .OnClicked_Lambda([Self, WeakDialogue, TextBox, WeakWindow]() {
                                    if (WeakDialogue.IsValid())
                                    {
                                        const FString EditedText = TextBox->GetText().ToString();
                                        Self->ImportDialogueFromText(WeakDialogue.Get(), EditedText, TEXT("AI Generated"), /*bConfirm*/ false);
                                    }
                                    if (TSharedPtr<SWindow> Win = WeakWindow.Pin())
                                    {
                                        Win->RequestDestroyWindow();
                                    }
                                    return FReply::Handled();
                                })]

                + SHorizontalBox::Slot()
                    .AutoWidth()
                    .Padding(4.f, 0.f)
                        [SNew(SButton)
                                .Text(FText::FromString(TEXT("Cancel")))
                                .OnClicked_Lambda([WeakWindow]() {
                                    if (TSharedPtr<SWindow> Win = WeakWindow.Pin())
                                    {
                                        Win->RequestDestroyWindow();
                                    }
                                    return FReply::Handled();
                                })]]);

    FSlateApplication::Get().AddWindow(Window);
#endif
}
