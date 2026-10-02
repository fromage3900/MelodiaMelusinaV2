// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "ADSDialogueFactory.h"
#include "Graph/ADSDialogue.h"


#define LOCTEXT_NAMESPACE "ADSGraphFactory"

UADSDialogueFactory::UADSDialogueFactory()
{
	bCreateNew = true;
	bEditAfterNew = true;
	SupportedClass = UADSDialogue::StaticClass();
}


UObject* UADSDialogueFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return NewObject<UObject>(InParent, Class, Name, Flags | RF_Transactional);
}

#undef LOCTEXT_NAMESPACE
