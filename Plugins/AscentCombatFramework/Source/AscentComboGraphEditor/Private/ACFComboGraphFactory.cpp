#include "ACFComboGraphFactory.h"
#include "Graph/ACFComboGraph.h"

#define LOCTEXT_NAMESPACE "ADSGraphFactory"

UACFComboGraphFactory::UACFComboGraphFactory()
{
    bCreateNew = true;
    bEditAfterNew = true;
    SupportedClass = UACFComboGraph::StaticClass();
}

UObject* UACFComboGraphFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
    return NewObject<UObject>(InParent, Class, Name, Flags);
}

#undef LOCTEXT_NAMESPACE
