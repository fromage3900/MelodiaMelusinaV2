// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/DialogBox.h"

#include "Core/QuillscriptSettings.h"


void UDialogBox::Setup(AQuillscriptInterpreter* InInterpreter, const FStatement& InDialogue)
{
	this->Interpreter = InInterpreter;
	this->Dialogue = InDialogue;
}

void UDialogBox::Play_Implementation(const FString& Speaker, const FText& Text, const TArray<FString>& Tags)
{
	// Override this method in child Blueprints/classes.
}

void UDialogBox::AddToViewportAtLayer()
{
	if (this->Layer == -1)
		this->Layer = UQuillscriptSettings::Get()->GetDialogBoxLayer();

	this->AddToViewport(this->Layer);
}