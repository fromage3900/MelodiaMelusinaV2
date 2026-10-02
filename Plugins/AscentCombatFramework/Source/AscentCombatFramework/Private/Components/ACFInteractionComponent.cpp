// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFInteractionComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFInteractableComponent.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "Logging.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/Actor.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>

// Sets default values for this component's properties
UACFInteractionComponent::UACFInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	SetCollisionResponseToAllChannels(ECR_Ignore);
	SetCollisionEnabled(ECollisionEnabled::NoCollision);
	CollisionChannels.Add(ECollisionChannel::ECC_Pawn);
	SetComponentTickEnabled(true);
	SetIsReplicatedByDefault(true);
}

void UACFInteractionComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFInteractionComponent, CurrentInteractingActor);
}

// Called when the game starts
void UACFInteractionComponent::BeginPlay()
{
	Super::BeginPlay();

	PawnOwner = Cast<APawn>(GetOwner());
	OnComponentBeginOverlap.AddDynamic(this, &UACFInteractionComponent::OnActorEnteredDetector);
	OnComponentEndOverlap.AddDynamic(this, &UACFInteractionComponent::OnActorLeavedDetector);

	if (!PawnOwner) {
		UE_LOG(ACFLog, Error, TEXT("UACFInteractionComponent is Not in a pawn!"));
	}

	if (bAutoEnableOnBeginPlay) {
		EnableDetection(bAutoEnableOnBeginPlay);
	}
}

void UACFInteractionComponent::EnableDetection(bool bIsEnabled)
{
	if (bIsEnabled) {
		InitChannels();
		SetSphereRadius(0.f, false);
		SetSphereRadius(InteractableArea, true);
		SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	}
	else {
		SetCollisionEnabled(ECollisionEnabled::NoCollision);
		interactables.Empty();
	}
	RefreshInteractions();
}

void UACFInteractionComponent::Interact(const FString& interactionType)
{
	if (currentBestInteractableActor) {
		ServerInteract(interactionType, currentBestInteractableActor);
	}
	else {
		UE_LOG(ACFLog, Warning, TEXT("UACFInteractionComponent::Interact: No valid interactable found!"));
	}
}

void UACFInteractionComponent::OnInteracted(const FString& interactionType)
{
	AActor* InteractableActor = CurrentInteractingActor ? CurrentInteractingActor.Get() : currentBestInteractableActor.Get();
	if (!InteractableActor)
	{
		return;
	}

	currentBestInteractableActor = InteractableActor;
	Internal_Interact(interactionType);
	LocalInteract(InteractableActor, interactionType);
}

