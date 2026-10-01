// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapWidget.h"
#include "AMSActorMarker.h"
#include "AMSMapArea.h"
#include "AMSMapMarkerComponent.h"
#include "AMSMapSubsystem.h"
#include "AMSMarkerWidget.h"
#include "AMSTypes.h"
#include "Blueprint/SlateBlueprintLibrary.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/InputComponent.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Kismet/KismetMathLibrary.h"
#include "Layout/Geometry.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Widgets/SWidget.h"
#include <CommonInputSubsystem.h>
#include <Components/Widget.h>
#include <Engine/Canvas.h>
#include <Engine/GameInstance.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>
#include <Kismet/KismetRenderingLibrary.h>
#include <Logging/StructuredLog.h>

UAMSMapWidget::UAMSMapWidget(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    MarkersClass = UAMSMarkerWidget::StaticClass();
    MarkersSize = FVector2D(32.f, 32.f);
    ActorMarkerClass = AAMSActorMarker::StaticClass();
    CanvasSize = FVector2D(1024.f);
    MarkerScaleWhenHighlighted = FVector2D(1.3f, 1.3f);
}

void UAMSMapWidget::ZoomIn(float zoomDelta)
{
    if (MapBrush && MapBrush->IsValidLowLevel()) {
        const float ZoomFactor = zoomDelta * ZoomSpeed;
        SetCurrentZoomLevel(CurrentZoomLevel + ZoomFactor);
        UpdateMarkers();
    }
}

void UAMSMapWidget::ProcessKeyDown(const FKey& pressedKey)
{
    if (pressedKey == ZoomInKey) {
        currentZoomState = EZoomState::EZoomIn;
    } else if (pressedKey == ZoomOutKey) {
        currentZoomState = EZoomState::EZoomOut;
    } else if (RemoveFromParentKey == pressedKey) {
        RemoveFromParent();
    } else if (pressedKey == SpawnActorMarkerKeyGamepad) {
        if (HasAnyHoveredMarker()) {
            TrackHoveredMarker();

        } else {
            GetMapSubsystem()->RemoveAllMarkerActors();
            SpawnMarkerActorAtScreenPosition(GetCursorPosition());
        }
    }
}

void UAMSMapWidget::ProcessKeyUp(const FKey& releasedKey)
{
    if (releasedKey == ZoomInKey || releasedKey == ZoomOutKey) {
        currentZoomState = EZoomState::ENone;
    }
}

void UAMSMapWidget::ProcessAnalogChange(FGeometry MyGeometry, FAnalogInputEvent InAnalogInputEvent)
{
    bool bValidInput = false;
    FVector2D offset;

    if (InAnalogInputEvent.GetKey() == MoveUpAxis) {
        offset.Y = InAnalogInputEvent.GetAnalogValue();
        bValidInput = true;
    }
    if (InAnalogInputEvent.GetKey() == MoveRightAxis) {
        offset.X = InAnalogInputEvent.GetAnalogValue();
        bValidInput = true;
    }

    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (!CanvasSlot) {
        return;
    }
    const FVector2D OldPos = CanvasSlot->GetPosition();
    if (bValidInput) {
        bValidInput = false;
        offset = offset * UGameplayStatics::GetWorldDeltaSeconds(this);

        const FVector2D newPos = CanvasSlot->GetPosition();

        if (MapCursor) {

            UCanvasPanelSlot* cursorSlot = Cast<UCanvasPanelSlot>(MapCursor->Slot);

            const FVector2D cursorOffset = cursorSlot->GetPosition();
            FVector2D mapOffset = FVector2D(0.f, 0.f);

            if ((cursorOffset.X > MoveMapStart.X && offset.X > 0.f) || (cursorOffset.X < -MoveMapStart.X && offset.X < 0.f)) {
                mapOffset.X = offset.X;
            }
            if ((cursorOffset.Y > MoveMapStart.Y && offset.Y < 0.f) || (cursorOffset.Y < -MoveMapStart.Y && offset.Y > 0.f)) {
                mapOffset.Y = offset.Y;
            }

            if (mapOffset != FVector2D(0.f, 0.f)) {
                MoveMap(offset);
            } else {
                offset *= 2.f;
            }
            MoveCursor(-offset);
            FVector2D pixelPos, viewportPos;
            USlateBlueprintLibrary::AbsoluteToViewport(this, MapCursor->GetCachedGeometry().GetAbsolutePosition(),
                pixelPos, viewportPos);
            UGameplayStatics::GetPlayerController(this, 0.f)->SetMouseLocation(pixelPos.X, pixelPos.Y);
        }
    }
}

