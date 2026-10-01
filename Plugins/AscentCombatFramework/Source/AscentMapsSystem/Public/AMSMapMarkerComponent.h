// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "Components/WidgetComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "AMSMapMarkerComponent.generated.h"

class UAMSMarkerWidget;

UCLASS(ClassGroup = (ANS), meta = (BlueprintSpawnableComponent))
class ASCENTMAPSSYSTEM_API UAMSMapMarkerComponent : public UWidgetComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UAMSMapMarkerComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /*Texture to be used to render this marker*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    UTexture2D* MarkerTexture;

    /*Useful to categorize and filter the various markers*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTagContainer MarkerCategory;

    /*Localized name of the marker used for UI*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FText MarkerName;

    /*ID of the marker, used the gather markers by name*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FString MarkerID = "Default Name";

    /*Indicates if this marker should rotate as the referenced actor
    when placed on the map*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    bool bShouldRotate = false;

    /*Indicates if we have to enable also the widget in this component in the world */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    bool bActivateWorldWidget = true;

public:
    /**
     * Gets the icon widget associated with this marker.
     * @return Pointer to the UAMSMarkerWidget.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UAMSMarkerWidget* GetIconWidget() const
    {
        return iconWidget;
    }

    /**
     * Adds a marker to the system.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void AddMarker();

    /**
     * Removes the marker from the system.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void RemoveMarker();

    /**
     * Gets the texture assigned to the marker.
     * @return Pointer to the UTexture2D used for the marker.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UTexture2D* GetMarkerTexture() const { return MarkerTexture; }

    /**
     * Gets the location of the owner of this marker.
     * @return The FVector representing the location.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FVector GetOwnerLocation() const;

    /**
     * Checks if the marker is currently marked.
     * @return True if marked, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsMarked() const;

    /**
     * Sets the texture for the marker.
     * @param val Pointer to the new UTexture2D texture.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMarkerTexture(UTexture2D* val) { MarkerTexture = val; }

    /**
     * Gets the category tag associated with the marker.
     * @return The FGameplayTag representing the marker category.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTagContainer GetMarkerCategory() const { return MarkerCategory; }

    /**
     * Gets the ID of the marker.
     * @return The marker id as an FString.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FString GetMarkerID() const
    {
        return MarkerID;
    }

    /**
     * Gets the name of the marker.
     * @return The marker name as a localizable FText.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FText GetMarkerName() const
    {
        return MarkerName;
    }

    /**
     * Sets the name of the marker.
     * @param inName The new marker name.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMarkerName(FText inName)
    {
        MarkerName = inName;
    }

    /**
     * Sets the ID of the marker.
     * @param inID The new marker ID.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMarkerID(const FString& inID)
    {
        MarkerID = inID;
    }

    /**
     * Sets the category tag of the marker.
     * @param val The new FGameplayTag category.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void AddMarkerCategory(FGameplayTag val)
    {
        MarkerCategory.AddTag(val);
    }

    /**
     * Gets the rotation of the owner.
     * @return The FRotator representing the owner's rotation.
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = ACF)
    FRotator GetOwnerRotation() const;

    /**
     * Checks if the marker should rotate.
     * @return True if the marker should rotate, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetShouldRotate() const { return bShouldRotate; }

    /**
     * Checks if the quest associated with this marker is being tracked.
     * @return True if the quest is tracked, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetTracked() const { return bTracked; }

    /**
     * Sets whether the quest associated with this marker is tracked.
     * @param val True to track the quest, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetTracked(bool val);

    /**
     * Determines if the marker should be shown on the compass.
     * @return True if it should be displayed, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool ShowOnCompass() const ;

    /**
     * Sets whether the marker should rotate.
     * @param val True to enable rotation, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetShouldRotate(bool val) { bShouldRotate = val; }

    /**
     * Checks if the world widget is activated for this marker.
     * @return True if the world widget is active, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetActivateWorldWidget() const { return bActivateWorldWidget; }

    /**
     * Sets whether the world widget should be activated.
     * @param val True to activate the world widget, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetActivateWorldWidget(bool val) { bActivateWorldWidget = val; }

private:
    TObjectPtr<UAMSMarkerWidget> iconWidget;

    // Id this component is target of a quest
    bool bTracked;
};
