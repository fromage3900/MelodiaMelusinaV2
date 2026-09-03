// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Base/TooltipTextStyle.h"
#include "Components/RichTextBlockDecorator.h"
#include "SmartTextBlockDecorator.generated.h"


UCLASS(Abstract, Blueprintable)
class USmartTextBlockDecorator : public URichTextBlockDecorator
{
    GENERATED_BODY()

public:
    static inline const FString DelayTagName{ "delay" };
    static inline const FString DelayShortTagOpen{ "((" };
    static inline const FString DelayShortTagClose{ "))" };


    virtual TSharedPtr<ITextDecorator> CreateDecorator(URichTextBlock* InOwner) override;


    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = Appearance)
    TMap<FString, FTooltipTextStyle> TooltipTags;


    /**
     * Convert a delay tag to seconds.
     */
    UFUNCTION(BlueprintCallable, Category = "Quillscript|Text|Delay")
    static float ConvertDelayToSeconds(FString Delay);

    /**
     * Count the delay time in a text.
     */
    UFUNCTION(BlueprintCallable, Category = "Quillscript|Text|Delay")
    static float CountDelayTime(FString Text);
};