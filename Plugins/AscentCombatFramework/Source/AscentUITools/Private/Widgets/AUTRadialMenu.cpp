// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Widgets/AUTRadialMenu.h"

#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanelSlot.h"
#include "Engine/Engine.h"
#include "Kismet/KismetMathLibrary.h"

UAUTRadialMenu::UAUTRadialMenu(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    MenuRadius = 200.0f;
    ItemSize = 64.0f;
    InnerRadius = 50.0f;
    SelectedColor = FLinearColor::Yellow;
    HoveredColor = FLinearColor::Green;
    DisabledColor = FLinearColor::Gray;

    SelectedItemIndex = -1;
    HoveredItemIndex = -1;
    bIsMenuOpen = false;
}

void UAUTRadialMenu::NativeConstruct()
{
    Super::NativeConstruct();

    // Find or create the canvas panel
    if (!MenuCanvas) {
        MenuCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("MenuCanvas"));
        WidgetTree->RootWidget = MenuCanvas;
    }

    SetHoveredItem(-1);
    SetSelectedItem(-1);
    CreateMenuItems();
    UpdateMenuItems();
}

void UAUTRadialMenu::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    UpdateItemVisuals();
}

FReply UAUTRadialMenu::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
    Super::NativeOnMouseMove(InGeometry, InMouseEvent);

    const FVector2D LocalMousePosition = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
    LastMousePosition = LocalMousePosition;

    // Calculate menu center
    MenuCenter = InGeometry.GetLocalSize() * 0.5f;

    // Check if mouse is within menu bounds
    const float DistanceFromCenter = FVector2D::Distance(LocalMousePosition, MenuCenter);

    if (DistanceFromCenter >= InnerRadius && DistanceFromCenter <= MenuRadius + ItemSize) {
        int32 NewHoveredIndex = GetItemIndexFromMousePosition(LocalMousePosition);
        SetHoveredItem(NewHoveredIndex);
    } else {
        SetHoveredItem(-1);
    }

    return FReply::Handled();
}

FReply UAUTRadialMenu::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
    Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);

    if (HoveredItemIndex >= 0 && HoveredItemIndex < MenuItems.Num()) {
        SelectCurrentItem();
        return FReply::Handled();
    }

    return FReply::Unhandled();
}

FReply UAUTRadialMenu::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
    Super::NativeOnKeyDown(InGeometry, InKeyEvent);
    return FReply::Unhandled();
}

void UAUTRadialMenu::SelectCurrentItem()
{
    if (HoveredItemIndex >= 0 && HoveredItemIndex < MenuItems.Num()) {
        if (MenuItems[HoveredItemIndex].bIsEnabled) {
            SetSelectedItem(HoveredItemIndex);
            OnItemSelected.Broadcast(MenuItems[HoveredItemIndex]);
        }
    }
}

void UAUTRadialMenu::UpdateMenuItems()
{
    if (!MenuCanvas) {
        return;
    }

    // Clear existing items
    ItemImages.Empty();
    ItemTexts.Empty();
    MenuCanvas->ClearChildren();

    CreateMenuItems();
    UpdateItemVisuals();
}

void UAUTRadialMenu::SetItems(const TArray<FAUTRadialMenuItem>& Items)
{
    MenuItems = Items;
}

void UAUTRadialMenu::AddItem(const FAUTRadialMenuItem& Item)
{
    MenuItems.Emplace(Item);
}