FVector2D UAMSMapWidget::GetCursorPosition() const
{
    if (MapCursor) {
        return MapCursor->GetCachedGeometry().GetAbsolutePosition();
    }
    return FVector2D();
}

void UAMSMapWidget::ProcessMouseClick(FGeometry MyGeometry, const FPointerEvent& MouseEvent)
{
    if (!MouseEvent.IsMouseButtonDown(SpawnActorMarkerKey)) {
        return;
    }

    SpawnMarkerActorAtMousePosition(MouseEvent);
}

void UAMSMapWidget::SpawnMarkerActorAtMousePosition(const FPointerEvent& MouseEvent)
{
    const FVector2D screenPos = MouseEvent.GetScreenSpacePosition();
    SpawnMarkerActorAtScreenPosition(screenPos);
}

void UAMSMapWidget::SpawnMarkerActorAtScreenPosition(const FVector2D screenPos)
{
    if (MapBrush) {

        const FVector2D widgetPos = USlateBlueprintLibrary::AbsoluteToLocal(MapBrush->GetCachedGeometry(), screenPos);
        const FVector2D normalizedPos = widgetPos / GetMapSize();

        AAMSMapArea* mapArea = GetMapArea();
        if (mapArea) {
            mapArea->SpawnActorMarkerAtMapLocation(normalizedPos, ActorMarkerClass);

            HandleMarkerActorsChanged();
            OnMarkerActorsChanged.Broadcast();
        }
    }
}

FVector UAMSMapWidget::GetWorldLocationFromMousePosition(const FPointerEvent& MouseEvent)
{
    const FVector2D screenPos = MouseEvent.GetScreenSpacePosition();
    const FVector2D widgetPos = USlateBlueprintLibrary::AbsoluteToLocal(MapBrush->GetCachedGeometry(), screenPos);
    const FVector2D normalizedPos = widgetPos / GetMapSize();
    return GetWorldLocationFromNormalizedMapPosition(normalizedPos);
}

FVector UAMSMapWidget::GetWorldLocationFromNormalizedMapPosition(const FVector2D& widgetPosition)
{
    const AAMSMapArea* mapArea = GetMapArea();
    if (mapArea) {
        return mapArea->GetWorldLocationFromNormalized2DPosition(widgetPosition);
    }
    return FVector();
}

void UAMSMapWidget::MoveRight(float RightPanAxis)
{
    MoveMap(FVector2D(0.f, RightPanAxis));
}

void UAMSMapWidget::MoveUp(float UpAxis)
{
    MoveMap(FVector2D(0.f, UpAxis));
}

void UAMSMapWidget::MoveMap(const FVector2D& Offset)
{
    const FVector2D finalDelta = Offset * MoveSpeed;
    MoveMapByPixelOffset(finalDelta);
}

void UAMSMapWidget::MoveMapByPixelOffset(const FVector2D& finalDelta)
{
    if (MapBrush && MapBrush->IsValidLowLevel()) {
        UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
        if (CanvasSlot) {
            const FVector2D CanvasPos = CanvasSlot->GetPosition();
            FVector2D finalPos;
            finalPos.X = CanvasPos.X - finalDelta.X;
            finalPos.Y = CanvasPos.Y + finalDelta.Y;
            Internal_SetCanvasPosition(finalPos);
        }
    }
}

