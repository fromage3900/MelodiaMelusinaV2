// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MeshBlendActivatorLogic.h"
#include "Subsystems/WorldSubsystem.h"
#include "MeshBlendActivatorSubsystem.generated.h"

UCLASS()
class MESHBLEND_API UMeshBlendActivatorSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Deinitialize() override;
	virtual void PostInitialize() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual bool IsTickableInEditor() const override { return true; }
	virtual ETickableTickType GetTickableTickType() const override;
	virtual TStatId GetStatId() const override;

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	void RefreshActor(AActor* Actor, bool bSoftReset);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend")
	static UMeshBlendActivatorSubsystem* GetInstance(const UWorld* World);

	UPROPERTY(Transient, DuplicateTransient)
	TObjectPtr<UMeshBlendActivatorLogic> MeshBlendActivatorLogic;

private:
	UPROPERTY(Transient, DuplicateTransient)
	bool CachedCVarMeshBlendEnable = true;

#if WITH_EDITOR

private:
	void OnPreSaveExternalActors(UWorld* World);
#endif
};
