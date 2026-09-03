#include "MelodiaOpeningPortal.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaAuthorityLocator.h"

AMelodiaOpeningPortal::AMelodiaOpeningPortal()
{
	PrimaryActorTick.bCanEverTick = false;
	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->SetBoxExtent(FVector(180.0f, 180.0f, 180.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));

	PromptText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PromptText"));
	PromptText->SetupAttachment(TriggerVolume);
	PromptText->SetRelativeLocation(FVector(0.0f, 0.0f, 180.0f));
	PromptText->SetText(FText::FromString(TEXT("Wake")));
	PromptText->SetHorizontalAlignment(EHTA_Center);
	PromptText->SetWorldSize(36.0f);
}

void AMelodiaOpeningPortal::BeginPlay()
{
	Super::BeginPlay();
	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AMelodiaOpeningPortal::HandleOverlap);
}

void AMelodiaOpeningPortal::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || (bOneShot && bActivated))
	{
		return;
	}

	if (APawn* Pawn = Cast<APawn>(OtherActor); Pawn && Pawn->IsPlayerControlled())
	{
		UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this);
		if (!Flow || !Flow->ApplyTravelEvent(TravelEvent))
		{
			return;
		}
		bActivated = true;

		// Routed through the authority locator (Decision 030) instead of a bare
		// OpenLevel -- this actor is MelodiaCore-native and cannot reach
		// UMelodiaTravelSubsystem directly (see MelodiaSharedAuthorityInterfaces.h).
		// Falls back to the old direct OpenLevel only if no travel provider has
		// registered, so a missing/misconfigured GameInstance subsystem degrades
		// instead of stranding the player on a one-shot portal that never fires.
		bool bRoutedThroughAuthority = false;
		if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
		{
			TScriptInterface<IMelodiaTravelProvider> Travel = Locator->GetTravelProvider();
			if (Travel.GetObject())
			{
				bRoutedThroughAuthority = Travel->TravelTo(DestinationLevelName, NAME_None);
			}
		}

		if (!bRoutedThroughAuthority)
		{
			UE_LOG(LogTemp, Warning, TEXT("MelodiaOpeningPortal: no travel provider registered, falling back to direct OpenLevel(%s)"),
				*DestinationLevelName.ToString());
			UGameplayStatics::OpenLevel(this, DestinationLevelName);
		}
	}
}
