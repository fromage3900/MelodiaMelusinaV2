// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTags.h"

#include "ACFBuildableEntityComponent.generated.h"

class UACFBuildRecipe;

/** Delegate called when the build process has been completed successfully. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBuilt, APlayerState*, Builder);

/** Delegate called when the buildable has been dismantled. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnDismantled, APlayerController*, Instigator, APlayerState*, Builder);

/**
 * A component that handles the logic for placement, validation, and replication of buildable objects.
 * Can be added to any actor to make it compatible with the building system.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTBUILDINGSYSTEM_API UACFBuildableEntityComponent : public UActorComponent {
    GENERATED_BODY()

public:
    /** Called when the build process completes. */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Building")
    FOnBuilt OnBuilt;

    /** Called when the buildable is dismantled. */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Building")
    FOnDismantled OnDismantled;

    /*Returns the recipe*/
    UFUNCTION(BlueprintPure, Category = ACF)
    UACFBuildRecipe* GetBuildingRecipe() const { return BuildingRecipe; }

    /*Returns the Owner's Player State*/
    UFUNCTION(BlueprintPure, Category = ACF)
    APlayerState* GetBuilderPlayerState() const { return BuilderPlayerState; }

    //Default Constructor
    UACFBuildableEntityComponent();

protected:
    /** PlayerState of the player who built this object (replicated). */
    UPROPERTY(Replicated)
    TObjectPtr<APlayerState> BuilderPlayerState;
    /** PlayerState of the player who built this object (replicated). */
    UPROPERTY(Replicated)
    TObjectPtr<UACFBuildRecipe> BuildingRecipe;

    /** Maximum allowed slope angle in degrees for valid placement */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Building")
    float MaxAllowedSlope = 30.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Building")
    FVector ShapeCollisionMargin = FVector(12.f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Building")
    bool bShowExtentDebug = false;

    /**
     * Collision channels considered as blocking when checking placement.
     * If the overlap box touches any object in these channels, placement is invalid.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Building")
    TArray<TEnumAsByte<ECollisionChannel>> BlockingChannels;

public:
    /**
     * Checks if the current placement position is valid for spawning the buildable object.
     * Override in Blueprint for custom logic.
     * @return True if the placement is valid.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    bool IsPlacementValid() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFBuildingManagerComponent* GetBuildableManager(APawn* Pawn) const;

    /**
     * Builds the associated actor or triggers related build logic.
     * @param BuilderPC - PlayerController of the player who built the object.
     */
    void Build(APlayerController* BuilderPC, UACFBuildRecipe* recipe);

    /**
     * Dismantles the associated buildable and returns items to the instigator's inventory.
     * @param Instigator - The actor initiating the dismantle action, usually the player.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void Dismantle(APlayerController* Instigator);

    UFUNCTION(BlueprintPure, BlueprintNativeEvent, Category = ACF)
    bool CanBeDismantled(APawn* Instigator) const;

    /** Replication setup. */
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
