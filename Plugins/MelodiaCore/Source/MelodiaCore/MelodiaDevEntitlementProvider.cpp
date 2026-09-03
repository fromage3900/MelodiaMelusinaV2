#include "MelodiaDevEntitlementProvider.h"

#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

FString UMelodiaDevEntitlementProvider::GetDevFilePath()
{
	return FPaths::ProjectSavedDir() / TEXT("DevEntitlements.json");
}

bool UMelodiaDevEntitlementProvider::LoadFromFile()
{
	ContentPacks.Reset();
	const FString FilePath = GetDevFilePath();
	FString JsonContent;
	if (!FFileHelper::LoadFileToString(JsonContent, *FilePath))
	{
		UE_LOG(LogTemp, Log, TEXT("MelodiaDevEntitlementProvider: no dev file at '%s'."), *FilePath);
		return false;
	}
	TSharedPtr<FJsonObject> Root;
	if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(JsonContent), Root) || !Root)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaDevEntitlementProvider: failed to parse '%s'."), *FilePath);
		return false;
	}
	const TArray<TSharedPtr<FJsonValue>>* Packs = nullptr;
	if (!Root->TryGetArrayField(TEXT("owned_content_packs"), Packs))
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaDevEntitlementProvider: 'owned_content_packs' not found in '%s'."), *FilePath);
		return false;
	}
	for (const TSharedPtr<FJsonValue>& Val : *Packs)
	{
		const FString Name = Val->AsString();
		if (!Name.IsEmpty())
			ContentPacks.Add(FName(*Name));
	}
	UE_LOG(LogTemp, Log, TEXT("MelodiaDevEntitlementProvider: loaded %d content packs from '%s'."), ContentPacks.Num(), *FilePath);
	return true;
}

bool UMelodiaDevEntitlementProvider::SaveToFile()
{
	const FString FilePath = GetDevFilePath();
	TSharedPtr<FJsonObject> Root = MakeShareable(new FJsonObject());
	TArray<TSharedPtr<FJsonValue>> Packs;
	for (const FName& Pack : ContentPacks)
	{
		Packs.Add(MakeShareable(new FJsonValueString(Pack.ToString())));
	}
	Root->SetArrayField(TEXT("owned_content_packs"), Packs);
	FString JsonContent;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonContent);
	if (!FJsonSerializer::Serialize(Root.ToSharedRef(), Writer))
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaDevEntitlementProvider: failed to serialize."));
		return false;
	}
	if (!FFileHelper::SaveStringToFile(JsonContent, *FilePath))
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaDevEntitlementProvider: failed to write '%s'."), *FilePath);
		return false;
	}
	UE_LOG(LogTemp, Log, TEXT("MelodiaDevEntitlementProvider: saved %d content packs to '%s'."), ContentPacks.Num(), *FilePath);
	return true;
}

TArray<FName> UMelodiaDevEntitlementProvider::QueryOwnedContentPacks_Implementation() const
{
	TArray<FName> Result = ContentPacks;
	Result.AddUnique(TEXT("Core"));
	Result.Sort(FNameLexicalLess());
	return Result;
}