void UAMSMapWidget::MoveCursor(const FVector2D& Offset)
{
    const FVector2D finalDelta = Offset * MoveCursorSpeed;
    if (MapCursor) {
        UCanvasPanelSlot* cursorSlot = Cast<UCanvasPanelSlot>(MapCursor->Slot);
        if (cursorSlot) {
            const FVector2D CanvasPos = cursorSlot->GetPosition();
            FVector2D updatedPos;
            updatedPos.X = CanvasPos.X - finalDelta.X;
            updatedPos.Y = CanvasPos.Y + finalDelta.Y;

            FVector2D finalPos = updatedPos;
            finalPos.Y = FMath::Clamp(updatedPos.Y, -CursorLimit.Y, CursorLimit.Y);
            finalPos.X = FMath::Clamp(updatedPos.X, -CursorLimit.X, CursorLimit.X);
            cursorSlot->SetPosition(finalPos);
        }
    }
}

void UAMSMapWidget::Internal_SetCanvasPosition(const FVector2D& updatedPos)
{
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);

    const FVector2D CanvasPos = CanvasSlot->GetPosition();

    const FVector2D MaxPos = (CanvasSlot->GetSize() / 2 - CanvasSize / 2);
    const FVector2D MinPos = -(CanvasSlot->GetSize() / 2 - CanvasSize / 2);

    FVector2D finalPos = updatedPos;
    finalPos.Y = FMath::Clamp(updatedPos.Y, MinPos.Y, MaxPos.Y);
    finalPos.X = FMath::Clamp(updatedPos.X, MinPos.X, MaxPos.X);
    CanvasSlot->SetPosition(finalPos);
}

void UAMSMapWidget::CenterOnLocalPlayer()
{
    const APawn* localPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    if (localPawn) {
        const FVector actorLoc = localPawn->GetActorLocation();
        CenterOnWorldLocation(actorLoc);
    }
}

void UAMSMapWidget::CenterOnWorldLocation(const FVector& actorLoc)
{
    const AAMSMapArea* areaMap = GetMapArea();
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (areaMap && CanvasSlot) {
        const FVector2D normalizedPlayer = areaMap->GetNormalized2DPositionFromWorldLocation(actorLoc);
        const FVector2D playerpos = .5 * GetMapSize() - (normalizedPlayer * GetMapSize());
        Internal_SetCanvasPosition(playerpos);
    }
}

UTexture* UAMSMapWidget::CreateFogTexture()
{
    AAMSMapArea* mapArea = GetMapArea();
    if (!mapArea || !mapArea->IsFogEnabled()) {
        return nullptr;
    }

    if (!BrushMaterial) {
        UE_LOG(LogTemp, Error, TEXT("Fog of War is not enabled or BrushMaterial is missing! - UAMSMapWidget::CreateFogTexture"));
        return nullptr;
    }

    const FVector2D leftmost = mapArea->GetMapAreaTopLeftmostPoint();
    const FVector2D rightmost = mapArea->GetMapAreaBottomRightmostPoint();
    const FVector2D mapExtent = rightmost - leftmost;

    UWorld* world = GetWorld();
    const FVector2D textureSize = GetMapSize();
    UTextureRenderTarget2D* NewTexture = UKismetRenderingLibrary::CreateRenderTarget2D(world, textureSize.X, textureSize.Y, ETextureRenderTargetFormat::RTF_RGBA8, FLinearColor::White, false, false);

    const FIntPoint cellsCount = mapArea->GetFogCellsCount();
    const int cellSize = textureSize.X / cellsCount.X;
    const float halfCellSize = (float)cellSize / 2;

    const TBitArray<FDefaultBitArrayAllocator> FogBitArray = mapArea->GetFogOfWarBits();
    const float cellDimensionMultiplier = mapArea->GetFogOfWarBrushMultiplier();

    UCanvas* canvas;
    FVector2D size;
    FDrawToRenderTargetContext context;
    UKismetRenderingLibrary::BeginDrawCanvasToRenderTarget(world, NewTexture, canvas, size, context);

    const FVector2D drawSize = FVector2D(cellSize * cellDimensionMultiplier);
    const FVector2D halfDrawSize = drawSize / 2;
    const FVector2D uv0(0, 0);

    if (canvas) {
        for (int32 y = 0; y < cellsCount.Y; ++y) {
            for (int32 x = 0; x < cellsCount.X; ++x) {
                const int32 Index = y * cellsCount.X + x;

                if (!FogBitArray[Index]) {
                    const float px = x * cellSize;
                    const float py = y * cellSize;

                    // Current cell
                    canvas->K2_DrawMaterial(BrushMaterial, FVector2D(px, py) - halfDrawSize, drawSize, uv0);

                    //// Right cell
                    // if (x < cellsCount.X - 1 && !FogBitArray[Index + 1])
                    //     canvas->K2_DrawMaterial(BrushMaterial, FVector2D(px + halfCellSize, py), drawSize, uv0);

                    //// Down cell
                    // if (y < cellsCount.Y - 1 && !FogBitArray[Index + cellsCount.X])
                    //     canvas->K2_DrawMaterial(BrushMaterial, FVector2D(px, py + halfCellSize), drawSize, uv0);

                    //// Down right cell
                    // if (x < cellsCount.X - 1 && y < cellsCount.Y - 1 && !FogBitArray[Index + cellsCount.X + 1])
                    //     canvas->K2_DrawMaterial(BrushMaterial, FVector2D(px + halfCellSize, py + halfCellSize), drawSize, uv0);

                    //// Down left cell
                    // if (x > 0 && y < cellsCount.Y - 1 && !FogBitArray[Index + cellsCount.X - 1])
                    //     canvas->K2_DrawMaterial(BrushMaterial, FVector2D(px - halfCellSize, py + halfCellSize), drawSize, uv0);
                }
            }
        }
    }

    UKismetRenderingLibrary::EndDrawCanvasToRenderTarget(world, context);

    return NewTexture;
}

