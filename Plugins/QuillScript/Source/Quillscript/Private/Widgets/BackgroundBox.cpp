// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/BackgroundBox.h"

#include "Core/QuillscriptSettings.h"


void UBackgroundBox::Setup(AQuillscriptInterpreter* InInterpreter, UTexture* InImage)
{
	this->Interpreter = InInterpreter;
	this->Image = InImage;
}

void UBackgroundBox::Play_Implementation(const UTexture* NewImage, const FString& Transition, const float Duration)
{
	// Override this method in child Blueprints/classes.
}

void UBackgroundBox::AddToViewportAtLayer()
{
	if (this->Layer == -1)
		this->Layer = UQuillscriptSettings::Get()->GetBackgroundBoxLayer();

	this->AddToViewport(this->Layer);
}