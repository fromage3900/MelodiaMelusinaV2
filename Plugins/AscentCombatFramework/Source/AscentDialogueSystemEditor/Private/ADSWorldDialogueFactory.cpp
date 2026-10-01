// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "ADSWorldDialogueFactory.h"
#include "Graph/ADSWorldDialogue.h"


#define LOCTEXT_NAMESPACE "ADSWorldGraphFactory"

UADSWorldDialogueFactory::UADSWorldDialogueFactory()
{
	bCreateNew = true;
	bEditAfterNew = true;
	SupportedClass = UADSWorldDialogue::StaticClass();
}


UObject* UADSWorldDialogueFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return NewObject<UObject>(InParent, Class, Name, Flags | RF_Transactional);
}

#undef LOCTEXT_NAMESPACE
