// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "AMSMapsEditorSubsystem.generated.h"

class UTextureRenderTarget2D;

/**
 * 
 */
UCLASS()
class ASCENTMAPSEDITOR_API UAMSMapsEditorSubsystem : public UEditorSubsystem
{
	GENERATED_BODY()

public: 

	UFUNCTION(BlueprintCallable, Category = AMS)
    bool FromRenderTargetToTexture(UTextureRenderTarget2D* renderTarget, const FString& pathToSave, const FString& textureName);
	
};
