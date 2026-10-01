// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "ADSWorldDialogueFactory.generated.h"


UCLASS()
class ASCENTDIALOGUESYSTEMEDITOR_API UADSWorldDialogueFactory : public UFactory {
  GENERATED_BODY()

public:
  UADSWorldDialogueFactory();

  virtual UObject *FactoryCreateNew(UClass *Class, UObject *InParent,
                                    FName Name, EObjectFlags Flags,
                                    UObject *Context,
                                    FFeedbackContext *Warn) override;



  /** Returns the name of the factory for menus */
  virtual FText GetDisplayName() const override { return  FText::FromString("World Dialogue"); }

  /** Returns the tooltip text description of this factory */
  virtual FText GetToolTip() const override {
    return  FText::FromString("Creates a new World Dialogue Graph");
  }

  /** Returns a new starting point name for newly created assets in the content
   * browser */
  virtual FString GetDefaultNewAssetName() const override {
    return "NewWorldDialogue";
  }
};
