#include "MelodiaCharacterBase.h"
#include "MelodiaOutfitComponent.h"
#include "MelodiaPartySubsystem.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "EnhancedInputSubsystems.h"

AMelodiaCharacterBase::AMelodiaCharacterBase()
{
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->bUsePawnControlRotation = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	Outfit = CreateDefaultSubobject<UMelodiaOutfitComponent>(TEXT("Outfit"));
}

void AMelodiaCharacterBase::OnPartySwitch()
{
	if (UMelodiaPartySubsystem* Party = UMelodiaPartySubsystem::Get(this))
	{
		Party->SwitchToNext(Cast<APlayerController>(GetController()));
	}
}

void AMelodiaCharacterBase::RemoveMappingContextOnUnpossess(UInputMappingContext* Context) const
{
	if (!Context)
	{
		return;
	}
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (ULocalPlayer* LocalPlayer = PC->GetLocalPlayer())
		{
			if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
			{
				Subsystem->RemoveMappingContext(Context);
			}
		}
	}
}

void AMelodiaCharacterBase::UnPossessed()
{
	Super::UnPossessed();
}
