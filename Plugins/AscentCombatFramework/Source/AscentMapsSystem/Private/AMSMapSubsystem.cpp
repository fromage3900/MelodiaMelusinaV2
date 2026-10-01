// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapSubsystem.h"
#include "AMSActorMarker.h"
#include "AMSDeveloperSettings.h"
#include "AMSMapArea.h"
#include "AMSMapLocation.h"
#include "AMSMapMarkerComponent.h"
#include "AMSMarkerWidget.h"
#include "GameplayTagContainer.h"
#include "Kismet/GameplayStatics.h"

UAMSMapSubsystem::UAMSMapSubsystem()
{
    bHasMarkerTracked = false;
}

void UAMSMapSubsystem::RegisterMapArea(const FName& tag, TObjectPtr<class AAMSMapArea> map)
{
    Maps.Add(tag, map);
}

void UAMSMapSubsystem::RegisterPlayerInArea(const FName& tag, int32 priority)
{
    Priorities.Add(tag, priority);
    UpdateCurrentMap();
}

void UAMSMapSubsystem::RegisterMarker(class UAMSMapMarkerComponent* markerComp)
{
    if (markerComp && !Markers.Contains(markerComp)) {
        Markers.AddUnique(markerComp);
        if (markerComp->GetActivateWorldWidget()) {
            markerComp->SetHiddenInGame(false, true);
        }
        OnMapMarkerAdded.Broadcast(markerComp);
    }
}

void UAMSMapSubsystem::RemoveMarker(class UAMSMapMarkerComponent* markerComp)
{
    if (Markers.Contains(markerComp)) {
        Markers.Remove(markerComp);
        if (markerComp->GetActivateWorldWidget()) {
            markerComp->SetHiddenInGame(true, true);
        }
        OnMapMarkerRemoved.Broadcast(markerComp);
    }
}

AAMSActorMarker* UAMSMapSubsystem::SpawnMarkerActor(const TSubclassOf<AAMSActorMarker>& markerClass, const FVector& worldPos, bool bProjectToNavmesh)
{
    FVector finalPos = worldPos;
    //     if (bProjectToNavmesh) {
    //         FVector outLoc;
    //         if (UNavigationSystemV1::K2_ProjectPointToNavigation(GetWorld(),worldPos, outLoc, nullptr, nullptr)) {
    //             finalPos = outLoc;
    //         }
    //     }
    AAMSActorMarker* newMarker = GetWorld()->SpawnActor<AAMSActorMarker>(markerClass, finalPos, FRotator::ZeroRotator);
    MarkerActors.Add(newMarker);
    return newMarker;
}

void UAMSMapSubsystem::RemoveAllMarkerActors()
{
    TArray<TObjectPtr<AAMSActorMarker>> MarkerActorsCopy = MarkerActors;
    for (const auto& marker : MarkerActorsCopy) {
        marker->Destroy(true);
    }
    MarkerActors.Empty();
}

bool UAMSMapSubsystem::HasAtLeastOneMarkerActor() const
{
    return MarkerActors.Num() > 0 && IsValid(MarkerActors[0]);
}

TArray<UAMSMapMarkerComponent*> UAMSMapSubsystem::GetAllMarkersByCategory(const FGameplayTag& categoryTag) const
{
    TArray<UAMSMapMarkerComponent*> outMarkers;

    for (UAMSMapMarkerComponent* markerComp : Markers) {
        if (markerComp->GetMarkerCategory().HasTag(categoryTag)) {
            outMarkers.Add(markerComp);
        }
    }
    return outMarkers;
}

void UAMSMapSubsystem::RemoveAllMarkersByCategory(const FGameplayTag& categoryTag)
{
    const TArray<UAMSMapMarkerComponent*> outMarkers = GetAllMarkersByCategory(categoryTag);
    for (UAMSMapMarkerComponent* markerComp : outMarkers) {
        RemoveMarker(markerComp);
    }
}

// UAMSCompassConfigDataAsset* UAMSMapSubsystem::GetCompassConfig() const
// {
//     UAMSDeveloperSettings* settings = GetMutableDefault<UAMSDeveloperSettings>();
//     if (settings) {
//         return settings->GetCompassConfig();
//     }
//     return nullptr;
// }

UAMSMarkersConfigDataAsset* UAMSMapSubsystem::GetIconConfig() const
{
    UAMSDeveloperSettings* settings = GetMutableDefault<UAMSDeveloperSettings>();
    if (settings) {
        return settings->GetMarkerIconConfig();
    }
    return nullptr;
}

void UAMSMapSubsystem::UnregisterPlayerInArea(const FName& tag)
{
    Priorities.Remove(tag);
    UpdateCurrentMap();
}

AAMSMapArea* UAMSMapSubsystem::GetRegisteredMapArea(const FName& tag) const
{
    if (Maps.Contains(tag)) {
        return Maps.FindChecked(tag);
    }
    return nullptr;
}

