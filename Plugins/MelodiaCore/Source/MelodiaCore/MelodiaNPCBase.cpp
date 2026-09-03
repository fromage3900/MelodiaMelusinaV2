#include "MelodiaNPCBase.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"

AMelodiaNPCBase::AMelodiaNPCBase()
{
	PrimaryActorTick.bCanEverTick = false;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	StaticMeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMesh"));
	StaticMeshComponent->SetupAttachment(Root);
	SkeletalMeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SkeletalMesh"));
	SkeletalMeshComponent->SetupAttachment(Root);
}

void AMelodiaNPCBase::BeginPlay()
{
	Super::BeginPlay();
	ApplyNPCDefinition();
}

bool AMelodiaNPCBase::SetNPCDefinition(UMelodiaNPCDefinitionAsset* InDefinition)
{
	NPCDefinition = InDefinition;
	return ApplyNPCDefinition();
}

bool AMelodiaNPCBase::ApplyNPCDefinition()
{
	UMelodiaNPCDefinitionAsset* Resolved = NPCDefinition.LoadSynchronous();
	FText Error;
	if (!Resolved || !Resolved->Definition.IsValid(&Error))
	{
		ApplyFallbackDefinition();
		UE_LOG(LogTemp, Warning, TEXT("Melodia NPC '%s' used fallback definition: %s"), *GetName(), *Error.ToString());
		return false;
	}
	ActiveDefinition = Resolved->Definition;
	UStaticMesh* StaticMesh = ActiveDefinition.StaticMesh.LoadSynchronous();
	USkeletalMesh* SkeletalMesh = ActiveDefinition.SkeletalMesh.LoadSynchronous();
	StaticMeshComponent->SetStaticMesh(StaticMesh);
	StaticMeshComponent->SetVisibility(StaticMesh != nullptr, true);
	SkeletalMeshComponent->SetSkeletalMeshAsset(SkeletalMesh);
	SkeletalMeshComponent->SetVisibility(SkeletalMesh != nullptr, true);
	return true;
}

void AMelodiaNPCBase::ApplyFallbackDefinition()
{
	ActiveDefinition = FMelodiaNPCDef();
	ActiveDefinition.DisplayName = FText::FromString(TEXT("Unconfigured NPC"));
	StaticMeshComponent->SetStaticMesh(nullptr);
	StaticMeshComponent->SetVisibility(false, true);
	SkeletalMeshComponent->SetSkeletalMeshAsset(nullptr);
	SkeletalMeshComponent->SetVisibility(false, true);
}