void UACFInteractionComponent::ServerInteract_Implementation(const FString& interactionType, AActor* bestInteractable)
{
	currentBestInteractableActor = bestInteractable;
	if (!currentBestInteractableActor)
	{
		return;
	}

	// No interface = not interactable. Interface is mandatory.
	if (!currentBestInteractableActor->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
	{
		return;
	}

	bool bCanInteract = IACFInteractableInterface::Execute_CanBeInteracted(currentBestInteractableActor, PawnOwner);

	// Component adds an additional constraint when present
	if (bCanInteract)
	{
		if (UACFInteractableComponent* Comp = currentBestInteractableActor->FindComponentByClass<UACFInteractableComponent>())
		{
			bCanInteract = Comp->CanBeInteracted(PawnOwner);
		}
	}

	if (bCanInteract)
	{
		CurrentInteractingActor = currentBestInteractableActor;

		if (UACFInteractableComponent* Comp = currentBestInteractableActor->FindComponentByClass<UACFInteractableComponent>())
		{
			if (Comp->GetInteractionActionTag().IsValid())
			{
				if (UACFAbilitySystemComponent* AbilityComp = PawnOwner->FindComponentByClass<UACFAbilitySystemComponent>())
				{
					if (AbilityComp->TriggerAction(Comp->GetInteractionActionTag(), EActionPriority::EHigh))
					{
						return;
					}
				}
			}
		}

		OnInteracted(interactionType);
	}
}

void UACFInteractionComponent::ServerInteractOnBehalf_Implementation(
	const FString& interactionType, AActor* bestInteractable, APawn* interactingPawn)
{
	if (!bestInteractable || !interactingPawn)
	{
		return;
	}

	// No interface = not interactable. Interface is mandatory.
	if (!bestInteractable->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
	{
		return;
	}

	bool bCanInteract = IACFInteractableInterface::Execute_CanBeInteracted(bestInteractable, interactingPawn);

	// Component adds an additional constraint when present
	if (bCanInteract)
	{
		if (UACFInteractableComponent* Comp = bestInteractable->FindComponentByClass<UACFInteractableComponent>())
		{
			bCanInteract = Comp->CanBeInteracted(interactingPawn);
		}
	}

	if (!bCanInteract)
	{
		return;
	}

	// Interface first — guaranteed (early-returned above if not implemented)
	IACFInteractableInterface::Execute_OnInteractedByPawn(bestInteractable, interactingPawn, interactionType);

	// Component on top (optional)
	if (UACFInteractableComponent* Comp = bestInteractable->FindComponentByClass<UACFInteractableComponent>())
	{
		Comp->HandleInteractedByPawn(interactingPawn, interactionType);
	}

	UACFInteractionComponent* InteractingPawnComp =
		interactingPawn->FindComponentByClass<UACFInteractionComponent>();
	if (InteractingPawnComp)
	{
		InteractingPawnComp->currentBestInteractableActor = bestInteractable;
		InteractingPawnComp->CurrentInteractingActor = bestInteractable;
		InteractingPawnComp->OnInteractionSucceded.Broadcast(bestInteractable);
	}

	LocalInteract(bestInteractable, interactionType);
}

void UACFInteractionComponent::LocalInteract_Implementation(AActor* bestInteractable, const FString& interactionType)
{
	currentBestInteractableActor = bestInteractable;
	// Set on the owning client for immediate feedback (server already set it in ServerInteract_Implementation).
	// On a listen-server both paths run and set the same value — harmless.
	CurrentInteractingActor = bestInteractable;

	if (currentBestInteractableActor)
	{
		// Component on top (optional)
		if (UACFInteractableComponent* Comp = currentBestInteractableActor->FindComponentByClass<UACFInteractableComponent>())
		{
			Comp->HandleLocalInteractedByPawn(PawnOwner, interactionType);
		}
		// Interface first — guaranteed to be implemented
		IACFInteractableInterface::Execute_OnLocalInteractedByPawn(currentBestInteractableActor, PawnOwner, interactionType);

		OnInteractionSucceded.Broadcast(currentBestInteractableActor);
	}
}

void UACFInteractionComponent::UpdateInteractionArea()
{
	SetSphereRadius(InteractableArea, true);
}

void UACFInteractionComponent::SetCurrentBestInteractable(class AActor* actor)
{
	if (actor == currentBestInteractableActor)
	{
		return;
	}

	// ── Unregister previous ──────────────────────────────────────────────────
	if (currentBestInteractableActor)
	{
		// Interface first (it got here only because it implements the interface)
		IACFInteractableInterface::Execute_OnInteractableUnregisteredByPawn(currentBestInteractableActor, PawnOwner);

		// Component on top (optional)
		if (UACFInteractableComponent* Comp = currentBestInteractableActor->FindComponentByClass<UACFInteractableComponent>())
		{
			Comp->HandleInteractableUnregisteredByPawn(PawnOwner);
		}

		OnInteractableUnregistered.Broadcast(currentBestInteractableActor);
	}

	// ── Register new ─────────────────────────────────────────────────────────
	if (actor)
	{
		// Interface is mandatory — no interface, no registration
		if (!actor->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
		{
			return;
		}

		currentBestInteractableActor = actor;

		// Interface first (mandatory)
		IACFInteractableInterface::Execute_OnInteractableRegisteredByPawn(currentBestInteractableActor, PawnOwner);

		// Component on top (optional)
		if (UACFInteractableComponent* Comp = actor->FindComponentByClass<UACFInteractableComponent>())
		{
			Comp->HandleInteractableRegisteredByPawn(PawnOwner);
		}

		OnInteractableRegistered.Broadcast(actor);
	}
	else
	{
		currentBestInteractableActor = nullptr;
	}
}

void UACFInteractionComponent::OnActorEnteredDetector(UPrimitiveComponent* _overlappedComponent, AActor* _otherActor, UPrimitiveComponent* _otherComp, int32 _otherBodyIndex, bool _bFromSweep, const FHitResult& _SweepResult)
{
	RegisterInteractable(_otherActor);
}

void UACFInteractionComponent::RegisterInteractable(AActor* otherActor)
{
	if (!PawnOwner || !IsValid(otherActor) || otherActor == PawnOwner)
	{
		return;
	}

	// Interface is mandatory — actors without it are never considered interactable
	if (otherActor->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
	{
		interactables.AddUnique(otherActor);
		RefreshInteractions();
	}
}

void UACFInteractionComponent::UnregisterInteractable(AActor* otherActor)
{
	if (interactables.Contains(otherActor)) {
		interactables.Remove(otherActor);
	}
	RefreshInteractions();
}

void UACFInteractionComponent::OnActorLeavedDetector(UPrimitiveComponent* _overlappedComponent, AActor* otherActor, UPrimitiveComponent* _otherComp, int32 _otherBodyIndex)
{
	UnregisterInteractable(otherActor);
}

void UACFInteractionComponent::RefreshInteractions()
{
	AActor* bestActor = nullptr;
	float bestScore = -BIG_NUMBER;

	// Camera forward for directional weighting (local player only)
	FVector CameraForward = FVector::ZeroVector;
	bool bUseCameraWeight = false;
	if (bOffsetTowardCamera && PawnOwner)
	{
		if (const APlayerController* PC = Cast<APlayerController>(PawnOwner->GetController()))
		{
			CameraForward = PC->GetControlRotation().Vector();
			bUseCameraWeight = true;
		}
	}

	for (const TObjectPtr<AActor>& interactable : interactables)
	{
		if (!IsValid(interactable.Get()))
		{
			continue;
		}

		// No interface = not interactable. Interface is mandatory.
		if (!interactable->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
		{
			continue;
		}

		bool bCanInteract = IACFInteractableInterface::Execute_CanBeInteracted(interactable, PawnOwner);

		// Component adds an additional constraint when present
		if (bCanInteract)
		{
			if (UACFInteractableComponent* Comp = interactable->FindComponentByClass<UACFInteractableComponent>())
			{
				bCanInteract = Comp->CanBeInteracted(PawnOwner);
			}
		}

		if (!bCanInteract)
		{
			continue;
		}

		const float distance = FMath::Max(1.f, PawnOwner->GetDistanceTo(interactable));
		float score;

		if (bUseCameraWeight)
		{
			const FVector DirToActor = (interactable->GetActorLocation() - PawnOwner->GetActorLocation()).GetSafeNormal();
			const float dot = FVector::DotProduct(CameraForward, DirToActor);
			score = (dot + 1.1f) / distance;
		}
		else
		{
			score = 1.f / distance;
		}

		if (score > bestScore)
		{
			bestScore = score;
			bestActor = interactable;
		}
	}

	SetCurrentBestInteractable(bestActor);
}

bool UACFInteractionComponent::HasValidInteractable() const
{
	return IsValid(currentBestInteractableActor.Get());
}

void UACFInteractionComponent::Internal_Interact(const FString& interactionType)
{
	if (!currentBestInteractableActor)
	{
		return;
	}

	// Component on top (optional)
	if (UACFInteractableComponent* Comp = currentBestInteractableActor->FindComponentByClass<UACFInteractableComponent>())
	{
		Comp->HandleInteractedByPawn(PawnOwner, interactionType);
	}

	// Interface first — guaranteed to be implemented (gate was checked in ServerInteract)
	IACFInteractableInterface::Execute_OnInteractedByPawn(currentBestInteractableActor, PawnOwner, interactionType);


	OnInteractionSucceded.Broadcast(currentBestInteractableActor);
}

void UACFInteractionComponent::EndInteraction()
{
	if (GetOwnerRole() == ROLE_Authority)
	{
		if (AActor* InteractableActor = CurrentInteractingActor.Get())
		{
			if (UACFInteractableComponent* InteractableComp = InteractableActor->FindComponentByClass<UACFInteractableComponent>())
			{
				InteractableComp->EndInteraction();
			}
		}

		// Server sets to null — DOREPLIFETIME propagates it to all clients automatically.
		CurrentInteractingActor = nullptr;
	}
	else
	{
		// Client path: forward to server so the authoritative null replicates to everyone.
		ServerEndInteraction();
	}
}

void UACFInteractionComponent::ServerEndInteraction_Implementation()
{
	EndInteraction();
}

// Called every frame
void UACFInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bOffsetTowardCamera && CameraForwardOffset > 0.f && PawnOwner)
	{
		if (const APlayerController* PC = Cast<APlayerController>(PawnOwner->GetController()))
		{
			const FVector WorldForward = PC->GetControlRotation().Vector();
			SetWorldLocation(PawnOwner->GetActorLocation() + WorldForward * CameraForwardOffset);
		}
	}

	RefreshInteractions();
}

void UACFInteractionComponent::AddCollisionChannel(TEnumAsByte<ECollisionChannel> inTraceChannel)
{
	if (!CollisionChannels.Contains(inTraceChannel)) {
		CollisionChannels.Add(inTraceChannel);
		InitChannels();
	}
}

void UACFInteractionComponent::RemoveCollisionChannel(TEnumAsByte<ECollisionChannel> inTraceChannel)
{
	if (CollisionChannels.Contains(inTraceChannel)) {
		CollisionChannels.Remove(inTraceChannel);
		InitChannels();
	}
}

void UACFInteractionComponent::InitChannels()
{
	SetCollisionResponseToAllChannels(ECR_Ignore);
	SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	for (const auto& channel : CollisionChannels) {
		SetCollisionResponseToChannel(channel, ECR_Overlap);
	}
}