AAMSMapArea* UAMSMapSubsystem::GetCurrentMapArea() const
{
    return currentMap;
}

void UAMSMapSubsystem::SetCurrentMapArea(AAMSMapArea* mapActor)
{
    currentMap = mapActor;
    OnMapAreaChanged.Broadcast(mapActor);
}

TArray<AAMSMapLocation*> UAMSMapSubsystem::GetAllLocations() const
{
    TArray<AActor*> outLocs;
    TArray<AAMSMapLocation*> finalLocs;
    UGameplayStatics::GetAllActorsOfClass(this, AAMSMapLocation::StaticClass(), outLocs);

    for (const auto& loc : outLocs) {
        AAMSMapLocation* mapLoc = Cast<AAMSMapLocation>(loc);
        if (mapLoc) {
            finalLocs.Add(mapLoc);
        }
    }
    return finalLocs;
}

AAMSMapLocation* UAMSMapSubsystem::GetLocationByID(const FName& locationName) const
{
    TArray<AActor*> outLocs;
    UGameplayStatics::GetAllActorsOfClass(this, AAMSMapLocation::StaticClass(), outLocs);

    for (const auto& loc : outLocs) {
        AAMSMapLocation* mapLoc = Cast<AAMSMapLocation>(loc);
        if (mapLoc && mapLoc->GetLocationID() == locationName) {
            return mapLoc;
        }
    }
    return nullptr;
}

TArray<AAMSMapLocation*> UAMSMapSubsystem::GetAllDiscoveredLocation() const
{
    TArray<AActor*> outLocs;
    TArray<AAMSMapLocation*> finalLocs;
    UGameplayStatics::GetAllActorsOfClass(this, AAMSMapLocation::StaticClass(), outLocs);

    for (const auto& loc : outLocs) {
        AAMSMapLocation* mapLoc = Cast<AAMSMapLocation>(loc);
        if (mapLoc && mapLoc->IsDiscovered()) {
            finalLocs.Add(mapLoc);
        }
    }
    return finalLocs;
}

TArray<AAMSMapLocation*> UAMSMapSubsystem::GetAllDiscoveredFastTravelLocation() const
{
    TArray<AActor*> outLocs;
    TArray<AAMSMapLocation*> finalLocs;
    UGameplayStatics::GetAllActorsOfClass(this, AAMSMapLocation::StaticClass(), outLocs);

    for (const auto& loc : outLocs) {
        AAMSMapLocation* mapLoc = Cast<AAMSMapLocation>(loc);
        if (mapLoc && mapLoc->IsDiscovered() && mapLoc->CanFastTravel()) {
            finalLocs.Add(mapLoc);
        }
    }
    return finalLocs;
}

TArray<class UAMSMapMarkerComponent*> UAMSMapSubsystem::GetAllMarkers() const
{
    return Markers;
}

void UAMSMapSubsystem::DiscoverAllLocation()
{
    TArray<AActor*> outLocs;
    UGameplayStatics::GetAllActorsOfClass(this, AAMSMapLocation::StaticClass(), outLocs);

    for (const auto& loc : outLocs) {
        AAMSMapLocation* mapLoc = Cast<AAMSMapLocation>(loc);
        if (mapLoc) {
            mapLoc->SetDiscoveredState(true);
        }
    }
}

bool UAMSMapSubsystem::IsMarkerActive(const class UAMSMapMarkerComponent* markerComp) const
{
    return Markers.Contains(markerComp);
}

void UAMSMapSubsystem::UpdateCurrentMap()
{
    int32 currentMax = 0;
    FName bestMap;
    for (auto& map : Priorities) {
        if (map.Value > currentMax) {
            currentMax = map.Value;
            bestMap = map.Key;
        }
    }

    const auto newMap = GetRegisteredMapArea(bestMap);
    if (newMap != currentMap) {
        currentMap = newMap;
        OnMapAreaChanged.Broadcast(currentMap);
    }
}

bool UAMSMapSubsystem::HasAnyTrackedMarker() const
{
    return bHasMarkerTracked;
}

void UAMSMapSubsystem::TrackMarker(UAMSMapMarkerComponent* marker)
{

    UAMSDeveloperSettings* settings = GetMutableDefault<UAMSDeveloperSettings>();

    if (marker && settings) {
        TrackedMarker = marker;
        TrackedMarker->SetTracked(true);
        bHasMarkerTracked = true;
        OnTrackedMarkerChanged.Broadcast(marker);
    }
}

void UAMSMapSubsystem::UntrackMarker()
{
    if (TrackedMarker) {
        TrackedMarker->SetTracked(false);
        bHasMarkerTracked = false;
        OnTrackedMarkerChanged.Broadcast(TrackedMarker);
    }
}

UAMSMapMarkerComponent* UAMSMapSubsystem::GetCurrentlytTrackedMarker() const
{
    return bHasMarkerTracked ? TrackedMarker : nullptr;
}

void UAMSMapSubsystem::UpdateDiscovererPosition(FVector worldPosition)
{
}
