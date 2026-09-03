// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BackgroundBox.generated.h"

class AQuillscriptInterpreter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams( FImageChangedDelegate, UTexture*, NewImage, UTexture*, OldImage );

/**
 * Base class for background box widgets classes and blueprints.
 */
UCLASS(Abstract, meta = ( DisplayName = "Background Box Base" ))
class QUILLSCRIPT_API UBackgroundBox : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(AQuillscriptInterpreter* InInterpreter, UTexture* InImage);

	/**
	 * Method used by the owner 'Interpreter' to start this widget.
	 * ! Has to be overriden in child Blueprints/classes.
	 *
	 * @param	NewImage	Reference to the texture used as a background image.
	 * @param	Transition	Transition animation name.
	 * @param	Duration	Transition duration in seconds.
	 */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = "Quillscript")
	void Play(const UTexture* NewImage, const FString& Transition, const float Duration);
	virtual void Play_Implementation(const UTexture* NewImage, const FString& Transition, const float Duration);

	/**
	 * Add this widget to the viewport at the specified layer.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript")
	void AddToViewportAtLayer();


	/// Getters and Setters

	UFUNCTION(BlueprintGetter)
	FORCEINLINE AQuillscriptInterpreter* GetInterpreter() const { return this->Interpreter; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UTexture* GetImage() const { return this->Image; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetLayer() const { return this->Layer; }


	/// Events

	/** Background image changed. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FImageChangedDelegate OnImageChanged;


private:
	/** Owner interpreter. */
	UPROPERTY(BlueprintGetter = GetInterpreter, Category = "Quillscript|References")
	TObjectPtr<AQuillscriptInterpreter> Interpreter;

	/** Current background. */
	UPROPERTY(BlueprintGetter = GetImage, Category = "Quillscript|References")
	TObjectPtr<UTexture> Image;

	/** User interface layer to render this widget. Leave -1 to use the plugin default value. */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetLayer, Category = "Quillscript|References")
	int32 Layer{ -1 };
};