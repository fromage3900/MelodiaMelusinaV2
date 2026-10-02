// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ANSWidgetInteractionComponent.h"
#include <CommonInputSubsystem.h>
#include "Engine/LocalPlayer.h"
#include <GameFramework/PlayerController.h>
#include <Engine/World.h>

UANSWidgetInteractionComponent::UANSWidgetInteractionComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	InteractionDistance = 10000.0f;

	PrimaryComponentTick.bCanEverTick = true;
}

void UANSWidgetInteractionComponent::SetInteractionEnabled(bool bEnabled)
{
	if (bIsInteractionEnabled == bEnabled)
	{
		return;
	}

	bIsInteractionEnabled = bEnabled;
	SetComponentTickEnabled(bEnabled);

	OnInteractionStateChanged.Broadcast(bIsInteractionEnabled);
}

void UANSWidgetInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (PlayerController && bIsInteractionEnabled && !bIsUsingGamepad)
	{
		FVector WorldLocation;
		FVector WorldDirection;

		const bool bSuccess = PlayerController->DeprojectMousePositionToWorld(WorldLocation, WorldDirection);

		if (bSuccess)
		{
			const FRotator NewRotation = WorldDirection.Rotation();
			SetWorldLocationAndRotation(WorldLocation, NewRotation);
		}
	}
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

void UANSWidgetInteractionComponent::BeginPlay()
{
	Super::BeginPlay();
	PlayerController = GetWorld()->GetFirstPlayerController();
	SetInteractionEnabled(bIsInteractionEnabled);

	UCommonInputSubsystem* commonInputSub = GetInputSubsystem();
	if (commonInputSub) {
		commonInputSub->OnInputMethodChangedNative.AddUObject(this, &UANSWidgetInteractionComponent::HandleInputChanged);
		HandleInputChanged(commonInputSub->GetCurrentInputType());
	}
}

void UANSWidgetInteractionComponent::HandleInputChanged(ECommonInputType inputType)
{
	bIsUsingGamepad = (inputType == ECommonInputType::Gamepad);

}


UCommonInputSubsystem* UANSWidgetInteractionComponent::GetInputSubsystem() const
{
	if (PlayerController && PlayerController->GetLocalPlayer()) {
		const ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer();
		return LocalPlayer->GetSubsystem<UCommonInputSubsystem>();
	}
	return nullptr;
}