void UAMSMapWidget::ApplyMaskMaterial()
{
    if (MapMask) {
        UMaterialInstanceDynamic* mat = MapMask->GetEffectMaterial();
        if (mat && Mask) {
            mat->SetTextureParameterValue("Texture", Mask);
            mat->SetTextureParameterValue("Texture2", Mask);
        }
    }
}

void UAMSMapWidget::NativePreConstruct()
{
    Super::NativePreConstruct();
    InitCanvas();
    ApplyMaskMaterial();
}

void UAMSMapWidget::NativeConstruct()
{
    Super::NativeConstruct();

    ApplyMaskMaterial();

    UAMSMapSubsystem* mapSubsystem = GetMapSubsystem();
    if (mapSubsystem) {
        mapSubsystem->OnMapMarkerAdded.AddDynamic(this, &UAMSMapWidget::HandleMarkerAdded);
        mapSubsystem->OnMapMarkerRemoved.AddDynamic(this, &UAMSMapWidget::HandleMarkerRemoved);
        mapSubsystem->OnTrackedMarkerChanged.AddDynamic(this, &UAMSMapWidget::HandleTrackedMarkerChanged);
    }

    UCommonInputSubsystem* commonInputSub = GetInputSubsystem();
    if (commonInputSub) {
        commonInputSub->OnInputMethodChangedNative.AddUObject(this, &UAMSMapWidget::HandleInputChanged);
        HandleInputChanged(commonInputSub->GetCurrentInputType());
    }

    SetCurrentZoomLevel(DefaultZoomLevel);
    
    // Clear any stale markers from previous session and rebuild fresh
    RefreshAllMarkers();

    bPendingTrackUpdate = true;
}

void UAMSMapWidget::HandleInputChanged(ECommonInputType bNewInputType)
{
    switch (bNewInputType) {
    case ECommonInputType::Gamepad:
        MapCursor->SetVisibility(ESlateVisibility::Visible);
        // UGameplayStatics::GetPlayerController(this, 0)->bShowMouseCursor = false;
        MapBrush->SetCursor(EMouseCursor::None);
        break;
    case ECommonInputType::MouseAndKeyboard:
        MapCursor->SetVisibility(ESlateVisibility::Collapsed);
        //   UGameplayStatics::GetPlayerController(this, 0)->bShowMouseCursor = true;
        MapBrush->SetCursor(EMouseCursor::Default);
        break;
    default:
        break;
    }
}

