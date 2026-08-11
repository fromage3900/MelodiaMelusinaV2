// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/Statement.h"
#include "Base/EvaluatedOption.h"

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SelectionBox.generated.h"

class AQuillscriptInterpreter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FSelectedDelegate, FStatement, Option );
DECLARE_DYNAMIC_MULTICAST_DELEGATE( FSelectionRollbackDelegate );

/**
 * Base class for selection box widgets classes and blueprints.
 */
UCLASS(Abstract, meta = ( DisplayName = "Selection Box Base" ))
class QUILLSCRIPT_API USelectionBox : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(AQuillscriptInterpreter* InInterpreter, const TArray<FStatement>& InSelections);

	/**
	 * Method used by the owner 'Interpreter' to start this widget.
	 * ! Has to be overriden in child Blueprints/classes.
	 *
	 * @param	Options	Pre-evaluated options.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript")
	void Play(const TArray<FEvaluatedOption>& Options);
	virtual void Play_Implementation(const TArray<FEvaluatedOption>& Options);

	/**
	 * Add this widget to the viewport at the specified layer.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript")
	void AddToViewportAtLayer();


	/// Data

	UFUNCTION(BlueprintPure, Category = "Quillscript|Data", meta = ( CompactNodeTitle = "Option", DefaultToSelf, HideSelfPin ))
	FStatement GetOption(const int32 Index);


	/// Getters and Setters

	UFUNCTION(BlueprintGetter)
	FORCEINLINE AQuillscriptInterpreter* GetInterpreter() const { return this->Interpreter; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE TArray<FStatement> GetSelections() const { return this->Selections; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetLayer() const { return this->Layer; }


	/// Events

	/** Option selected event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FSelectedDelegate OnSelected;

	/** Options rollback event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FSelectionRollbackDelegate OnRollback;


private:
	/** Owner 'Interpreter' that handles this 'Player Options'. */
	UPROPERTY(BlueprintGetter = GetInterpreter, Category = "Quillscript|References")
	TObjectPtr<AQuillscriptInterpreter> Interpreter;

	/** Complete 'Selection' for this *Selection. */
	UPROPERTY(BlueprintGetter = GetSelections, Category = "Quillscript|References")
	TArray<FStatement> Selections;

	/** User interface layer to render this widget. Leave -1 to use the plugin default value. */
	UPROPERTY(EditDefaultsOnly, BlueprintGetter = GetLayer, Category = "Quillscript|References")
	int32 Layer{ -1 };
};