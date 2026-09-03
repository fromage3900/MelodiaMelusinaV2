// Copyright Monolith. All Rights Reserved.

#include "MonolithParamUtils.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Misc/Paths.h"

namespace MonolithParamUtils
{

bool ParseVector(const TSharedPtr<FJsonObject>& Params, const FString& Key, FVector& Out)
{
	// Try array format: [x, y, z]
	const TArray<TSharedPtr<FJsonValue>>* Arr;
	if (Params->TryGetArrayField(Key, Arr) && Arr->Num() >= 3)
	{
		Out.X = (*Arr)[0]->AsNumber();
		Out.Y = (*Arr)[1]->AsNumber();
		Out.Z = (*Arr)[2]->AsNumber();
		return true;
	}

	// Try object format: {x, y, z}
	const TSharedPtr<FJsonObject>* Obj;
	if (Params->TryGetObjectField(Key, Obj))
	{
		Out.X = (*Obj)->GetNumberField(TEXT("x"));
		Out.Y = (*Obj)->GetNumberField(TEXT("y"));
		Out.Z = (*Obj)->GetNumberField(TEXT("z"));
		return true;
	}

	return false;
}

bool ParseRotator(const TSharedPtr<FJsonObject>& Params, const FString& Key, FRotator& Out)
{
	// Try array format: [pitch, yaw, roll]
	const TArray<TSharedPtr<FJsonValue>>* Arr;
	if (Params->TryGetArrayField(Key, Arr) && Arr->Num() >= 3)
	{
		Out.Pitch = (*Arr)[0]->AsNumber();
		Out.Yaw   = (*Arr)[1]->AsNumber();
		Out.Roll  = (*Arr)[2]->AsNumber();
		return true;
	}

	// Try object format: {pitch, yaw, roll}
	const TSharedPtr<FJsonObject>* Obj;
	if (Params->TryGetObjectField(Key, Obj))
	{
		Out.Pitch = (*Obj)->GetNumberField(TEXT("pitch"));
		Out.Yaw   = (*Obj)->GetNumberField(TEXT("yaw"));
		Out.Roll  = (*Obj)->GetNumberField(TEXT("roll"));
		return true;
	}

	return false;
}

UWorld* GetEditorWorld()
{
	if (GEditor)
	{
		UWorld* World = GEditor->GetEditorWorldContext().World();
		if (World)
		{
			return World;
		}
	}
	return nullptr;
}

TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V)
{
	TArray<TSharedPtr<FJsonValue>> Arr;
	Arr.Add(MakeShared<FJsonValueNumber>(V.X));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
	return Arr;
}

FString NormalizeBlueprintClassPath(const FString& BlueprintPath)
{
	FString ClassPath = BlueprintPath;
	if (!ClassPath.Contains(TEXT(".")))
	{
		FString BaseName = FPaths::GetBaseFilename(ClassPath);
		ClassPath = ClassPath + TEXT(".") + BaseName + TEXT("_C");
	}
	else if (!ClassPath.EndsWith(TEXT("_C")))
	{
		ClassPath += TEXT("_C");
	}
	return ClassPath;
}

bool ParseMobility(const FString& MobilityStr, EComponentMobility::Type& OutMobility)
{
	if (MobilityStr.Equals(TEXT("static"), ESearchCase::IgnoreCase))
	{
		OutMobility = EComponentMobility::Static;
		return true;
	}
	if (MobilityStr.Equals(TEXT("stationary"), ESearchCase::IgnoreCase))
	{
		OutMobility = EComponentMobility::Stationary;
		return true;
	}
	if (MobilityStr.Equals(TEXT("movable"), ESearchCase::IgnoreCase))
	{
		OutMobility = EComponentMobility::Movable;
		return true;
	}
	return false;
}

} // namespace MonolithParamUtils
