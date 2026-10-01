
#include "ACFSkillTreeFactory.h"
#include "Graph/ACFSkillTreeGraph.h"

#define LOCTEXT_NAMESPACE "ACFSkillTreeFactory"

UACFSkillTreeFactory::UACFSkillTreeFactory()
{
    bCreateNew = true;
    bEditAfterNew = true;
    SupportedClass = UACFSkillTreeGraph::StaticClass();
}

UObject* UACFSkillTreeFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
    return NewObject<UObject>(InParent, Class, Name, Flags);
}

#undef LOCTEXT_NAMESPACE