void UAMSMapWidget::NativeDestruct()
{
    Super::NativeDestruct();
    UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(this);
    UAMSMapSubsystem* mapSubsystem = GameInstance->GetSubsystem<UAMSMapSubsystem>();
    if (mapSubsystem) {
        mapSubsystem->OnMapMarkerAdded.RemoveDynamic(this, &UAMSMapWidget::HandleMarkerAdded);
        mapSubsystem->OnMapMarkerRemoved.RemoveDynamic(this, &UAMSMapWidget::HandleMarkerRemoved);
        mapSubsystem->OnTrackedMarkerChanged.RemoveDynamic(this, &UAMSMapWidget::HandleTrackedMarkerChanged);
    }
    UCommonInputSubsystem* commonInputSub = GetInputSubsystem();
    if (commonInputSub) {
        commonInputSub->OnInputMethodChangedNative.RemoveAll(this);
    }
    /* UGameplayStatics::GetPlayerController(this, 0)->bShowMouseCursor = false;*/
    SetCurrentZoomLevel(DefaultZoomLevel);
}

void UAMSMapWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);

    switch (currentZoomState) {
    case EZoomState::ENone:
        break;
    case EZoomState::EZoomIn:
        ZoomIn(InDeltaTime * 10.f);
        break;
    case EZoomState::EZoomOut:
        ZoomIn(InDeltaTime * -10.f);
        break;
    }

    if (bPendingMarkersUpdate) {
        Internal_UpdateMarkers();
    }

    if (bPendingTrackUpdate) {
        FAMSMarker markerRef = GetCurrentlytTrackedMarker();
        if (markerRef.ValidCheck()) {
            TrackMarker(markerRef);
        }
        bPendingTrackUpdate = false;
    }
}

FAMSMarker UAMSMapWidget::GetCurrentlytTrackedMarker() const
{
    const UAMSMapMarkerComponent* markerComp = GetMapSubsystem()->GetCurrentlytTrackedMarker();
    const FAMSMarker* markerRef = markerWidgets.FindByKey(markerComp);
    if (markerRef && markerRef->ValidCheck()) {
        return *markerRef;
    }
    return FAMSMarker();
}

void UAMSMapWidget::HandleTrackedMarkerChanged_Implementation(UAMSMapMarkerComponent* marker)
{
}

void UAMSMapWidget::ResetDefaultZoom()
{
    if (MapBrush && MapBrush->IsValidLowLevel()) {

        UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
        if (CanvasSlot) {
            CanvasSlot->SetAlignment(InitialAlignment);
            CanvasSlot->SetSize(InitialCanvasSize);
            SetCurrentZoomLevel(DefaultZoomLevel);
            Internal_SetCanvasPosition(InitialCanvasPosition);
        }
    }
}

void UAMSMapWidget::SetCurrentZoomLevel(float val)
{
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (CanvasSlot) {
        const float oldZoomLevel = CurrentZoomLevel;
        CurrentZoomLevel = FMath::Clamp(val, MinimumZoomLevel, MaximumZoomLevel);
        const FVector2D newSize = InitialCanvasSize * FVector2D(CurrentZoomLevel, CurrentZoomLevel);

        const FVector2D OldSize = CanvasSlot->GetSize();
        if (newSize != OldSize) {
            const FVector2D Pivot = CanvasSlot->GetAlignment();
            const FVector2D OldCanvasPos = CanvasSlot->GetPosition();
            CanvasSlot->SetSize(newSize);
            const FVector2D CanvasCenter = OldSize * Pivot;
            const FVector2D OffsetFromCenter = OldCanvasPos - CanvasCenter;
            const FVector2D ZoomRatio = FVector2D(CurrentZoomLevel / oldZoomLevel, CurrentZoomLevel / oldZoomLevel);
            const FVector2D NewCanvasCenter = newSize * Pivot;
            const FVector2D NewCanvasPos = NewCanvasCenter + OffsetFromCenter * ZoomRatio;
            Internal_SetCanvasPosition(NewCanvasPos);
            UpdateMarkers();
        }
    }
}

