// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendActivatorSubsystem.h"

#include "EngineUtils.h"
#include "Engine/World.h"
#include "Logging/MessageLog.h"
#include "UObject/ObjectSaveContext.h"

#if WITH_EDITOR
#include "Editor.h"
#endif


static TAutoConsoleVariable<bool> CVarMeshBlendEnable(
	TEXT("r.MeshBlend.Enable"),
	true,
	TEXT("Enable/Disable the Activator."));

static TAutoConsoleVariable<float> CVarMeshBlendProcessBudget(
	TEXT("r.MeshBlend.ProcessBudget"),
	0.3,
	TEXT(".."));

#if WITH_EDITOR

static TAutoConsoleVariable<bool> CVarMeshBlendDisableRestrictions(
	TEXT("r.MeshBlend.DisableRestrictions"),
	false,
	TEXT("Enable/Disable the distance and time budget of the activator. (Used with sequencer movie rendering)"));

static TAutoConsoleVariable<bool> CVarMeshBlendCustomerGBufferChannel(
	TEXT("r.MeshBlend.CustomerGBufferChannel"),
	false,
	TEXT("When true will stop warnings related to Material AO workflow and hide the shader patcher tool."));

#endif

#define LOCTEXT_NAMESPACE "UMeshBlendActivatorSubsystem"

bool UMeshBlendActivatorSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	check(World);
	
	return !World->IsNetMode(NM_DedicatedServer) && Super::ShouldCreateSubsystem(Outer);
}

void UMeshBlendActivatorSubsystem::Deinitialize()
{
	check(MeshBlendActivatorLogic);

#if WITH_EDITOR
	FEditorDelegates::PreSaveExternalActors.RemoveAll(this);
#endif

	MeshBlendActivatorLogic->Deinitialize();
	Super::Deinitialize();
}

void UMeshBlendActivatorSubsystem::PostInitialize()
{
	Super::PostInitialize();
	MeshBlendActivatorLogic = NewObject<UMeshBlendActivatorLogic>(this, UMeshBlendActivatorLogic::StaticClass());
	MeshBlendActivatorLogic->ProcessBudget = FMath::Max(0.0f, CVarMeshBlendProcessBudget.GetValueOnGameThread());
	
#if WITH_EDITOR
	MeshBlendActivatorLogic->bDisableRestrictions = CVarMeshBlendDisableRestrictions.GetValueOnGameThread();
#endif
	
	MeshBlendActivatorLogic->IsBlendingEnabled = CVarMeshBlendEnable.GetValueOnGameThread();
	CachedCVarMeshBlendEnable = CVarMeshBlendEnable.GetValueOnGameThread();

	if (UWorld* World = GetWorld())
	{
		MeshBlendActivatorLogic->Initialize(World);

#if WITH_EDITOR
		if (World->WorldType == EWorldType::Editor)
		{
			FEditorDelegates::PreSaveExternalActors.AddUObject(this, &UMeshBlendActivatorSubsystem::OnPreSaveExternalActors);
		}
#endif
	}
}

void UMeshBlendActivatorSubsystem::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	check(MeshBlendActivatorLogic);

	if (const UWorld* World = GetWorld())
	{
		if (CVarMeshBlendEnable.GetValueOnGameThread() != CachedCVarMeshBlendEnable)
		{
			CachedCVarMeshBlendEnable = CVarMeshBlendEnable.GetValueOnGameThread();

			if (CachedCVarMeshBlendEnable)
			{
				MeshBlendActivatorLogic->RestartActivator(World, true);
			}
			else
			{
				MeshBlendActivatorLogic->StopActivator();
			}
		}

		if (!CachedCVarMeshBlendEnable)
		{
			return;
		}

		MeshBlendActivatorLogic->ProcessBudget = FMath::Max(0.0f, CVarMeshBlendProcessBudget.GetValueOnGameThread());
		
#if WITH_EDITOR
		MeshBlendActivatorLogic->bDisableRestrictions = CVarMeshBlendDisableRestrictions.GetValueOnGameThread();
#endif
		
		MeshBlendActivatorLogic->Tick(World);
	}
}

ETickableTickType UMeshBlendActivatorSubsystem::GetTickableTickType() const
{
	return IsTemplate() ? ETickableTickType::Never : ETickableTickType::Always;
}

TStatId UMeshBlendActivatorSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UMeshBlendActivatorSubSystem, STATGROUP_Tickables);
}

void UMeshBlendActivatorSubsystem::RefreshActor(AActor* Actor, const bool bSoftReset)
{
	check(MeshBlendActivatorLogic);
	MeshBlendActivatorLogic->ScheduleActorRefresh(Actor, bSoftReset);
}


UMeshBlendActivatorSubsystem* UMeshBlendActivatorSubsystem::GetInstance(const UWorld* World)
{
	if (World)
	{
		UMeshBlendActivatorSubsystem* Subsystem = World->GetSubsystem<UMeshBlendActivatorSubsystem>();
		return (Subsystem && Subsystem->IsInitialized()) ? Subsystem : nullptr;
	}

	return nullptr;
}

#if WITH_EDITOR

void UMeshBlendActivatorSubsystem::OnPreSaveExternalActors(UWorld* World)
{
	check(MeshBlendActivatorLogic);

	for (const UPackage* ExternalPackage : World->PersistentLevel->GetLoadedExternalObjectPackages())
	{
		if (!ExternalPackage->IsDirty())
		{
			continue;
		}

		TArray<UObject*> ExternalObjects;
		GetObjectsWithOuter(ExternalPackage, ExternalObjects);

		for (UObject* ExternalObject : ExternalObjects)
		{
			AActor* Actor = Cast<AActor>(ExternalObject);
			MeshBlendActivatorLogic->ScheduleActorRefresh(Actor, false);
		}
	}
}

#endif

#undef LOCTEXT_NAMESPACE
