#include "AQSQuestFactory.h"
#include "Graph/AQSQuest.h"




#define LOCTEXT_NAMESPACE "AQSGraphFactory"

UAQSQuestFactory::UAQSQuestFactory()
{
	bCreateNew = true;
	bEditAfterNew = true;
	SupportedClass = UAQSQuest::StaticClass();
}


UObject* UAQSQuestFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return NewObject<UObject>(InParent, Class, Name, Flags | RF_Transactional);
}

#undef LOCTEXT_NAMESPACE

