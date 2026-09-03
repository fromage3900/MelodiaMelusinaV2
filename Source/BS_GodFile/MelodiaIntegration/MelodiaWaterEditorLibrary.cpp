// Copyright Melodia Water Systems. All Rights Reserved.

#include "MelodiaWaterEditorLibrary.h"

#if WITH_EDITOR

#include "AssetToolsModule.h"
#include "Factories/Factory.h"
#include "Misc/PackageName.h"
#include "NiagaraDataChannel.h"
#include "NiagaraDataChannelAsset.h"
#include "NiagaraDataChannelAssetFactoryNew.h"
#include "NiagaraDataChannelVariable.h"
#include "NiagaraDataChannel_Global.h"
#include "NiagaraTypes.h"
#include "Editor.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"

namespace MelodiaWaterEditorPrivate
{
	static bool SetObjectProperty(UObject* Object, const FName PropertyName, UObject* Value)
	{
		if (!Object)
		{
			return false;
		}

		if (FObjectProperty* ObjectProperty = FindFProperty<FObjectProperty>(Object->GetClass(), PropertyName))
		{
			ObjectProperty->SetObjectPropertyValue_InContainer(Object, Value);
			return true;
		}

		return false;
	}

	static bool SetBoolProperty(UObject* Object, const FName PropertyName, const bool Value)
	{
		if (!Object)
		{
			return false;
		}

		if (FBoolProperty* BoolProperty = FindFProperty<FBoolProperty>(Object->GetClass(), PropertyName))
		{
			BoolProperty->SetPropertyValue_InContainer(Object, Value);
			return true;
		}

		return false;
	}

	static bool SetChannelVariables(UNiagaraDataChannel* Channel)
	{
		if (!Channel)
		{
			return false;
		}

		FArrayProperty* VariablesProperty = FindFProperty<FArrayProperty>(Channel->GetClass(), TEXT("ChannelVariables"));
		if (!VariablesProperty)
		{
			return false;
		}

		FStructProperty* VariableStructProperty = CastField<FStructProperty>(VariablesProperty->Inner);
		if (!VariableStructProperty || VariableStructProperty->Struct != FNiagaraDataChannelVariable::StaticStruct())
		{
			return false;
		}

		FScriptArrayHelper VariablesHelper(VariablesProperty, VariablesProperty->ContainerPtrToValuePtr<void>(Channel));
		VariablesHelper.EmptyValues();

		struct FWaterField
		{
			FName Name;
			FNiagaraTypeDefinition Type;
		};

		const FWaterField Fields[] = {
			{ TEXT("Position"), FNiagaraTypeDefinition::GetPositionDef() },
			{ TEXT("Velocity"), FNiagaraTypeDefinition::GetVec3Def() },
			{ TEXT("Radius"), FNiagaraTypeDefinition::GetFloatDef() },
			{ TEXT("Intensity"), FNiagaraTypeDefinition::GetFloatDef() },
			{ TEXT("Immersion"), FNiagaraTypeDefinition::GetFloatDef() },
			{ TEXT("WaterBodyIndex"), FNiagaraTypeDefinition::GetIntDef() },
			{ TEXT("EventType"), FNiagaraTypeDefinition::GetIntDef() },
			{ TEXT("RandomSeed"), FNiagaraTypeDefinition::GetIntDef() }
		};

		for (const FWaterField& Field : Fields)
		{
			const int32 NewIndex = VariablesHelper.AddValue();
			FNiagaraDataChannelVariable* NewVariable = reinterpret_cast<FNiagaraDataChannelVariable*>(VariablesHelper.GetRawPtr(NewIndex));
			if (!NewVariable)
			{
				return false;
			}

			VariableStructProperty->InitializeValue(NewVariable);
			NewVariable->SetName(Field.Name);
			NewVariable->SetType(FNiagaraDataChannelVariable::ToDataChannelType(Field.Type));
		}

		return true;
	}
}

bool UMelodiaWaterEditorLibrary::CreateOrUpdateWaterContactDataChannel(const FString& AssetPath, FString& OutReport)
{
	using namespace MelodiaWaterEditorPrivate;

	OutReport.Reset();

	if (!AssetPath.StartsWith(TEXT("/Game/")) || AssetPath.Contains(TEXT(".")))
	{
		OutReport = TEXT("AssetPath must be a project package path such as /Game/EnvSandbox/Water/v10/NDC_MelodiaWaterContact");
		return false;
	}

	const FString PackagePath = FPackageName::GetLongPackagePath(AssetPath);
	const FString AssetName = FPackageName::GetShortName(AssetPath);
	if (PackagePath.IsEmpty() || AssetName.IsEmpty())
	{
		OutReport = TEXT("AssetPath could not be split into a valid package path and asset name");
		return false;
	}

	UNiagaraDataChannelAsset* Asset = LoadObject<UNiagaraDataChannelAsset>(nullptr, *AssetPath);
	if (!Asset)
	{
		FAssetToolsModule& AssetToolsModule = FAssetToolsModule::GetModule();
		UNiagaraDataChannelAssetFactoryNew* Factory = NewObject<UNiagaraDataChannelAssetFactoryNew>();
		Asset = Cast<UNiagaraDataChannelAsset>(AssetToolsModule.Get().CreateAsset(
			AssetName,
			PackagePath,
			UNiagaraDataChannelAsset::StaticClass(),
			Factory));
	}

	if (!Asset)
	{
		OutReport = FString::Printf(TEXT("Failed to create Niagara Data Channel asset at %s"), *AssetPath);
		return false;
	}

	Asset->Modify();
	UNiagaraDataChannel* Channel = Asset->Get();
	if (!Channel || !Channel->IsA<UNiagaraDataChannel_Global>())
	{
		Channel = NewObject<UNiagaraDataChannel_Global>(Asset, NAME_None, RF_Transactional);
		if (!SetObjectProperty(Asset, TEXT("DataChannel"), Channel))
		{
			OutReport = TEXT("Failed to assign the project-owned NiagaraDataChannel_Global inner object");
			return false;
		}
	}

	Channel->Modify();
	if (!SetChannelVariables(Channel))
	{
		OutReport = TEXT("Failed to populate the Niagara Data Channel variable contract");
		return false;
	}

	SetBoolProperty(Channel, TEXT("bKeepPreviousFrameData"), true);
	SetBoolProperty(Channel, TEXT("bEnforceTickGroupReadWriteOrder"), false);
	Asset->MarkPackageDirty();
	Channel->MarkPackageDirty();

	// Use the editor's registered-asset save pipeline. Direct UPackage::SavePackage
	// bypasses editor asset bookkeeping and can leave orphaned .tmp files or fail
	// while another editor-owned package operation is active.
	UEditorAssetSubsystem* EditorAssetSubsystem = GEditor
		? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()
		: nullptr;
	const bool bSaved = EditorAssetSubsystem
		&& EditorAssetSubsystem->SaveLoadedAsset(Asset, /*bOnlyIfIsDirty=*/ false);
	OutReport = FString::Printf(
		TEXT("%s: Position, Velocity, Radius, Intensity, Immersion, WaterBodyIndex, EventType, RandomSeed; saved=%s"),
		*AssetPath,
		bSaved ? TEXT("true") : TEXT("false"));
	return bSaved;
}

#endif // WITH_EDITOR
