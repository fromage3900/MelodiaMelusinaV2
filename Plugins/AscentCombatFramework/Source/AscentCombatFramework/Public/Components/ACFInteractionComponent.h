// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include <Components/SphereComponent.h>

#include "ACFInteractionComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnInteractableRegistered, AActor*, interctableActor);

UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFInteractionComponent : public USphereComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFInteractionComponent();

	/* Interacts with the best interactable nearby, calling both the server and client functions */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void Interact(const FString& interactionType = "");

	void OnInteracted(const FString& interactionType = "");

	/* Sets the current best interactable actor */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCurrentBestInteractable(class AActor* actor);

	/* Retrieves the current best interactable actor */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE AActor* GetCurrentBestInteractableActor() const { return currentBestInteractableActor.Get(); }

	/* Returns the actor currently being actively interacted with (set at interaction start, cleared on EndInteraction) */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE AActor* GetCurrentInteractingActor() const { return CurrentInteractingActor.Get(); }

	/** Clears the active interaction, resetting CurrentInteractingActor to null.
	 *  Safe to call from both server and client: if called on a client it forwards to the server
	 *  via a reliable RPC so the null is authoritative and replicates back to all machines. */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void EndInteraction();

	/* Enables or disables interaction detection */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void EnableDetection(bool bIsEnabled);

	/* Adds a collision channel to be considered for interaction */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddCollisionChannel(TEnumAsByte<ECollisionChannel> inTraceChannel);

	/* Removes a collision channel from the list of considered interactions */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RemoveCollisionChannel(TEnumAsByte<ECollisionChannel> inTraceChannel);

	/* Refreshes the list of available interactables */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RefreshInteractions();

	/* Checks if there is a valid interactable available */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool HasValidInteractable() const;

	/* Routes an interaction through this component's connection on behalf of another pawn
	(e.g., the rider character after a possession swap to the mount). */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void ServerInteractOnBehalf(const FString& interactionType, AActor* bestInteractable, APawn* interactingPawn);


	/* Event triggered when an interactable is registered */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnInteractableRegistered OnInteractableRegistered;

	/* Event triggered when an interactable is unregistered */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnInteractableRegistered OnInteractableUnregistered;

	/* Event triggered when an interaction is successfully completed */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnInteractableRegistered OnInteractionSucceded;

	UFUNCTION(BlueprintCallable, Category = ACF)
	void RegisterInteractable(AActor* otherActor);

	UFUNCTION(BlueprintCallable, Category = ACF)
	void UnregisterInteractable(AActor* otherActor);

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	/*Channels used to check for interactable objects*/
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACF)
	TArray<TEnumAsByte<ECollisionChannel>> CollisionChannels;

	UPROPERTY(EditDefaultsOnly, Category = ACF)
	float InteractableArea = 180.f;

	UPROPERTY(EditDefaultsOnly, Category = ACF)
	bool bAutoEnableOnBeginPlay = false;

	/**
	 * Fixed distance (cm) by which the sphere center is shifted toward the camera look direction.
	 * Only the camera's direction is used — position and zoom distance have no effect.
	 * Set to 0 to keep the sphere centered on the pawn (default behavior).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF, meta = (ClampMin = "0.0"))
	float CameraForwardOffset = 60.f;

	/**
	 * When true, the sphere center tracks the camera look direction every tick.
	 * Has no effect on AI or dedicated server (no PlayerController available).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bOffsetTowardCamera = false;

	UPROPERTY(Transient)
	TObjectPtr<AActor> currentBestInteractableActor;

	/** The actor currently being actively interacted with. Replicated so both server and all clients are aware.
	 *  Set at interaction start (server + client), cleared by EndInteraction() or as fallback when no interactable is nearby. */
	UPROPERTY(Replicated, Transient, BlueprintReadOnly, Category = ACF)
	TObjectPtr<AActor> CurrentInteractingActor;

public:
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY()
	TObjectPtr<APawn> PawnOwner;

	UFUNCTION(Server, Reliable)
	void ServerInteract(const FString& interactionType = "", AActor* bestInteractable = nullptr);

	UFUNCTION(Client, Reliable)
	void LocalInteract(AActor* bestInteractable, const FString& interactionType = "");

	/** Server-side clear forwarded from EndInteraction() when called on a client. */
	UFUNCTION(Server, Reliable)
	void ServerEndInteraction();

	// UPROPERTY()
	class IACFInteractableInterface* currentBestInteractable;



	UPROPERTY()
	TArray<TObjectPtr<AActor>> interactables;

	UFUNCTION()
	void UpdateInteractionArea();

	void InitChannels();

	UFUNCTION()
	void OnActorEnteredDetector(UPrimitiveComponent* _overlappedComponent,
		AActor* _otherActor, UPrimitiveComponent* _otherComp, int32 _otherBodyIndex,
		bool _bFromSweep, const FHitResult& _SweepResult);

	UFUNCTION()
	void OnActorLeavedDetector(UPrimitiveComponent* _overlappedComponent,
		AActor* _otherActor, UPrimitiveComponent* _otherComp, int32 _otherBodyIndex);

	void Internal_Interact(const FString& interactionType = "");
};
