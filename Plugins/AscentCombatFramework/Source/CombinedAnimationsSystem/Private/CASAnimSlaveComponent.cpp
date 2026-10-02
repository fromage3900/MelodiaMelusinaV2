// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "CASAnimSlaveComponent.h"
#include "CASTypes.h"
#include "CASAnimCondition.h"
#include <GameFramework/Character.h>
#include "GameplayTagContainer.h"

// Sets default values for this component's properties
UCASAnimSlaveComponent::UCASAnimSlaveComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);

	// ...
}


bool UCASAnimSlaveComponent::SupportsAnimation(const FGameplayTag& animTag) const
{
	if (SlaveAnimations) {
		FCombinedAnimsSlave* animConfig = nullptr;
		const auto& anims = SlaveAnimations->GetRowMap();
		for (const auto& anim : anims) {
			FCombinedAnimsSlave* currConfig = (FCombinedAnimsSlave*)anim.Value;
			if (currConfig && currConfig->AnimTag == animTag) {
				animConfig = currConfig;
				return true;
			}
		}
	}
	return false;
}

bool UCASAnimSlaveComponent::CanStartCombinedAnimation(const FGameplayTag& animTag, const ACharacter* animMaster)
{
	return SupportsAnimation( animTag) && VerifyConditions(animTag, animMaster);	
}

bool UCASAnimSlaveComponent::TryGetSlaveAnim(const FGameplayTag& animTag, FCombinedAnimsSlave& outSlave) const
{
	if (SlaveAnimations) {
		const auto& anims = SlaveAnimations->GetRowMap();
		for (const auto& anim : anims) {
			FCombinedAnimsSlave* currConfig = (FCombinedAnimsSlave*)anim.Value;
			if (currConfig && currConfig->AnimTag == animTag) {
				outSlave = *currConfig;
				return true;
			}
		}
	}
	return false;
}

bool UCASAnimSlaveComponent::VerifyConditions(const FGameplayTag& animTag, const ACharacter* animMaster)
{
    /*
	for (const auto condition : AnimStartingConditions) {
		if (!condition->Internal_VerifyCondition(this, animTag,  animMaster)) {
			return false;
		}
	}*/
	return true;
}

// Called when the game starts
void UCASAnimSlaveComponent::BeginPlay()
{
	Super::BeginPlay();

	characterOwner = Cast<ACharacter>(GetOwner());
	
}


