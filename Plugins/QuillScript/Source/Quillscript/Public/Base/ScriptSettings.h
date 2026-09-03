// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Templates/SubclassOf.h"

#include "InputMode.h"
#include "Picker.h"

#include "CoreMinimal.h"
#include "ScriptSettings.generated.h"

/**
 * Quillscript Scene settings structure.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FScriptSettings
{
	GENERATED_BODY()


	/// Default Classes

	/** Default interpreter class. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Classes")
	TSubclassOf<class AQuillscriptInterpreter> InterpreterClass;

	/** Default Dialog Box widget class. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Classes")
	TSubclassOf<class UDialogBox> DialogBoxClass;

	/** Default Selection Box widget class. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Classes")
	TSubclassOf<class USelectionBox> SelectionBoxClass;

	/** Default Background Box widget class. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Classes")
	TSubclassOf<class UBackgroundBox> BackgroundBoxClass;

	/** Default Sprite Box widget class. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Classes")
	TSubclassOf<class USpriteBox> SpriteBoxClass;


	/// Input

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EPicker ShowMouseCursorDuring{ EPicker::Default };

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EPicker ShowMouseCursorAfter{ EPicker::Default };

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EPicker EnableInputDuring{ EPicker::Default };

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EPicker EnableInputAfter{ EPicker::Default };

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EInputMode InputModeDuring{ EInputMode::Default };

	/** . */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	EInputMode InputModeAfter{ EInputMode::Default };
};