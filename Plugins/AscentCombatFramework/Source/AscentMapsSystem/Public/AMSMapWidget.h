// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AMSMarkerWidget.h"
#include "AMSTypes.h"
#include "Blueprint/UserWidget.h"
#include "CommonUserWidget.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/InputComponent.h"
#include "Components/RetainerBox.h"
#include "Containers/BitArray.h"
#include "CoreMinimal.h"
#include "Framework/Application/AnalogCursor.h"
#include "GameplayTagContainer.h"
#include "InputCoreTypes.h"
#include <Components/SizeBox.h>

#include "AMSMapWidget.generated.h"

class UAMSMarkerWidget;
class UAMSMapSubsystem;
class UCommonInputSubsystem;
class UTexture2D;

/** Delegate broadcast when a marker is hovered. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMarkerHovered, const FAMSMarker&, marker);
/** Delegate broadcast when a marker is unhovered. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMarkerUnhovered, const FAMSMarker&, marker);
/** Delegate broadcast when marker actors are spawned or changed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMarkerActorSpawned);

/**
 * Main map widget: displays a pannable/zoomable map with markers from UAMSMapMarkerComponent.
 * Handles zoom, pan, cursor, marker hover/track, and optional fog of war. Bind MapBrush, MapMask, MapCanvas, MapCursor in Blueprint.
 */
UCLASS()
class ASCENTMAPSSYSTEM_API UAMSMapWidget : public UCommonUserWidget {
	GENERATED_BODY()

public:
	UAMSMapWidget(const FObjectInitializer& ObjectInitializer);

	/** Broadcast when a marker is hovered. */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMarkerHovered OnMarkerHovered;

	/** Broadcast when a marker is unhovered. */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMarkerUnhovered OnMarkerUnhovered;

	/** Broadcast when marker actors are spawned or changed. */
	UPROPERTY(BlueprintAssignable, Category = AMS)
	FOnMarkerActorSpawned OnMarkerActorsChanged;

	/** Key and input processing (call from owning widget or input). */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void ProcessKeyDown(const FKey& pressedKey);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void ProcessKeyUp(const FKey& releasedKey);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void ProcessAnalogChange(FGeometry MyGeometry, FAnalogInputEvent InAnalogInputEvent);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void ProcessMouseClick(FGeometry MyGeometry, const FPointerEvent& MouseEvent);

	/*MOVEMENT & ZOOM*/
	UFUNCTION(BlueprintCallable, Category = AMS)
	void ZoomIn(float zoomDelta);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void MoveUp(float UpAxis);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void MoveRight(float RightPanAxis);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void MoveMap(const FVector2D& Offset);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void MoveCursor(const FVector2D& Offset);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void MoveMapByPixelOffset(const FVector2D& finalDelta);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void CenterOnLocalPlayer();

	UFUNCTION(BlueprintCallable, Category = AMS)
	void CenterOnWorldLocation(const FVector& actorLoc);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void ResetDefaultZoom();

	UFUNCTION(BlueprintPure, Category = AMS)
	float GetCurrentZoomLevel() const { return CurrentZoomLevel; }

	UFUNCTION(BlueprintPure, Category = AMS)
	FVector2D GetMapSize() const;

	UFUNCTION(BlueprintPure, Category = AMS)
	FVector2D GetMapOffset() const;

	UFUNCTION(BlueprintPure, Category = AMS)
	FVector2D GetCursorPosition() const;

	void SpawnMarkerActorAtMousePosition(const FPointerEvent& MouseEvent);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void SpawnMarkerActorAtScreenPosition(const FVector2D screenPos);

	UFUNCTION(BlueprintCallable, Category = AMS)
	FVector GetWorldLocationFromMousePosition(const FPointerEvent& MouseEvent);
	UFUNCTION(BlueprintCallable, Category = AMS)
	FVector GetWorldLocationFromNormalizedMapPosition(const FVector2D& widgetPosition);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void SetMapArea(AAMSMapArea* mapAreaBound);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void SetMapAreaByTag(const FName& mapArea);



	UFUNCTION(BlueprintPure, BlueprintCallable, Category = AMS)
	class AAMSMapArea* GetMapArea() const {
		return currentMapArea;
	}




	/*MARKERS*/
	UFUNCTION(BlueprintPure, Category = AMS)
	TArray<FAMSMarker> GetMarkerWidgets() const { return markerWidgets; }

	UFUNCTION(BlueprintPure, Category = AMS)
	FAMSMarker GetHoveredWidget() const { return HoveredWidget; }

	UFUNCTION(BlueprintPure, Category = AMS)
	FAMSMarker GetCurrentlytTrackedMarker() const;

	UFUNCTION(BlueprintPure, Category = AMS)
	bool HasAnyHoveredMarker() const
	{
		return IsValid(HoveredWidget.markerComp);
	}

	UFUNCTION(BlueprintPure, Category = AMS)
	bool HasAnyTrackedMarker() const;

	UFUNCTION(BlueprintCallable, Category = AMS)
	void TrackHoveredMarker();

	UFUNCTION(BlueprintCallable, Category = AMS)
	void TrackMarker(const FAMSMarker& marker);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void UntrackCurrentMarker();

	UFUNCTION(BlueprintCallable, Category = AMS)
	void UpdateMarkers();

	UFUNCTION(BlueprintCallable, Category = AMS)
	void AddMarker(class UAMSMapMarkerComponent* marker);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveMarker(class UAMSMapMarkerComponent* marker);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void HighlightMarker(class UAMSMapMarkerComponent* marker, bool resetOtherMarkers = true);

	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveAllMarkerHighlights();

