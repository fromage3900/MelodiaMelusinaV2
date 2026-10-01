 // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFInputBufferNotifyState.h"
#include "ACFComboComponent.h"
#include <Components/SkeletalMeshComponent.h>

void UACFInputBufferNotifyState::NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
    SetBufferEnabled(MeshComp, true);
}

void UACFInputBufferNotifyState::SetBufferEnabled(USkeletalMeshComponent* MeshComp, bool bEnabled)
{
    if (MeshComp) {
        AActor* owner = MeshComp->GetOwner();
        if (owner) {
            UACFComboComponent* comboComp = owner->FindComponentByClass<UACFComboComponent>();
            if (comboComp) {
                comboComp->SetInputBufferOpened(bEnabled);
            }
        }
    }
}

void UACFInputBufferNotifyState::NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
    SetBufferEnabled(MeshComp, false);

}
