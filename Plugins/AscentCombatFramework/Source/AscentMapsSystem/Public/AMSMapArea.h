// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AMSTypes.h"
#include "Containers/BitArray.h"
#include "Containers/ContainerAllocationPolicies.h"
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"

#include "AMSMapArea.generated.h"

/**
 * Represents a defined area of the world to be displayed on the in-game map.
 * Each MapArea provides bounds, texture, and utility functions to convert between
 * world and normalized map space.
 */
UCLASS(BlueprintType, Blueprintable)
class ASCENTMAPSSYSTEM_API AAMSMapArea : public AActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AAMSMapArea();

    /** Returns the unique name assigned to this map area */
    UFUNCTION(BlueprintCallable, Category = AMS)
    FName GetAreaName() const
    {
        return AreaName;
    }

    /**
     * Returns the texture used to visually represent this area on the map,
     * depending on the current configuration or zoom level.
     */
    UFUNCTION(BlueprintPure, Category = AMS)
    UTexture* GetMapTexture() const;

    /** Returns the world location of the center of the map area's bounds */
    UFUNCTION(BlueprintPure, Category = AMS)
    FVector GetMapAreaCenter() const;

    /** Returns the 3D extent (half-size) of the map area in world units */
    UFUNCTION(BlueprintPure, Category = AMS)
    FVector GetMapAreaExtent() const;

    /** Returns the top-leftmost corner of the map area in 2D coordinates */
    UFUNCTION(BlueprintPure, Category = AMS)
    FVector2D GetMapAreaTopLeftmostPoint() const;

    /** Returns the bottom-rightmost corner of the map area in 2D coordinates */
    UFUNCTION(BlueprintPure, Category = AMS)
    FVector2D GetMapAreaBottomRightmostPoint() const;

    /**
     * Converts a world position to a normalized 2D position within the map area.
     *
     * @param worldPos The world location to convert
     * @return A value from 0 to 1 in both X and Y indicating the position within the map bounds
     */
    UFUNCTION(BlueprintCallable, Category = AMS)
    FVector2D GetNormalized2DPositionFromWorldLocation(const FVector& worldPos) const;

    /**
     * Checks whether a given world location lies within this map area's bounds.
     *
     * @param point The world position to test
     * @return True if the point is inside the area bounds, false otherwise
     */
    UFUNCTION(BlueprintCallable, Category = AMS)
    bool IsPointInThisArea(const FVector& point) const;

    UFUNCTION(BlueprintCallable, Category = AMS)
    FVector GetPointRelativeLocation(const FVector& point) const;

    /*Generates the textures in the render target for the current area*/
    UFUNCTION(BlueprintCallable, Category = AMS)
    void GenerateMapTexture();

    /*Generates the textures in the render target for the current area*/
    UFUNCTION(BlueprintCallable, Category = AMS)
    void GenerateMap(const TArray<AActor*>& ActorsToHide, float ExposuteCompensation = 1.f);

    /*Spawns a marker actor of the provided class inside the relative normalized location
    inside the map area with 0, 0 being the left topmost point and 1 , 1 the right bottom point
    of the area. Returns the spawned instance*/
    UFUNCTION(BlueprintCallable, Category = AMS)
    class AAMSActorMarker* SpawnActorMarkerAtMapLocation(const FVector2D& normalizedMapPosition, const TSubclassOf<class AAMSActorMarker>& markerClass);

    /**
     * Converts a normalized 2D position (0-1 range) into a world-space location.
     *
     * @param normalizedPosition A value between 0 and 1 in both X and Y, relative to the area bounds
     * @return Corresponding world position within this map area
     */
    UFUNCTION(BlueprintPure, Category = AMS)
    FVector GetWorldLocationFromNormalized2DPosition(const FVector2D& normalizedPosition) const;

    /**
     * Returns the Scene Capture Component associated with this area.
     * Used for rendering the area into a render target.
     *
     * @return Pointer to the SceneCaptureComponent2D used in this map area
     */
    UFUNCTION(BlueprintCallable, Category = AMS)
    class USceneCaptureComponent2D* GetCaptureComponent() const
    {
        return CaptureComp;
    }

    /**
     * Returns the render target used to store the scene capture output of this area.
     *
     * @return Texture render target used by the map area capture system
     */
    UFUNCTION(BlueprintPure, Category = AMS)
    class UTextureRenderTarget2D* GetRenderTarget() const { return RenderTarget; }

    void SetRenderTarget(TObjectPtr<class UTextureRenderTarget2D> val) { RenderTarget = val; }

    UFUNCTION(BlueprintPure, Category = AMS)
    FVector2D GetTextureSize() const;

