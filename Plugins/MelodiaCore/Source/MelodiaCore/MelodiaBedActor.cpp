#include "MelodiaBedActor.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaSaveGameSubsystem.h"
#include "UObject/ConstructorHelpers.h"

AMelodiaBedActor::AMelodiaBedActor()
{
	PrimaryActorTick.bCanEverTick = false;

	BedMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BedMesh"));
	SetRootComponent(BedMesh);
	BedMesh->SetCollisionProfileName(TEXT("BlockAll"));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ProxyMeshFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (ProxyMeshFinder.Succeeded())
	{
		BedMesh->SetStaticMesh(ProxyMeshFinder.Object);
		BedMesh->SetRelativeScale3D(FVector(2.0f, 1.0f, 0.5f));
	}

	InteractionTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionTrigger"));
	InteractionTrigger->SetupAttachment(BedMesh);
	InteractionTrigger->SetBoxExtent(FVector(110.0f, 60.0f, 60.0f));
	InteractionTrigger->SetCollisionProfileName(TEXT("Trigger"));
}

void AMelodiaBedActor::BeginPlay()
{
	Super::BeginPlay();
	SaveSubsystem = UMelodiaSaveGameSubsystem::Get(this);
	if (SaveSubsystem)
	{
		SaveSubsystem->OnSaveCompleted.AddUniqueDynamic(this, &AMelodiaBedActor::HandleSaveCompleted);
	}
	InteractionTrigger->OnComponentBeginOverlap.AddUniqueDynamic(this, &AMelodiaBedActor::HandleInteractionOverlap);
}

void AMelodiaBedActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (SaveSubsystem)
	{
		SaveSubsystem->OnSaveCompleted.RemoveDynamic(this, &AMelodiaBedActor::HandleSaveCompleted);
	}
	Super::EndPlay(EndPlayReason);
}

void AMelodiaBedActor::HandleInteractionOverlap(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!PlayerPawn || OtherActor != PlayerPawn || !PlayerPawn->IsPlayerControlled())
	{
		return;
	}

	PresentSleepBeat();

	if (bSaveOnInteract && SaveSubsystem)
	{
		SaveSubsystem->SaveGame();
	}
}

void AMelodiaBedActor::HandleSaveCompleted(const bool bSuccess)
{
	PresentSaveCompleted(bSuccess);
}
