#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithAudioQueryActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult ListAudioAssets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SearchAudioAssets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetSoundWaveInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetSoundClassHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetSubmixHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindAudioReferences(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindUnusedAudio(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindSoundsWithoutClass(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindUnattenuatedSounds(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetAudioStats(const TSharedPtr<FJsonObject>& Params);

	// Helpers
	static UClass* ResolveAudioClass(const FString& TypeName);
	static TSharedPtr<FJsonObject> BuildSoundClassTree(class USoundClass* SoundClass, TSet<USoundClass*>& Visited);
	static TSharedPtr<FJsonObject> BuildSubmixTree(class USoundSubmixBase* Submix, TSet<USoundSubmixBase*>& Visited);
	static FString CompressionTypeToString(uint8 Type);
};
