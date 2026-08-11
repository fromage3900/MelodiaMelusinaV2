// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/SelectionBox.h"

#include "Core/QuillscriptSettings.h"


void USelectionBox::Setup(AQuillscriptInterpreter* InInterpreter, const TArray<FStatement>& InSelections)
{
	this->Interpreter = InInterpreter;
	this->Selections = InSelections;
}

void USelectionBox::Play_Implementation(const TArray<FEvaluatedOption>& Options)
{
	// Override this method in child Blueprints/classes.
}

void USelectionBox::AddToViewportAtLayer()
{
	if (this->Layer == -1)
		this->Layer = UQuillscriptSettings::Get()->GetSelectionBoxLayer();

	this->AddToViewport(this->Layer);
}

FStatement USelectionBox::GetOption(const int32 Index)
{
	if (this->Selections.IsValidIndex(Index))
		return this->Selections[Index];

	return FStatement();
}