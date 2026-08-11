// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/Statement.h"

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "DialogBox.generated.h"

class AQuillscriptInterpreter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE( FDialogAdvanceDelegate );
DECLARE_DYNAMIC_MULTICAST_DELEGATE( FDialogRollbackDelegate );

/**
 * Base class for dialog box widgets classes and blueprints.
 */
UCLASS(Abstract, meta = ( DisplayName = "Dialog Box Base" ))
class QUILLSCRIPT_API UDialogBox : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(AQuillscriptInterpreter* InInterpreter, const FStatement& InDialogue);

	/**
	 * Method used by the owner 'Interpreter' to start this widget.
	 * ! Has to be overriden in child Blueprints/classes.
	 *
	 * @param	Speaker	Dialogue speaker's name.
	 * @param	Text	Dialogue text.
	 * @param	Tags	Dialogue tags.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript")
	void Play(const FString& Speaker, const FText& Text, const TArray<FString>& Tags);
	virtual void Play_Implementation(const FString& Speaker, const FText& Text, const TArray<FString>& Tags);

	/**
	 * Add this widget to the viewport at the specified layer.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript")
	void AddToViewportAtLayer();


	/// Getters and Setters

	UFUNCTION(BlueprintGetter)
	FORCEINLINE AQuillscriptInterpreter* GetInterpreter() const { return this->Interpreter; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE FStatement GetDialogue() const { return this->Dialogue; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetLayer() const { return this->Layer; }


	// Events

	/** Dialog advance event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FDialogAdvanceDelegate OnAdvance;

	/** Dialog rollback event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FDialogRollbackDelegate OnRollback;


private:
	/// References

	/** Owner 'Interpreter' that handles this 'Player Options'. */
	UPROPERTY(BlueprintGetter = GetInterpreter, Category = "Quillscript|References")
	TObjectPtr<AQuillscriptInterpreter> Interpreter;

	/** Complete 'Action' for this Dialogue. */
	UPROPERTY(BlueprintGetter = GetDialogue, Category = "Quillscript|References")
	FStatement Dialogue;

	/** User interface layer to render this widget. Leave -1 to use the plugin default value. */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetLayer, Category = "Quillscript|References")
	int32 Layer{ -1 };
};