void UAMSMapWidget::Internal_UpdateMarkers()
{
    bPendingMarkersUpdate = false;

    UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(this);
    UAMSMapSubsystem* mapSubsystem = GameInstance->GetSubsystem<UAMSMapSubsystem>();

    if (mapSubsystem) {
        const TArray<class UAMSMapMarkerComponent*> markers = mapSubsystem->GetAllMarkers();
        
        // First pass: remove any invalid/stale markers from our widget list
        CleanupInvalidMarkers();
        
        for (const auto& marker : markers) {
            // Skip invalid markers from subsystem
            if (!IsValid(marker)) {
                continue;
            }
            
            if (markerWidgets.Contains(marker)) {
                FAMSMarker* markerStruct = markerWidgets.FindByKey(marker);
                if (markerStruct && markerStruct->ValidCheck()) {
                    UpdateMarker(*markerStruct);
                }
            } else {
                AddMarker(marker);
            }
        }
    }
}

void UAMSMapWidget::CleanupInvalidMarkers()
{
    // Remove markers with invalid/stale component references
    for (int32 i = markerWidgets.Num() - 1; i >= 0; --i) {
        FAMSMarker& marker = markerWidgets[i];
        
        // Check if the marker component is still valid (catches stale pointers after save/load)
        if (!marker.ValidCheck()) {
            // Clean up the widget if it exists
            if (IsValid(marker.markerWidget)) {
                marker.markerWidget->OnHovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerHovered);
                marker.markerWidget->OnUnhovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerUnhovered);
                marker.markerWidget->RemoveFromParent();
            }
            
            markerWidgets.RemoveAt(i);
            UE_LOG(LogTemp, Warning, TEXT("Removed stale marker reference during cleanup - UAMSMapWidget::CleanupInvalidMarkers"));
        }
    }
}

void UAMSMapWidget::RefreshAllMarkers()
{
    // Clear all existing marker widgets
    for (FAMSMarker& marker : markerWidgets) {
        if (IsValid(marker.markerWidget)) {
            marker.markerWidget->OnHovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerHovered);
            marker.markerWidget->OnUnhovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerUnhovered);
            marker.markerWidget->RemoveFromParent();
        }
    }
    markerWidgets.Empty();
    
    // Reset hovered widget
    HoveredWidget.Reset();
    
    // Trigger fresh marker update
    UpdateMarkers();
}

void UAMSMapWidget::HandleMarkerAdded(UAMSMapMarkerComponent* marker)
{
    UpdateMarkers();
}

void UAMSMapWidget::HandleMarkerRemoved(UAMSMapMarkerComponent* marker)
{
    RemoveMarker(marker);
    UpdateMarkers();
}

void UAMSMapWidget::Internal_HandleMarkerHovered(const UAMSMarkerWidget* marker)
{
    if (markerWidgets.Contains(marker)) {
        FAMSMarker* foundMarker = markerWidgets.FindByKey(marker);
        if (foundMarker && foundMarker->ValidCheck()) {
            HoveredWidget.markerComp = foundMarker->markerComp;
            HoveredWidget.markerWidget = foundMarker->markerWidget;
            HandleMarkerHovered(HoveredWidget);
            OnMarkerHovered.Broadcast(HoveredWidget);
        }
    }
}

void UAMSMapWidget::Internal_HandleMarkerUnhovered(const UAMSMarkerWidget* marker)
{
    if (markerWidgets.Contains(marker)) {
        HandleMarkerUnhovered(HoveredWidget);

        OnMarkerUnhovered.Broadcast(HoveredWidget);
        HoveredWidget.Reset();
    }
}

bool UAMSMapWidget::HasAnyTrackedMarker() const
{
    return GetMapSubsystem()->HasAnyTrackedMarker();
}

void UAMSMapWidget::TrackHoveredMarker()
{
    if (HoveredWidget.ValidCheck()) {
        AAMSActorMarker* markerActor = Cast<AAMSActorMarker>(HoveredWidget.markerComp->GetOwner());
        if (markerActor) {
            GetMapSubsystem()->RemoveAllMarkerActors();
            OnMarkerActorsChanged.Broadcast();
            HandleMarkerActorsChanged();
        } else {
            if (HoveredWidget.markerComp == GetMapSubsystem()->GetCurrentlytTrackedMarker()) {
                UntrackCurrentMarker();
            } else {
                UntrackCurrentMarker();
                TrackMarker(HoveredWidget);
            }
        }
    }
}

