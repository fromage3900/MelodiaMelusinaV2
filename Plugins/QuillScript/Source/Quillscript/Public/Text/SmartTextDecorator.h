// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Components/RichTextBlockDecorator.h"

class USmartTextBlockDecorator;


class FSmartTextDecorator final : public FRichTextDecorator
{
public:
    FSmartTextDecorator(URichTextBlock* InOwner, USmartTextBlockDecorator* InSmartTextBlockDecorator);
    virtual bool Supports(const FTextRunParseResults& RunParseResult, const FString& Text) const override;


protected:
    virtual TSharedPtr<SWidget> CreateDecoratorWidget(const FTextRunInfo& InRunInfo, const FTextBlockStyle& InTextStyle) const override;


private:
    TObjectPtr<USmartTextBlockDecorator> SmartTextBlockDecorator{ nullptr };
    TSharedPtr<FSlateBrush> CustomTooltipBrush;
};