#pragma region FogOfWar
    /**
     * Checks if Fog of War is currently enabled for this map area.
     *
     * @return True if Fog of War is active, false otherwise
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "AMS|FogOfWar")
    bool IsFogEnabled() const { return EnableFog; }

    /**
     * Returns the multiplier applied to the Fog of War brush when revealing cells.
     *
     * @return The current brush size multiplier used for fog reveal
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "AMS|FogOfWar")
    float GetFogOfWarBrushMultiplier() const { return FogOfWarBrushMultiplier; }

    /**
     * Updates the Fog of War at the specified world position,
     * typically used when a player or unit reveals part of the map.
     *
     * @param worldPosition The world location used to update the fog mask
     */
    UFUNCTION(BlueprintCallable, Category = "AMS|FogOfWar")
    void UpdateFogOfWar(FVector worldPosition);

    /**
     * Saves the current Fog of War data (bitmask or texture) to persistent storage.
     */
    UFUNCTION(BlueprintCallable, Category = "AMS|FogOfWar")
    void OnSave();

    /**
     * Loads previously saved Fog of War data and restores the visibility mask.
     */
    UFUNCTION(BlueprintCallable, Category = "AMS|FogOfWar")
    void OnLoad();

    /**
     * Returns the width of each fog cell in world units.
     *
     * @return Size in centimeters of a single fog cell
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "AMS|FogOfWar")
    int GetFogCellWidth() const;

    /**
     * Returns the total number of fog pixels vertically (Y axis).
     *
     * @return Number of rows (height) in the fog grid
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "AMS|FogOfWar")
    int GetFogHeightPixelsCount() const;

    /**
     * Returns the number of cells along X and Y used to define the Fog of War grid.
     *
     * @return Total cell count in 2D (columns, rows)
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "AMS|FogOfWar")
    FIntPoint GetFogCellsCount() const;

    /**
     * Returns a bit array representing the current Fog of War mask.
     * Each bit represents the visibility state of a single cell.
     *
     * @return Bitmask of visible/invisible fog cells
     */
    TBitArray<FDefaultBitArrayAllocator> GetFogOfWarBits() const { return FogOfWarBits; }
#pragma endregion FogOfWar

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = AMS)
    FName AreaName;

    UPROPERTY(EditAnywhere, Category = AMS)
    int AreaPriority = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = AMS)
    EAMSBackgroundType TextureType;

    UPROPERTY(EditAnywhere, Category = AMS)
    float AreaSize = 20000.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "TextureType == EAMSBackgroundType::ERenderTarget"), Category = AMS)
    TObjectPtr<class UTextureRenderTarget2D> RenderTarget;

    UPROPERTY(EditAnywhere, meta = (EditCondition = "TextureType == EAMSBackgroundType::ECustomTexture"), Category = AMS)
    TObjectPtr<class UTexture2D> Texture;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = AMS)
    TObjectPtr<class USceneCaptureComponent2D> CaptureComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = AMS)
    TObjectPtr<class UBoxComponent> MapBounds;

#pragma region FogOfWar
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|FogOfWar")
    bool EnableFog;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, meta = (EditCondition = "EnableFog == true"), Category = "AMS|FogOfWar")
    int FogWidthPixelsCount = 128;

    UPROPERTY(EditAnywhere, meta = (EditCondition = "EnableFog == true"), Category = "AMS|FogOfWar")
    float FogOfWarBrushMultiplier = 1.1f;

    UPROPERTY(SaveGame)
    TArray<uint8> SavedFogMapData;

    UFUNCTION(BlueprintCallable, Category = "AMS|FogOfWar")
    void ClearFogOfWarMatrix();

    TBitArray<FDefaultBitArrayAllocator> FogOfWarBits;
#pragma endregion FogOfWar

#if WITH_EDITOR
    virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;

#endif

private:
    void UpdateBoxProperties();

    UFUNCTION()
    void OnBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void OnEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
};
