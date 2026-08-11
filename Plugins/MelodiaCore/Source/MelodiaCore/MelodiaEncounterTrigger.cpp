// Encounter trigger ΓÇö overlap volume that starts a rhythm battle.

#include "MelodiaEncounterTrigger.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Character.h"
#include "Materials/MaterialInterface.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

AMelodiaEncounterTrigger::AMelodiaEncounterTrigger()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	TriggerVolume->SetBoxExtent(FVector(200.0f, 200.0f, 150.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	TriggerVolume->SetGenerateOverlapEvents(true);
	RootComponent = TriggerVolume;

	EncounterLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("EncounterLabel"));
	EncounterLabel->SetupAttachment(RootComponent);
	EncounterLabel->SetRelativeLocation(FVector(0.0f, 0.0f, 165.0f));
	EncounterLabel->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
	EncounterLabel->SetHorizontalAlignment(EHTA_Center);
	EncounterLabel->SetVerticalAlignment(EVRTA_TextCenter);
	EncounterLabel->SetTextRenderColor(FColor(255, 220, 96));
	EncounterLabel->SetWorldSize(34.0f);
	EncounterLabel->SetText(FText::FromString(TEXT("Encounter")));

	EncounterLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("EncounterLight"));
	EncounterLight->SetupAttachment(RootComponent);
	EncounterLight->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));
	EncounterLight->SetLightColor(FLinearColor(1.0f, 0.78f, 0.28f));
	EncounterLight->SetIntensity(900.0f);
	EncounterLight->SetAttenuationRadius(420.0f);

	EnemyPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EnemyPresentation"));
	EnemyPresentation->SetupAttachment(RootComponent);
	EnemyPresentation->SetRelativeLocation(FVector(0.0f, 0.0f, 70.0f));
	EnemyPresentation->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	EnemyPresentation->SetVisibility(false);

}

bool AMelodiaEncounterTrigger::StartEncounterForPlayer()
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	ACharacter* PlayerCharacter = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!PlayerCharacter || !PlayerCharacter->IsPlayerControlled() || (bOneShot && bTriggered))
	{
		return false;
	}
	const double CurrentTime = FPlatformTime::Seconds();
	if (CurrentTime - LastTriggerTime < CooldownSeconds)
	{
		return false;
	}
	if (TryStartStockJRPGBattle())
	{
		bTriggered = true;
		LastTriggerTime = CurrentTime;
		return true;
	}
	UE_LOG(LogTemp, Warning, TEXT("Melodia: Stock JRPG bridge refused encounter %s; no fallback battle will be created."), *EnemyId.ToString());
	return false;
}

bool AMelodiaEncounterTrigger::TryStartStockJRPGBattle()
{
	if (!bPreferStockJRPGPresentation || EnemyId.IsNone())
	{
		return false;
	}
	UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr;
	UClass* BridgeClass = FindObject<UClass>(nullptr, TEXT("/Script/BS_GodFile.MelodiaExternalJRPGBridgeSubsystem"));
	if (!GameInstance || !BridgeClass)
	{
		return false;
	}
	UGameInstanceSubsystem* Bridge = GameInstance->GetSubsystemBase(BridgeClass);
	UFunction* StartFunction = Bridge ? Bridge->FindFunction(TEXT("StartTaggedJRPGBattle")) : nullptr;
	if (!StartFunction)
	{
		return false;
	}
	FStructOnScope Parameters(StartFunction);
	FNameProperty* EncounterParameter = FindFProperty<FNameProperty>(StartFunction, TEXT("EncounterId"));
	FBoolProperty* ReturnValue = FindFProperty<FBoolProperty>(StartFunction, TEXT("ReturnValue"));
	if (!EncounterParameter || !ReturnValue)
	{
		return false;
	}
	EncounterParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), FName(*FString::Printf(TEXT("Encounter_%s"), *EnemyId.ToString())));
	Bridge->ProcessEvent(StartFunction, Parameters.GetStructMemory());
	return ReturnValue->GetPropertyValue_InContainer(Parameters.GetStructMemory());
}

void AMelodiaEncounterTrigger::ConfigureEnemyPresentation(const FMelodiaEnemyDef& Enemy)
{
	if (!EnemyPresentation)
	{
		return;
	}

	if (!Enemy.DisplayMesh.IsNull())
	{
		if (UStaticMesh* Mesh = Enemy.DisplayMesh.LoadSynchronous())
		{
			EnemyPresentation->SetStaticMesh(Mesh);
		}
	}
	if (!Enemy.DisplayMaterial.IsNull())
	{
		if (UMaterialInterface* Material = Enemy.DisplayMaterial.LoadSynchronous())
		{
			EnemyPresentation->SetMaterial(0, Material);
		}
	}
	EnemyPresentation->SetRelativeScale3D(FVector(FMath::Max(0.01f, Enemy.MeshScale)));
	SetEnemyPresentationVisible(EnemyPresentation->GetStaticMesh() != nullptr);
}

void AMelodiaEncounterTrigger::SetEnemyPresentationVisible(const bool bVisible)
{
	if (EnemyPresentation)
	{
		EnemyPresentation->SetVisibility(bVisible);
	}
}

void AMelodiaEncounterTrigger::BeginPlay()
{
	Super::BeginPlay();

	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AMelodiaEncounterTrigger::OnTriggerOverlap);
}

void AMelodiaEncounterTrigger::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (EncounterLabel)
	{
		EncounterLabel->SetText(EncounterDisplayName.IsEmpty()
			? FText::FromString(TEXT("Encounter"))
			: EncounterDisplayName);
	}
}

void AMelodiaEncounterTrigger::OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	// Only trigger on player character
	if (!OtherActor || !OtherActor->IsA<ACharacter>())
	{
		return;
	}

	// One-shot check
	if (bOneShot && bTriggered)
	{
		return;
	}

	// Cooldown check
	const double CurrentTime = FPlatformTime::Seconds();
	if (CurrentTime - LastTriggerTime < CooldownSeconds)
	{
		return;
	}

	if (TryStartStockJRPGBattle())
	{
		bTriggered = true;
		LastTriggerTime = CurrentTime;
		UE_LOG(LogTemp, Log, TEXT("Melodia: Encounter routed to tagged stock JRPG battle (%s)."), *EnemyId.ToString());
		return;
	}

	UE_LOG(LogTemp, Warning, TEXT("Melodia: Stock JRPG bridge refused encounter %s; no fallback battle will be created."), *EnemyId.ToString());
}