	UFUNCTION(BlueprintCallable, Category = AMS)
	void RemoveMarkerHighlight(class UAMSMapMarkerComponent* marker);

protected:
	UPROPERTY(BlueprintReadWrite, meta = (BindWidget), Category = AMS)
	UBorder* MapBrush;

	UPROPERTY(BlueprintReadWrite, meta = (BindWidget), Category = AMS)
	URetainerBox* MapMask;

	UPROPERTY(BlueprintReadWrite, meta = (BindWidget), Category = AMS)
	UCanvasPanel* MapCanvas;

	UPROPERTY(BlueprintReadWrite, meta = (BindWidget), Category = AMS)
	USizeBox* MapCursor;

	UPROPERTY(EditAnywhere, Category = "AMS|Materials")
	class UMaterialInterface* MapMaterial;

	UPROPERTY(EditAnywhere, Category = "AMS|Materials")
	FName TextureParameterName = "Texture";

	UPROPERTY(EditAnywhere, Category = "AMS|Materials")
	class UTexture* Mask;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Markers")
	TSubclassOf<UAMSMarkerWidget> MarkersClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Markers")
	FVector2D MarkersSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Markers")
	FVector2D MarkerScaleWhenHighlighted;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Actor Marker")
	FKey SpawnActorMarkerKey;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Actor Marker")
	FKey SpawnActorMarkerKeyGamepad;

	/** The Class of the marker that will be spawned at click*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Actor Marker")
	TSubclassOf<class AAMSActorMarker> ActorMarkerClass;

	/** Minimum Zoom level the Map should be set, beyond which Zooming Out won't be possible.*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	float MinimumZoomLevel = 0.1f;

	/** Maximum Zoom level the Map should be set, beyond which Zooming In won't be possible.*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	float MaximumZoomLevel = 5.f;

	/** Default Zoom Level the Map should open at.*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	float DefaultZoomLevel = 2.f;

	/** Speed at which the MapMaterial can be Zoomed.*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	float ZoomSpeed = .2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	FKey ZoomInKey;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Zoom")
	FKey ZoomOutKey;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FVector2D CanvasSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FVector2D MoveMapStart = FVector2D(190.f, 108.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FVector2D CursorLimit = FVector2D(720.f, 480.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	UTexture2D* CursorImage;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FKey MoveRightAxis;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FKey MoveUpAxis;

	/*The speed to move the map in the canvas with the analog cursor*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	float MoveSpeed = 500.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	float MoveCursorSpeed = 200.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AMS|Movement")
	FKey RemoveFromParentKey;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AMS|FogOfWar")
	TObjectPtr<class UTextureRenderTarget2D> FogTexture;

	UPROPERTY(EditAnywhere, Category = "AMS|FogOfWar")
	TObjectPtr<class UMaterialInterface> BrushMaterial;

	UFUNCTION(Category = AMS)
	UTexture* CreateFogTexture();

	UPROPERTY(EditAnywhere, Category = "AMS|FogOfWar")
	FName FogTextureParameterName = "FogTexture";

	UPROPERTY(EditAnywhere, Category = "AMS|FogOfWar")
	FName UseMapFogParameter = "UseMapFog";

	virtual void NativePreConstruct() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime);

	UFUNCTION(BlueprintNativeEvent, Category = AMS)
	void HandleTrackedMarkerChanged(UAMSMapMarkerComponent* marker);

	UFUNCTION(BlueprintImplementableEvent, Category = AMS)
	void HandleMarkerHovered(const FAMSMarker& marker);

	UFUNCTION(BlueprintImplementableEvent, Category = AMS)
	void HandleMarkerUnhovered(const FAMSMarker& marker);

	UFUNCTION(BlueprintImplementableEvent, Category = AMS)
	void HandleMarkerActorsChanged();

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	AAMSMapArea* currentMapArea;

	/** Removes markers with invalid/stale component references after save/load */
	void CleanupInvalidMarkers();

	/** Clears all marker widgets and rebuilds from subsystem data */
	void RefreshAllMarkers();

	/** Re-applies mask texture params and area material. Call from Blueprint Event On Activated. */
	UFUNCTION(BlueprintCallable, Category = AMS)
	void RefreshMaterials();

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> CachedMapMaterial;

private:
	void ApplyMaskMaterial();

	bool bCanvasInitialized = false;
	FName AreaTag;
	void SetCurrentZoomLevel(float val);

	void Internal_UpdateMarkers();

	void Internal_SetCanvasPosition(const FVector2D& updatedPos);

	UFUNCTION()
	void HandleMarkerAdded(class UAMSMapMarkerComponent* marker);

	UFUNCTION()
	void HandleMarkerRemoved(class UAMSMapMarkerComponent* marker);

	UFUNCTION()
	void Internal_HandleMarkerHovered(const UAMSMarkerWidget* marker);

	UFUNCTION()
	void Internal_HandleMarkerUnhovered(const UAMSMarkerWidget* marker);

	TArray<FAMSMarker> markerWidgets;

	FAMSMarker HoveredWidget;



	void UpdateMarker(FAMSMarker& marker);
	void InitCanvas();

	float CurrentZoomLevel = 1.f;

	bool bPendingMarkersUpdate = false;

	EZoomState currentZoomState;

	// INITIAL VALUES//
	FVector2D InitialAlignment;

	FVector2D InitialCanvasSize;

	FVector2D InitialCanvasPosition;
	// END//

	UAMSMapSubsystem* GetMapSubsystem() const;
	UCommonInputSubsystem* GetInputSubsystem() const;

	UFUNCTION()
	void HandleInputChanged(ECommonInputType bNewInputType);

	bool bPendingTrackUpdate = false;
};
