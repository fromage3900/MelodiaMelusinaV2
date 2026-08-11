// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AutoBlendUserData.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "MeshBlendBPLibrary.generated.h"

UCLASS()
class MESHBLEND_API UMeshBlendBPLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void SetBlendUserDataOnMesh(UStaticMesh* Mesh, EAutoBlendOption NewBlendOption);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void ClearBlendUserDataFromMesh(UStaticMesh* Mesh);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void SetBlendOptionOnActor(AActor* Actor, EAutoBlendOption NewBlendOption);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void DisableBlendOnActor(AActor* Actor);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void RefreshBlendOnActor(AActor* Actor, bool bSoftReset);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static void ClearBlendOptionFromActor(AActor* Actor);

#if WITH_EDITOR

private:
	static void RefreshActorsReferencingAsset(const UStaticMesh* Mesh, const UWorld* World);

#endif
};
