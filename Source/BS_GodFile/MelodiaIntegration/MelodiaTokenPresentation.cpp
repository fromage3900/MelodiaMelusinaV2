#include "MelodiaTokenPresentation.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextBlock.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/RotatingMovementComponent.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	bool IsEligibleCollector(const AActor* Actor)
	{
		const APawn* Pawn = Cast<APawn>(Actor);
		if (!IsValid(Pawn) || !Pawn->IsPlayerControlled())
		{
			return false;
		}

		return Pawn->ActorHasTag(TEXT("Melusina"))
			|| Pawn->GetClass()->GetName().Contains(TEXT("Melusina"), ESearchCase::IgnoreCase);
	}

	void SetCount(UTextBlock* Text, const FMelodiaWalletSnapshot& Snapshot, const FName Element)
	{
		if (Text)
		{
			Text->SetText(FText::AsNumber(Snapshot.Shards.FindRef(Element)));
		}
	}
}

AMelodiaTokenPickup::AMelodiaTokenPickup()
{
	PrimaryActorTick.bCanEverTick = false;

	CollectionVolume = CreateDefaultSubobject<USphereComponent>(TEXT("CollectionVolume"));
	SetRootComponent(CollectionVolume);
	CollectionVolume->InitSphereRadius(90.0f);
	CollectionVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	CollectionVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
	CollectionVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

	TokenMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TokenMesh"));
	TokenMesh->SetupAttachment(CollectionVolume);
	TokenMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TokenMesh->SetRelativeScale3D(FVector(0.35f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		TokenMesh->SetStaticMesh(SphereMesh.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> HeartMaterial(
		TEXT("/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart.MI_MelodyToken_Heart"));
	if (HeartMaterial.Succeeded())
	{
		TokenMesh->SetMaterial(0, HeartMaterial.Object);
	}

	Rotation = CreateDefaultSubobject<URotatingMovementComponent>(TEXT("Rotation"));
	Rotation->RotationRate = FRotator(0.0f, 60.0f, 0.0f);
}

void AMelodiaTokenPickup::BeginPlay()
{
	Super::BeginPlay();
	CollectionVolume->OnComponentBeginOverlap.AddUniqueDynamic(this, &ThisClass::HandleBeginOverlap);

	if (UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);
		Wallet && !GrantId.IsNone() && Wallet->IsGrantConsumed(GrantId))
	{
		EnterCollectedPresentation();
	}
	else if (GrantId.IsNone())
	{
		UE_LOG(LogTemp, Error,
			TEXT("Melodia token pickup %s has no stable GrantId; collection is disabled to prevent duplicate grants."),
			*GetPathName());
	}
}

void AMelodiaTokenPickup::HandleBeginOverlap(UPrimitiveComponent*, AActor* OtherActor,
	UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (bCollectOnOverlap)
	{
		TryCollect(OtherActor);
	}
}

bool AMelodiaTokenPickup::TryInteract(AActor* InteractingActor)
{
	return TryCollect(InteractingActor);
}

bool AMelodiaTokenPickup::TryCollect(AActor* CollectingActor)
{
	if (bCollectionAccepted || GrantId.IsNone() || Amount <= 0 || !IsEligibleCollector(CollectingActor)
		|| !UMelodiaTokenWalletSubsystem::GetElementNames().Contains(Element))
	{
		return false;
	}

	UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);
	if (!Wallet || !Wallet->TryGrantShards(Element, Amount, GrantId))
	{
		return false;
	}

	bCollectionAccepted = true;
	EnterCollectedPresentation();
	OnCollected.Broadcast(CollectingActor);
	return true;
}

void AMelodiaTokenPickup::EnterCollectedPresentation()
{
	bCollectionAccepted = true;
	CollectionVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TokenMesh->SetVisibility(false, true);
	SetActorEnableCollision(false);
}

void UMelodiaWalletHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this))
	{
		Wallet->OnWalletChanged.AddUniqueDynamic(this, &ThisClass::HandleWalletChanged);
	}
	RefreshFromWallet();
}

void UMelodiaWalletHUDWidget::NativeDestruct()
{
	if (UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this))
	{
		Wallet->OnWalletChanged.RemoveDynamic(this, &ThisClass::HandleWalletChanged);
	}
	Super::NativeDestruct();
}

void UMelodiaWalletHUDWidget::RefreshFromWallet()
{
	if (const UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this))
	{
		PresentSnapshot(Wallet->GetSnapshot());
	}
}

void UMelodiaWalletHUDWidget::HandleWalletChanged(const FMelodiaWalletSnapshot& NewSnapshot)
{
	PresentSnapshot(NewSnapshot);
}

void UMelodiaWalletHUDWidget::PresentSnapshot(const FMelodiaWalletSnapshot& NewSnapshot)
{
	Snapshot = NewSnapshot;
	SetCount(TXT_Forte, Snapshot, TEXT("Forte"));
	SetCount(TXT_Tide, Snapshot, TEXT("Tide"));
	SetCount(TXT_Gale, Snapshot, TEXT("Gale"));
	SetCount(TXT_Stone, Snapshot, TEXT("Stone"));
	SetCount(TXT_Radiant, Snapshot, TEXT("Radiant"));
	SetCount(TXT_Umbral, Snapshot, TEXT("Umbral"));
	SetCount(TXT_Arcane, Snapshot, TEXT("Arcane"));

	if (TXT_Mana)
	{
		TXT_Mana->SetText(FText::Format(NSLOCTEXT("Melodia", "WalletMana", "{0} / {1}"),
			FText::AsNumber(Snapshot.ManaCurrent), FText::AsNumber(Snapshot.ManaMax)));
	}
	if (TXT_GoldenTokens)
	{
		TXT_GoldenTokens->SetText(FText::AsNumber(Snapshot.GoldenTokens));
	}
	if (TXT_TotalCollected)
	{
		TXT_TotalCollected->SetText(FText::AsNumber(Snapshot.TotalCollected));
	}

	OnSnapshotPresented.Broadcast(Snapshot);
}
