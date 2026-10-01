// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AMSTypes.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "AMSMapSubsystem.generated.h"

class AAMSMapArea;
class UAMSMapMarkerComponent;
class AAMSActorMarker;
class AAMSMapLocation;
class UAMSMarkersConfigDataAsset;
class UAMSCompassConfigDataAsset;
class UAMSMarkerWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMapMarkerAdded, UAMSMapMarkerComponent*, marker);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMapMarkerRemoved, UAMSMapMarkerComponent*, marker);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTrackedMarkerChanged, UAMSMapMarkerComponent*, marker);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMapAreaChanged, AAMSMapArea*, mapArea);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLocationDiscovered, AAMSMapLocation*, location);

/**
 * Subsystem responsible for managing map areas, locations, and markers across the game.
 * Provides API for retrieving and interacting with in-world locations and map marker components.
 */
UCLASS()
class ASCENTMAPSSYSTEM_API UAMSMapSubsystem : public UGameInstanceSubsystem {
	GENERATED_BODY()

public:
	UAMSMapSubsystem();

	/*Gets the MapArea with the provided name*/
	UFUNCTION(BlueprintCallable, Category = AMS)
	AAMSMapArea* GetRegisteredMapArea(const FName& tag) const;

	/*Returns the current Map Area set with SetCurrentMapArea*/
	UFUNCTION(BlueprintPure, Category = AMS)
	AAMSMapArea* GetCurrentMapArea() const;

	/*Set a map area as the current one to be used */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void SetCurrentMapArea(AAMSMapArea* mapActor);

	/*LOCATIONS*/

	/** Retrieves a specific location by its unique ID */
	UFUNCTION(BlueprintPure, Category = AMS)
	AAMSMapLocation* GetLocationByID(const FName& locationID) const;

	/** Returns all discovered locations in the current map */
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<AAMSMapLocation*> GetAllDiscoveredLocation() const;

	/** Returns all discovered fast travel locations in the current map */
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<AAMSMapLocation*> GetAllDiscoveredFastTravelLocation() const;

	/** Returns all the locations in the current map */
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<AAMSMapLocation*> GetAllLocations() const;

	/*MARKERS*/

	/** Returns all active marker components */
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<UAMSMapMarkerComponent*> GetAllMarkers() const;

	/** Cheat function to mark all locations as discovered */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void DiscoverAllLocation();

	/** Returns whether a specific marker is currently active */
	UFUNCTION(BlueprintPure, Category = AMS)
	bool IsMarkerActive(const UAMSMapMarkerComponent* markerComp) const;

	/** Registers a new map marker component */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void RegisterMarker(class UAMSMapMarkerComponent* markerComp);

	/** Removes a marker component from the map system */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveMarker(class UAMSMapMarkerComponent* markerComp);

	/** Spawns an in-world actor marker at the specified world position */
	UFUNCTION(BlueprintCallable, Category = AMS)
	AAMSActorMarker* SpawnMarkerActor(const TSubclassOf<AAMSActorMarker>& markerClass, const FVector& worldPos, bool bProjectToNavmesh = true);

	/** Removes all actor markers currently spawned in the world */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveAllMarkerActors();

	/** Checks if there is at least one actor marker in the world */
	UFUNCTION(BlueprintPure, Category = AMS)
	bool HasAtLeastOneMarkerActor() const;

	/** Retrieves all markers of a specific gameplay tag category */
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<class UAMSMapMarkerComponent*> GetAllMarkersByCategory(const FGameplayTag& markerComp) const;

	/** Removes all markers matching a specific category tag */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveAllMarkersByCategory(const FGameplayTag& markerComp);

	/** Returns the marker icon configuration asset */
	UFUNCTION(BlueprintCallable, Category = AMS)
	UAMSMarkersConfigDataAsset* GetIconConfig() const;

	/** Broadcast when a new marker is added */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMapMarkerAdded OnMapMarkerAdded;

	/** Broadcast when a marker is removed */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMapMarkerRemoved OnMapMarkerRemoved;

	/** Broadcast when the current map area is changed */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMapAreaChanged OnMapAreaChanged;

	/** Broadcast when a new location is discovered */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnLocationDiscovered OnLocationDiscovered;

	/** Checks if any marker is currently being tracked */
	UFUNCTION(BlueprintPure, Category = AMS)
	bool HasAnyTrackedMarker() const;

	/** Sets a specific marker to be tracked by the map system */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void TrackMarker(UAMSMapMarkerComponent* marker);

	/** Stops tracking the specified marker */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void UntrackMarker();

	UFUNCTION(BlueprintPure, Category = AMS)
	UAMSMapMarkerComponent* GetCurrentlytTrackedMarker() const;

	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnTrackedMarkerChanged OnTrackedMarkerChanged;

	UFUNCTION(BlueprintCallable, Category = AMS)
	void UpdateDiscovererPosition(FVector worldPosition);

	UFUNCTION(BlueprintCallable, Category = AMS)
	TMap<FName, int32> GetAllAreasWithLocalPlayer() const
	{
		return Priorities;
	}

	/*MAP AREAS*/
	void RegisterMapArea(const FName& tag, TObjectPtr<class AAMSMapArea> map);

	void RegisterPlayerInArea(const FName& tag, int32 priority);

	void UnregisterPlayerInArea(const FName& tag);

private:
	TMap<FName, TObjectPtr<AAMSMapArea>> Maps;

	TObjectPtr<AAMSMapArea> currentMap;

	TMap<FName, int32> Priorities;

	TArray<TObjectPtr<UAMSMapMarkerComponent>> Markers;

	TObjectPtr<UAMSMapMarkerComponent> TrackedMarker;
	bool bHasMarkerTracked;

	TArray<TObjectPtr<AAMSActorMarker>> MarkerActors;

	void UpdateCurrentMap();
};