void UAMSMapWidget::TrackMarker(const FAMSMarker& marker)
{
    if (marker.ValidCheck()) {
        GetMapSubsystem()->TrackMarker(marker.markerComp);
        marker.markerWidget->TrackMarker(true);
    }
}

void UAMSMapWidget::UntrackCurrentMarker()
{
    UAMSMapMarkerComponent* markerComp = GetMapSubsystem()->GetCurrentlytTrackedMarker();
    FAMSMarker* markerRef = markerWidgets.FindByKey(markerComp);
    if (markerRef && markerRef->ValidCheck()) {
        markerRef->markerWidget->TrackMarker(false);
        GetMapSubsystem()->UntrackMarker();
    }
}

void UAMSMapWidget::AddMarker(UAMSMapMarkerComponent* marker)
{
    // Early validation - skip invalid markers
    if (!IsValid(marker)) {
        return;
    }
    
    const FVector worldLoc = marker->GetOwnerLocation();
    const AAMSMapArea* mapAreaBound = GetMapArea();
    if (mapAreaBound && mapAreaBound->IsPointInThisArea(worldLoc)) {
        UAMSMarkerWidget* widgetMarker = CreateWidget<UAMSMarkerWidget>(this, MarkersClass);
        FAMSMarker markerStruct = FAMSMarker(marker, widgetMarker);
        markerWidgets.Add(markerStruct);
        widgetMarker->SetupMarkerIcon(marker);
        widgetMarker->SetMarkerIcon(marker->GetMarkerTexture());
        widgetMarker->OnHovered.AddDynamic(this, &UAMSMapWidget::Internal_HandleMarkerHovered);
        widgetMarker->OnUnhovered.AddDynamic(this, &UAMSMapWidget::Internal_HandleMarkerUnhovered);
        /*   widgetMarker->SetMarkerSize(MarkersSize);*/
        MapCanvas->AddChildToCanvas(widgetMarker);
        UpdateMarker(markerStruct);
    }
}

void UAMSMapWidget::RemoveMarker(class UAMSMapMarkerComponent* marker)
{
    if (markerWidgets.Contains(marker)) {
        const int32 index = markerWidgets.IndexOfByKey(marker);
        if (markerWidgets.IsValidIndex(index)) {
            FAMSMarker markerStruct = markerWidgets[index];
            markerWidgets.Remove(markerStruct);
            if (IsValid(markerStruct.markerWidget)) {
                markerStruct.markerWidget->RemoveFromParent();
                markerStruct.markerWidget->OnHovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerHovered);
                markerStruct.markerWidget->OnUnhovered.RemoveDynamic(this, &UAMSMapWidget::Internal_HandleMarkerUnhovered);
            }
        }
    }
}

void UAMSMapWidget::HighlightMarker(class UAMSMapMarkerComponent* marker, bool resetOtherMarkers /*= true*/)
{
    if (resetOtherMarkers) {
        RemoveAllMarkerHighlights();
    }
    FAMSMarker* markerWidget = markerWidgets.FindByKey(marker);
    if (markerWidget && markerWidget->ValidCheck()) {
        markerWidget->bHighlighted = true;
    }
    UpdateMarkers();
}

void UAMSMapWidget::RemoveAllMarkerHighlights()
{
    for (FAMSMarker& marker : markerWidgets) {
        if (marker.ValidCheck()) {
            RemoveMarkerHighlight(marker.markerComp);
        }
    }
    UpdateMarkers();
}

void UAMSMapWidget::RemoveMarkerHighlight(class UAMSMapMarkerComponent* marker)
{
    FAMSMarker* markerWidget = markerWidgets.FindByKey(marker);
    if (markerWidget && markerWidget->ValidCheck()) {
        markerWidget->bHighlighted = false;
    }
    UpdateMarkers();
}

void UAMSMapWidget::UpdateMarkers()
{
    bPendingMarkersUpdate = true;
}

