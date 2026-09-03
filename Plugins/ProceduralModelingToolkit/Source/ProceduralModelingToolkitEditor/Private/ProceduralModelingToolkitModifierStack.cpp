#include "ProceduralModelingToolkitModifierStack.h"

#include "ProceduralModelingToolkitEditorModule.h"
#include "UDynamicMesh.h"

UProceduralModelingToolkitModifier* UProceduralModelingToolkitModifierStack::AddModifier(TSubclassOf<UProceduralModelingToolkitModifier> ModifierClass)
{
	if (!ModifierClass.Get())
	{
		UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("Modifier stack rejected null modifier class."));
		return nullptr;
	}

	UProceduralModelingToolkitModifier* Modifier = NewObject<UProceduralModelingToolkitModifier>(this, ModifierClass.Get(), NAME_None, RF_Transactional);
	if (!Modifier)
	{
		UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("Modifier stack failed to create modifier '%s'."), *ModifierClass.Get()->GetName());
		return nullptr;
	}

	Modifiers.Add(Modifier);
	return Modifier;
}

bool UProceduralModelingToolkitModifierStack::RemoveModifierAt(int32 Index)
{
	if (!IsValidIndex(Index))
	{
		return false;
	}

	Modifiers.RemoveAt(Index);
	return true;
}

bool UProceduralModelingToolkitModifierStack::MoveModifier(int32 FromIndex, int32 ToIndex)
{
	if (!IsValidIndex(FromIndex) || ToIndex < 0 || ToIndex >= Modifiers.Num())
	{
		return false;
	}

	if (FromIndex == ToIndex)
	{
		return true;
	}

	TObjectPtr<UProceduralModelingToolkitModifier> Modifier = Modifiers[FromIndex];
	Modifiers.RemoveAt(FromIndex);
	Modifiers.Insert(Modifier, ToIndex);
	return true;
}

void UProceduralModelingToolkitModifierStack::SetModifierEnabled(int32 Index, bool bEnabled)
{
	if (IsValidIndex(Index) && Modifiers[Index])
	{
		Modifiers[Index]->SetEnabled(bEnabled);
	}
}

FProceduralModelingToolkitModifierStackResult UProceduralModelingToolkitModifierStack::Execute(
	UDynamicMesh* TargetMesh,
	const FProceduralModelingToolkitModifierExecutionContext& Context
)
{
	FProceduralModelingToolkitModifierStackResult StackResult;

	if (!TargetMesh)
	{
		StackResult.bSuccess = false;
		StackResult.Messages.Add(TEXT("Modifier stack execution failed: target Dynamic Mesh is null."));
		return StackResult;
	}

	for (UProceduralModelingToolkitModifier* Modifier : Modifiers)
	{
		if (!Modifier || !Modifier->IsEnabled())
		{
			continue;
		}

		const FProceduralModelingToolkitModifierResult ModifierResult = Modifier->Execute(TargetMesh, Context);
		StackResult.ExecutedCount++;

		if (!ModifierResult.Message.IsEmpty())
		{
			StackResult.Messages.Add(ModifierResult.Message);
		}

		if (!ModifierResult.bSuccess)
		{
			StackResult.bSuccess = false;
			break;
		}
	}

	UE_LOG(
		LogProceduralModelingToolkit,
		Log,
		TEXT("Modifier stack executed. Modifiers=%d Executed=%d Success=%s Source='%s' Output='%s'"),
		Modifiers.Num(),
		StackResult.ExecutedCount,
		StackResult.bSuccess ? TEXT("true") : TEXT("false"),
		*Context.SourceAssetPath,
		*Context.OutputAssetPath
	);

	return StackResult;
}

void UProceduralModelingToolkitModifierStack::Serialize(FArchive& Ar)
{
	Super::Serialize(Ar);
}

bool UProceduralModelingToolkitModifierStack::IsValidIndex(int32 Index) const
{
	return Modifiers.IsValidIndex(Index);
}
