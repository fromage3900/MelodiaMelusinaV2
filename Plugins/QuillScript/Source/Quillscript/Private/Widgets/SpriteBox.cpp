// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/SpriteBox.h"

#include "Core/QuillscriptInterpreter.h"
#include "Utils/Quill.h"


void USpriteBox::Setup(AQuillscriptInterpreter* InInterpreter)
{
	this->Interpreter = InInterpreter;
}

void USpriteBox::Destroy()
{
	this->RemoveFromParent();

	const FName SpriteName{ this->FindSpriteName() };
	UQuill::RemoveScriptReferenceByName(this, SpriteName);

	if (this->Interpreter->GetSpriteBoxes().Find(SpriteName))
		this->Interpreter->GetSpriteBoxes().Remove(SpriteName);

	this->ConditionalBeginDestroy();
}

FName USpriteBox::FindSpriteName() const
{
	if (this->Interpreter)
		for (const auto& SpriteBox : this->Interpreter->GetSpriteBoxes())
			if (SpriteBox.Value == this)
				return SpriteBox.Key;

	return NAME_None;
}