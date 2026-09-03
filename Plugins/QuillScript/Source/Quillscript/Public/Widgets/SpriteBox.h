// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SpriteBox.generated.h"

class UCanvasPanel;
class AQuillscriptInterpreter;

/**
 * Layer to place Dialogue Character Sprites.
 */
UCLASS(Abstract, meta = ( DisplayName = "Sprite Box Base" ))
class QUILLSCRIPT_API USpriteBox : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(AQuillscriptInterpreter* InInterpreter);

	/**
	 * Remove this Sprite Box from the Interpreter map and from the parent.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Data")
	void Destroy();

	/**
	 * Find this Sprite Box name in the Interpreter map.
	 * Return none if it can't find it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Data")
	FName FindSpriteName() const;


	/// Getters and Setters
	#pragma region GetSet

	UFUNCTION(BlueprintGetter)
	FORCEINLINE AQuillscriptInterpreter* GetInterpreter() const { return this->Interpreter; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UObject* GetCharacter() const { return this->Character; }

	#pragma endregion GetSet


private:
	/// References
	#pragma region References

	/** Owner 'Interpreter' that handles this 'Player Options'. */
	UPROPERTY(BlueprintGetter = GetInterpreter, Category = "Quillscript|References")
	TObjectPtr<AQuillscriptInterpreter> Interpreter;

	/** Asset to display in canvas. */
	UPROPERTY(BlueprintGetter = GetCharacter, Category = "Quillscript|References")
	TObjectPtr<UObject> Character;

	#pragma endregion References
};