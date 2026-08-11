// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptSubsystem.h"

#include "TimerManager.h"
#include "Core/QuillscriptNetwork.h"
#include "Core/QuillscriptSettings.h"
#include "Engine/Engine.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"
#include "Utils/Tools.h"

#if WITH_EDITOR

	#include "Editor.h"

#endif


UQuillscriptSubsystem::UQuillscriptSubsystem()
{
	// Set self reference.
	Self = this;

	// Clear any previous selected Settings Asset, and ensure the game always starts using project settings.
	UQuillscriptSettings::ClearSettingsAsset();

	// Inject defaults.
	this->AppendDefaultValues(UQuillscriptSettings::Get()->GetDefaultVariables(), UQuillscriptSettings::Get()->GetDefaultScriptReferences());
}

void UQuillscriptSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	/// Set timer to check for players still in session.
	// FTimerHandle TimerHandle;
	//
	// this->GetWorld()->GetTimerManager().SetTimer(
	// 	TimerHandle,
	// 	FTimerDelegate::CreateUObject(this, &UQuillscriptSubsystem::CreateNetworksForPlayers),
	// 	2.0f,
	// 	true
	// );
}


#pragma region References

UWorld* UQuillscriptSubsystem::World(const UObject* WorldContextObject)
{
	// Try to use an automatic world context object.
	if (WorldContextObject && WorldContextObject->IsValidLowLevel())
		if (TObjectPtr<UWorld> World{ WorldContextObject->GetWorld() })
			if (World->IsValidLowLevel())
				return World;

	// Try to get it from self.
	if (Self && Self->IsValidLowLevel())
	{
		if (TObjectPtr<UWorld> World{ Self->GetWorld() })
		{
			if (
				World->IsValidLowLevel() &&
				(
					World->WorldType == EWorldType::Game ||
					World->WorldType == EWorldType::PIE ||
					World->WorldType == EWorldType::GamePreview
				)
			)
				return World;
		}
	}

	// Try to get it from the Engine.
	if (GEngine && GEngine->IsValidLowLevel())
		return GEngine->GetWorldContextFromGameViewport(GEngine->GameViewport)->World();

	// Try to get it from the Editor.
	#if WITH_EDITOR

	if (GEditor && GEditor->IsValidLowLevel())
		return GEditor->GetEditorWorldContext().World();

	#endif

	// This may cause a crash, if not evaluated.
	return nullptr;
}

#pragma endregion References


#pragma region Data

void UQuillscriptSubsystem::AppendDefaultValues(const TMap<FName, FText>& DefaultVariables, TMap<FName, FSoftObjectPath> DefaultScriptReferences)
{
	// Inject default variables.
	this->Variables.Append(DefaultVariables);

	// Inject default script references.
	TArray<FName> ReferencesNames;
	DefaultScriptReferences.GenerateKeyArray(ReferencesNames);

	for (int32 I{ 0 }; I < ReferencesNames.Num(); ++I)
		this->References.Add(ReferencesNames[I], DefaultScriptReferences[ReferencesNames[I]].TryLoad());
}

void UQuillscriptSubsystem::CreateNetworksForPlayers()
{
	if (UQuillscriptSettings::Get()->HasMultiplayer() && UTools::HasAuthority(this))
	{
		// Remove any networks that are not in the game anymore.
		for (auto NetworksCopy{ this->Networks }; auto* Network : NetworksCopy)
		{
			bool bExists{ false };

			for (const auto& PlayerState : this->GetWorld()->GetGameState()->PlayerArray)
			{
				if (PlayerState == Cast<APlayerState>(Network->GetOwner()))
				{
					bExists = true;
					break;
				}
			}

			if (!bExists)
				this->Networks.Remove(Network);
		}

		// Add any new networks that are in the game.
		for (const auto& PlayerState : this->GetWorld()->GetGameState()->PlayerArray)
		{
			bool bExists{ false };

			for (const auto* Network : this->Networks)
            {
                if (PlayerState == Cast<APlayerState>(Network->GetOwner()))
                {
                    bExists = true;
                    break;
                }
            }

			if (!bExists)
            {
                TObjectPtr<AQuillscriptNetwork> Network{ this->GetWorld()->SpawnActor<AQuillscriptNetwork>() };
                Network->SetOwner(PlayerState);
                this->Networks.Add(Network);
            }
		}
	}
}

#pragma endregion Data


#pragma region SaveLoad

void UQuillscriptSubsystem::SerializeQuillscriptData(FMemoryWriter& Ar)
{
	// Prevent crash caused when trying to save an empty history.
	if (!History.IsEmpty())
	{
		FString Type;
		HistoryAsString = UTools::GetPropertyByName(this, "History", Type);
	}
	else
		HistoryAsString = FooData;

	Ar << Variables;
	Ar << HistoryAsString;
}

void UQuillscriptSubsystem::DeserializeQuillscriptData(FMemoryReader& Ar)
{
	Ar << Variables;
	Ar << HistoryAsString;

	// Only reload history if there is data to reload.
	if (HistoryAsString != FooData)
		UTools::SetPropertyByName(this, "History", HistoryAsString);
}

void UQuillscriptSubsystem::InjectQuillscriptDataIntoSaveGame(TArray<uint8>& SaveGameBytesToInjectInto)
{
	TArray<uint8> QuillscriptDataBytes;
	TArray<uint8> QuillscriptDataBytesLength;

	// Create a memory writer to inject Quillscript persistent data.
	FMemoryWriter DataMemoryWriter(QuillscriptDataBytes, true);
	this->SerializeQuillscriptData(DataMemoryWriter);

	// Create a memory writer to inject Quillscript persistent data length.
	FMemoryWriter LengthMemoryWriter(QuillscriptDataBytesLength, true);

	int32 DataLength{ QuillscriptDataBytes.Num() };
	LengthMemoryWriter << DataLength;

	// Save.
	SaveGameBytesToInjectInto.Append(QuillscriptDataBytes);
	SaveGameBytesToInjectInto.Append(QuillscriptDataBytesLength);
}

void UQuillscriptSubsystem::ExtractQuillscriptDataFromSaveGame(TArray<uint8>& SaveGameBytesToExtractFrom)
{
	TArray<uint8> QuillscriptDataBytes;
	TArray<uint8> QuillscriptDataBytesLength;
	int32 Int32Size{ sizeof(int32) };

	// Retrieve Quillscript data length.
	for (int32 I{ SaveGameBytesToExtractFrom.Num() - Int32Size }; I < SaveGameBytesToExtractFrom.Num(); I++)
		QuillscriptDataBytesLength.Add(SaveGameBytesToExtractFrom[I]);

	FMemoryReader LengthMemoryReader{ FMemoryReader(QuillscriptDataBytesLength, true) };

	int32 DataLength;
	LengthMemoryReader << DataLength;

	// Retrieve Quillscript data.
	for (int32 I{ SaveGameBytesToExtractFrom.Num() - ( DataLength + Int32Size ) }; I < SaveGameBytesToExtractFrom.Num(); I++)
		QuillscriptDataBytes.Add(SaveGameBytesToExtractFrom[I]);

	FMemoryReader DataMemoryReader{ FMemoryReader(QuillscriptDataBytes, true) };
	this->DeserializeQuillscriptData(DataMemoryReader);
}

#pragma endregion SaveLoad