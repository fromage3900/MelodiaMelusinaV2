#pragma once

#include "CoreMinimal.h"
#include "ProceduralModelingToolkitModifier.h"
#include "Templates/SubclassOf.h"
#include "UObject/Object.h"
#include "UObject/ObjectPtr.h"
#include "ProceduralModelingToolkitModifierStack.generated.h"

class UDynamicMesh;

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitModifierStackResult
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier Stack")
	bool bSuccess = true;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier Stack")
	int32 ExecutedCount = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Procedural Modifier Stack")
	TArray<FString> Messages;
};

UCLASS(BlueprintType)
class UProceduralModelingToolkitModifierStack : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier Stack")
	int32 Version = 1;

	UPROPERTY(EditAnywhere, Instanced, BlueprintReadWrite, Category = "Procedural Modifier Stack")
	TArray<TObjectPtr<UProceduralModelingToolkitModifier>> Modifiers;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Modifier Stack")
	FString PresetSourcePath;

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier Stack")
	UProceduralModelingToolkitModifier* AddModifier(TSubclassOf<UProceduralModelingToolkitModifier> ModifierClass);

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier Stack")
	bool RemoveModifierAt(int32 Index);

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier Stack")
	bool MoveModifier(int32 FromIndex, int32 ToIndex);

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier Stack")
	void SetModifierEnabled(int32 Index, bool bEnabled);

	UFUNCTION(BlueprintCallable, Category = "Procedural Modifier Stack")
	FProceduralModelingToolkitModifierStackResult Execute(
		UDynamicMesh* TargetMesh,
		const FProceduralModelingToolkitModifierExecutionContext& Context
	);

	virtual void Serialize(FArchive& Ar) override;

private:
	bool IsValidIndex(int32 Index) const;
};