void UAUTRadialMenu::CreateMenuItems()
{
    if (!MenuCanvas || MenuItems.Num() == 0) {
        return;
    }

    for (int32 i = 0; i < MenuItems.Num(); i++) {
        // Calculate angle for this item
        float Angle = (2.0f * PI * i) / MenuItems.Num();
        float Radius = 150.0f; // Adjust this value for menu size

        // Calculate position relative to center
        FVector2D ItemPosition;
        ItemPosition.X = FMath::Cos(Angle) * Radius;
        ItemPosition.Y = FMath::Sin(Angle) * Radius;

        // Create image widget
        UImage* ItemImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),
            *FString::Printf(TEXT("ItemImage_%d"), i));
        if (MenuItems[i].ItemIcon) {
            ItemImage->SetBrushFromTexture(MenuItems[i].ItemIcon);
        }

        UCanvasPanelSlot* ImageSlot = MenuCanvas->AddChildToCanvas(ItemImage);
        ImageSlot->SetSize(FVector2D(ItemSize, ItemSize));
        ImageSlot->SetAlignment(FVector2D(0.5f, 0.5f));
        ImageSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f)); // Center anchor
        ImageSlot->SetPosition(ItemPosition);
        ItemImages.Add(ItemImage);

        // Create text widget (positioned below the image)
        UTextBlock* ItemText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),
            *FString::Printf(TEXT("ItemText_%d"), i));
        ItemText->SetText(FText::FromString(MenuItems[i].ItemName));
        ItemText->SetJustification(ETextJustify::Center);

        UCanvasPanelSlot* TextSlot = MenuCanvas->AddChildToCanvas(ItemText);
        TextSlot->SetSize(FVector2D(ItemSize * 1.5f, 20.0f));
        TextSlot->SetAlignment(FVector2D(0.5f, 0.5f));
        TextSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f)); // Center anchor

        // Position text slightly outside the image
        FVector2D TextPosition = ItemPosition;
        float TextRadius = Radius + (ItemSize * 0.5f) + 15.0f; // Offset from image
        TextPosition.X = FMath::Cos(Angle) * TextRadius;
        TextPosition.Y = FMath::Sin(Angle) * TextRadius;
        TextSlot->SetPosition(TextPosition);

        ItemTexts.Add(ItemText);
    }
}
void UAUTRadialMenu::UpdateItemVisuals()
{
    if (!MenuCanvas) {
        return;
    }

    for (int32 i = 0; i < MenuItems.Num(); i++) {
        if (i >= ItemImages.Num() || i >= ItemTexts.Num()) {
            continue;
        }

        FVector2D ItemPosition = CalculateItemPosition(i);

        // Update image
        if (UImage* ItemImage = ItemImages[i]) {
            if (UCanvasPanelSlot* ImageSlot = Cast<UCanvasPanelSlot>(ItemImage->Slot)) {
                // Set proper anchoring and alignment
                ImageSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
                ImageSlot->SetAlignment(FVector2D(0.5f, 0.5f));
                ImageSlot->SetPosition(ItemPosition);

                // Set color based on state
                FLinearColor ItemColor = MenuItems[i].ItemColor;
                if (!MenuItems[i].bIsEnabled) {
                    ItemColor = DisabledColor;
                } else if (i == SelectedItemIndex) {
                    ItemColor = SelectedColor;
                } else if (i == HoveredItemIndex) {
                    ItemColor = HoveredColor;
                }
                ItemImage->SetColorAndOpacity(ItemColor);

                // Apply animation scale
                float Scale = 1.0f + (i == HoveredItemIndex ? 0.2f : 0.0f);
                ItemImage->SetRenderScale(FVector2D(Scale, Scale));
            }
        }

        // Update text
        if (UTextBlock* ItemText = ItemTexts[i]) {
            if (UCanvasPanelSlot* TextSlot = Cast<UCanvasPanelSlot>(ItemText->Slot)) {
                // Set proper anchoring and alignment for text
                TextSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
                TextSlot->SetAlignment(FVector2D(0.5f, 0.5f));

                // Calculate text position with proper radial offset
                FVector2D TextPosition = CalculateTextPosition(i);
                TextSlot->SetPosition(TextPosition);
            }
        }
    }
}

FVector2D UAUTRadialMenu::CalculateItemPosition(int32 ItemIndex) const
{
    if (MenuItems.Num() == 0) {
        return FVector2D::ZeroVector;
    }

    const float AngleStep = 2.0f * PI / MenuItems.Num();
    const float Angle = ItemIndex * AngleStep - PI * 0.5f; // Start from top
    const float CurrentRadius = MenuRadius;

    // Return position relative to center (0,0) since we're using center anchors
    return FVector2D(CurrentRadius * FMath::Cos(Angle), CurrentRadius * FMath::Sin(Angle));
}

FVector2D UAUTRadialMenu::CalculateTextPosition(int32 ItemIndex) const
{
    if (MenuItems.Num() == 0) {
        return FVector2D::ZeroVector;
    }

    const float AngleStep = 2.0f * PI / MenuItems.Num();
    const float Angle = ItemIndex * AngleStep - PI * 0.5f; // Start from top
    const float TextRadius = MenuRadius + (ItemSize * 0.5f) + 15.0f; // Outside the images

    // Return position relative to center (0,0) since we're using center anchors
    return FVector2D(TextRadius * FMath::Cos(Angle), TextRadius * FMath::Sin(Angle));
}
int32 UAUTRadialMenu::GetItemIndexFromMousePosition(const FVector2D& MousePosition) const
{
    if (MenuItems.IsEmpty()) {
        return -1;
    }

    float Angle = GetAngleFromMousePosition(MousePosition);

    // Convert to index
    float AngleStep = 2.0f * PI / MenuItems.Num();
    int32 Index = FMath::RoundToInt(Angle / AngleStep) % MenuItems.Num();

    return FMath::Clamp(Index, 0, MenuItems.Num() - 1);
}

float UAUTRadialMenu::GetAngleFromMousePosition(const FVector2D& MousePosition) const
{
    const FVector2D Direction = MousePosition - MenuCenter;
    float Angle = FMath::Atan2(Direction.Y, Direction.X) + PI * 0.5f; // Offset to start from top

    // Normalize to 0-2π range
    if (Angle < 0) {
        Angle += 2.0f * PI;
    }

    return Angle;
}

void UAUTRadialMenu::SetSelectedItem(int32 ItemIndex)
{
    if (SelectedItemIndex != ItemIndex) {
        SelectedItemIndex = ItemIndex;
        UpdateItemVisuals();
    }
}

void UAUTRadialMenu::SetHoveredItem(int32 ItemIndex)
{
    if (HoveredItemIndex != ItemIndex) {
        HoveredItemIndex = ItemIndex;
        UpdateItemVisuals();
    }
}