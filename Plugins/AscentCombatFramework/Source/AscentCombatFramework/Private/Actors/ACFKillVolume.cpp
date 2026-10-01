// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Actors/ACFKillVolume.h"
#include "Actors/ACFCharacter.h"

void AACFKillVolume::ActorEnteredVolume(class AActor* Other)
{
    Super::ActorEnteredVolume(Other);
    AACFCharacter* character = Cast<AACFCharacter>(Other);
    if (character) {
        character->KillCharacter();
    }
}
