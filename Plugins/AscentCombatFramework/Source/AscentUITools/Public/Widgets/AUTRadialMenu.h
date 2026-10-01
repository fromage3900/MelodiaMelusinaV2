// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.
#pragma once

#include "Blueprint/UserWidget.h"
#include "Components/CanvasPanel.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "GameplayTags.h"
#include <Engine/DataAsset.h>
#include <Engine/Texture2D.h>

#include "AUTRadialMenu.generated.h"

/** Single item in the radial menu (name, icon, color, optional asset, enabled state). */
USTRUCT(BlueprintType)
struct FAUTRadialMenuItem {
    GENERATED_BODY()

    FAUTRadialMenuItem()
    {
        ItemName = TEXT("Default Item");
        ItemIcon = nullptr;
        ItemColor = FLinearColor::White;
        bIsEnabled = true;
        OriginAsset = nullptr;
    }

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    FString ItemName;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    TObjectPtr<UTexture2D> ItemIcon;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    FLinearColor ItemColor;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    UPrimaryDataAsset* OriginAsset;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    bool bIsEnabled;
};

/** Delegate broadcast when the user selects an item in the radial menu. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRadialMenuItemSelected, const FAUTRadialMenuItem&, MenuItem);

/**
 * Radial (pie) menu widget: items arranged in a circle, selectable by mouse angle or keys.
 * Set MenuItems and bind MenuCanvas; use SetItems/AddItem to update, SelectCurrentItem to confirm selection.
 */
UCLASS()
class ASCENTUITOOLS_API UAUTRadialMenu : public UUserWidget {
    GENERATED_BODY()

public:
    UAUTRadialMenu(const FObjectInitializer& ObjectInitializer);

    /** Broadcast when an item is selected (e.g. on click or confirm). */
    UPROPERTY(BlueprintAssignable, Category = "Radial Menu")
    FOnRadialMenuItemSelected OnItemSelected;

    UFUNCTION(BlueprintCallable, Category = "Radial Menu")
    void SelectCurrentItem();

    UFUNCTION(BlueprintCallable, Category = "Radial Menu")
    void UpdateMenuItems();

    UFUNCTION(BlueprintCallable, Category = "Radial Menu")
    int32 GetSelectedItemIndex() const { return SelectedItemIndex; }

    UFUNCTION(BlueprintCallable, Category = "Radial Menu")
    void SetItems(const TArray<FAUTRadialMenuItem>& Items);

    UFUNCTION(BlueprintCallable, Category = "Radial Menu")
    void AddItem(const FAUTRadialMenuItem& Item);

protected:
    void NativeConstruct() override;
    void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
    FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
    FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

private:

    void CreateMenuItems();
    void UpdateItemVisuals();
    FVector2D CalculateTextPosition(int32 ItemIndex) const;
    FVector2D CalculateItemPosition(int32 ItemIndex) const;
    int32 GetItemIndexFromMousePosition(const FVector2D& MousePosition) const;
    float GetAngleFromMousePosition(const FVector2D& MousePosition) const;
    void SetSelectedItem(int32 ItemIndex);
    void SetHoveredItem(int32 ItemIndex);

    /** List of items shown in the radial menu. */
    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    TArray<FAUTRadialMenuItem> MenuItems;

    /** Radius of the circle on which items are placed. */
    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    float MenuRadius;

    /** Size of each item (icon/text). */
    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    float ItemSize;

    /** Inner radius (optional ring / dead zone). */
    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    float InnerRadius;

    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    FLinearColor SelectedColor;

    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    FLinearColor HoveredColor;

    UPROPERTY(EditAnywhere, Category = "Radial Menu")
    FLinearColor DisabledColor;

    UPROPERTY(EditAnywhere,Category = "Radial Menu", meta = (BindWidget))
    UCanvasPanel* MenuCanvas;

    TArray<UImage*> ItemImages;
    TArray<UTextBlock*> ItemTexts;

    int32 SelectedItemIndex;
    int32 HoveredItemIndex;
    bool bIsMenuOpen;
    FVector2D MenuCenter;
    FVector2D LastMousePosition;
};