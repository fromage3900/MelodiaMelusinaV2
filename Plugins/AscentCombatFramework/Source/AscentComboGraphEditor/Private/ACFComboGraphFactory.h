#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "ACFComboGraphFactory.generated.h"

UCLASS()
class ASCENTCOMBOGRAPHEDITOR_API UACFComboGraphFactory : public UFactory {
    GENERATED_BODY()

public:
    UACFComboGraphFactory();

    virtual UObject* FactoryCreateNew(UClass* Class, UObject* InParent,
        FName Name, EObjectFlags Flags,
        UObject* Context,
        FFeedbackContext* Warn) override;

    /** Returns an optional override brush name for the new asset menu. If this is
     * not specified, the thumbnail for the supported class will be used. */
    virtual FName GetNewAssetThumbnailOverride() const override
    {
        return "";
    }

    /** Returns the name of the factory for menus */
    virtual FText GetDisplayName() const override { return FText::FromString("Combo Graph"); }

    /** Returns the tooltip text description of this factory */
    virtual FText GetToolTip() const override
    {
        return FText::FromString("Creates a new Combo Graph");
    }

    /** Returns a new starting point name for newly created assets in the content
     * browser */
    virtual FString GetDefaultNewAssetName() const override
    {
        return "NewComboGraph";
    }
};
