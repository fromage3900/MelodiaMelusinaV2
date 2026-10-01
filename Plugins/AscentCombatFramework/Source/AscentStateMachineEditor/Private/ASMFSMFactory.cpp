#include "ASMFSMFactory.h"
#include "Graph/ASMStateMachine.h"

#define LOCTEXT_NAMESPACE "ADSGraphFactory"

UASMFSMFactory::UASMFSMFactory()
{
    bCreateNew = true;
    bEditAfterNew = true;
    SupportedClass = UASMStateMachine::StaticClass();
}

UObject* UASMFSMFactory::FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
    return NewObject<UObject>(InParent, Class, Name, Flags);
}

#undef LOCTEXT_NAMESPACE
