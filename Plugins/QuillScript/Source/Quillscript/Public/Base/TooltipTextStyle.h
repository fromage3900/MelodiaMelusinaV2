// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Styling/SlateTypes.h"
#include "TooltipTextStyle.generated.h"


/**
 * Quillscript Rich Text Block Decorator tooltip tags.
 */
USTRUCT(BlueprintType)
struct QUILLSCRIPT_API FTooltipTextStyle
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FTextBlockStyle TextStyle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FSlateBrush TextBorderBrush;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FMargin TextPadding{ 0, 0, 0, 0 };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FTextBlockStyle TooltipStyle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FSlateBrush TooltipBorderBrush;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Text")
	FMargin TooltipPadding{ 10, 5, 10, 5 };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Widget")
	TSubclassOf<UUserWidget> TextWidgetClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Widget")
	TSubclassOf<UUserWidget> TooltipWidgetClass;
};