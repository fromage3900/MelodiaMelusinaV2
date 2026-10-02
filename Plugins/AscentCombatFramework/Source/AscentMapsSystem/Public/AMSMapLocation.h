// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "AMSMapLocation.generated.h"

class UAMSMapMarkerComponent;
class USphereComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnDiscovered);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnFastTravel);

/**
 * @class ACFLocation
 * Represents a location in the game world, supporting discovery and fast travel functionality.
 */

UCLASS()
class ASCENTMAPSSYSTEM_API AAMSMapLocation : public AActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AAMSMapLocation();

    /**
     * Retrieves the ID of the location.
     * @return FString The ID of the location.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FString GetLocationID() const;

    /**
     * Retrieves the Localizable name of the location.
     * @return FString The Localizable name of the location.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FText GetLocationUIName() const;

    /**
     * Sets a new UI name for the location.
     * @param newName The new name to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetLocationUIName(const FText& newName);
    /**
     * Sets a new ID for the location.
     * @param newName The new ID to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetLocationID(const FString& newID);

    /**
     * Marks the location as discovered.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void DiscoverLocation(const APawn* pawn);

    /**
     * Sets the discovered state of the location.
     * @param newState True to mark the location as discovered, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetDiscoveredState(bool newState);

    /**
     * Checks if the location has been discovered.
     * @return True if discovered, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsDiscovered() const { return bDiscovered; }

    /**
     * Determines if the location allows fast travel.
     * @return True if fast travel is allowed, false otherwise.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool CanFastTravel() const;
    virtual bool CanFastTravel_Implementation() const;

    /**
     * Teleports the current player to the designated fast travel location.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void FastTraverlToLocation();

    /**
     * Gets the location point where the player will be teleported.
     * @return FVector The coordinates of the fast travel point.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FVector GetFastTravelPoint() const;

    /**
     * Retrieves the marker component of the location.
     * @return A pointer to the AMSMapMarkerComponent associated with this location.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UAMSMapMarkerComponent* GetMarkerComponent() const
    {
        return MarkerComp;
    }

    /**
     * Retrieves the discoverable area component.
     * @return A pointer to the USphereComponent that defines the discovery area.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    USphereComponent* GetDiscoverAreaComponent() const
    {
        return SphereComp;
    }

    /** Event triggered when fast travel occurs. */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnFastTravel OnFastTravelEvent;

    /** Event triggered when the location is discovered. */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnDiscovered OnDiscoveredEvent;

protected:
    /**
     * Called when the game starts or the actor is spawned.
     */
    virtual void BeginPlay() override;

    /** Defines the area where the player must enter to discover the location. */
    UPROPERTY(VisibleAnywhere, DisplayName = "Discover Area Component", Category = "AMS")
    TObjectPtr<USphereComponent> SphereComp;

    /** Holds a marker component for the location. */
    UPROPERTY(VisibleAnywhere, DisplayName = "AMS Marker Component", Category = "AMS")
    TObjectPtr<UAMSMapMarkerComponent> MarkerComp;

    /** Determines whether the location should be discovered when the player overlaps with it. */
    UPROPERTY(EditAnywhere, Category = "AMS")
    bool bDiscoverOnPlayerOverlap = true;

    /** Indicates whether this location supports fast travel. */
    UPROPERTY(EditAnywhere, Category = "AMS")
    bool bCanFastTravel = false;

    /** Specifies the location the player will be teleported to during fast travel. */
    UPROPERTY(EditAnywhere, meta = (MakeEditWidget), meta = (EditCondition = "bCanFastTravel"), Category = "AMS")
    FVector FastTravelLocation;

    /**
     * Called when the location is discovered.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnDiscovered(const APawn* pawn);

    /**
     * Called when the player is teleported to this location.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnTeleported();

private:
    UPROPERTY(Savegame)
    bool bDiscovered = false;

    UFUNCTION()
    void HandleLocalPlayerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void HandleOverlapEnds( UPrimitiveComponent*  OnComponentEndOverlap, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

};