void UAMSMapWidget::UpdateMarker(FAMSMarker& marker)
{
    AAMSMapArea* mapArea = GetMapArea();

    // Use ValidCheck() which properly validates both component and widget
    if (mapArea && marker.ValidCheck()) {
        const FVector2D mapPos = mapArea->GetNormalized2DPositionFromWorldLocation(marker.markerComp->GetOwnerLocation());
        const FVector2D mapSize = GetMapSize();
        const FVector2D scaledPos = (mapSize * mapPos) - (MarkersSize);
        marker.markerWidget->SetRenderTranslation(scaledPos);
        if (marker.bHighlighted) {
            marker.markerWidget->SetRenderScale(MarkerScaleWhenHighlighted);
        } else {
            marker.markerWidget->SetRenderScale(FVector2D(1.f, 1.f));
        }
        if (marker.markerComp->GetShouldRotate()) {
            const float rot = marker.markerComp->GetOwnerRotation().Yaw;
            marker.markerWidget->Rotate(rot);
        }
    }
}

void UAMSMapWidget::InitCanvas()
{
    if (bCanvasInitialized)
    {
        return;
    }
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (CanvasSlot) {
        InitialCanvasPosition = CanvasSlot->GetPosition();
        InitialCanvasSize = CanvasSlot->GetSize();
        InitialAlignment = CanvasSlot->GetAlignment();
        bCanvasInitialized = true;
    }
}

UAMSMapSubsystem* UAMSMapWidget::GetMapSubsystem() const
{
    const UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(this);
    return GameInstance->GetSubsystem<UAMSMapSubsystem>();
}

UCommonInputSubsystem* UAMSMapWidget::GetInputSubsystem() const
{
    const ULocalPlayer* BindingOwner = GetOwningLocalPlayer();
    return UCommonInputSubsystem::Get(BindingOwner);
}

void UAMSMapWidget::SetMapAreaByTag(const FName& mapArea)
{
    AreaTag = mapArea;
    AAMSMapArea* mapAreaBound = GetMapArea();

    SetMapArea(mapAreaBound);

}

void UAMSMapWidget::SetMapArea(AAMSMapArea* mapAreaBound)
{
	if (mapAreaBound/* && mapAreaBound != currentMapArea*/) {
		if (MapMaterial && MapBrush) {
			UTexture* areaTexture = mapAreaBound->GetMapTexture();
			UMaterialInstanceDynamic* dynamicMat = UKismetMaterialLibrary::CreateDynamicMaterialInstance(this, MapMaterial);
			CachedMapMaterial = dynamicMat;
			MapBrush->SetBrushFromMaterial(dynamicMat);
			dynamicMat->SetTextureParameterValue(TextureParameterName, areaTexture);
			if (mapAreaBound->IsFogEnabled()) {
				UTexture* fogTexture = CreateFogTexture();
				dynamicMat->SetTextureParameterValue(FogTextureParameterName, fogTexture);
				dynamicMat->SetScalarParameterValue(UseMapFogParameter, 1.f);
			}
            currentMapArea = mapAreaBound;
		}
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Invalid Area Tag! - UAMSMapWidget::SetMapArea"));
	}
}

void UAMSMapWidget::RefreshMaterials()
{
    ApplyMaskMaterial();
    if (CachedMapMaterial && MapBrush) {
        MapBrush->SetBrushFromMaterial(CachedMapMaterial);
    }
}



FVector2D UAMSMapWidget::GetMapOffset() const
{
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (CanvasSlot) {
        return CanvasSlot->GetPosition();
    }
    UE_LOG(LogTemp, Error, TEXT("Invalid Map Widget, missing canvas slot! - UAMSMapWidget::GetMapOffset"));
    return FVector2D();
}

FVector2D UAMSMapWidget::GetMapSize() const
{
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(MapBrush->Slot);
    if (CanvasSlot) {
        return CanvasSlot->GetSize();
    }
    UE_LOG(LogTemp, Error, TEXT("Invalid Map Widget, missing canvas slot! - UAMSMapWidget::GetMapSize"));
    return FVector2D();
}