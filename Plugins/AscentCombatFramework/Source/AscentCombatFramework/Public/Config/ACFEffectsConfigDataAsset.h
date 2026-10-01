// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFTypes.h"

#include "ACFEffectsConfigDataAsset.generated.h"

/**
 * Data Asset used to configure FX-related parameters for footsteps and other effects.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFEffectsConfigDataAsset : public UPrimaryDataAsset {
	GENERATED_BODY()

protected:
	/*Enable terrain material check for footsteps*/
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF| Footstep")
	bool bCheckForSurface = false;

	/*Effect played on Footstep when CheckForSurface is DISABLED*/
	UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "!bCheckForSurface"), EditDefaultsOnly, Category = "ACF| Footstep")
	FBaseFX DefaultFootstepFX;

	/*Effects played on Footstep when CheckForSurface is ENABLED, depending on the actual
	terrain surface physical material*/
	UPROPERTY(BlueprintReadOnly, meta = (EditCondition = "bCheckForSurface"), EditDefaultsOnly, Category = "ACF| Footstep")
	TMap<TEnumAsByte<EPhysicalSurface>, FBaseFX> FootstepEffectsBySurface;

	/*Effects triggered when this character gets hit depending on the DamageType Received.
	Location will always be the impact point*/
	UPROPERTY(BlueprintReadOnly, meta = (TitleProperty = "TagName"), EditDefaultsOnly, Category = "ACF| Damages")
	TArray<FEffectByDamageType> DamageEffectsByHitReaction;

	/*Effects triggered when this character avoids an hit*/
	UPROPERTY(BlueprintReadOnly, meta = (TitleProperty = "TagName"), EditDefaultsOnly, Category = "ACF| Damages")
	TMap<FGameplayTag, FBaseFX> DamageAvoidedEffects;

public:
	bool ShouldCheckForSurface() const
	{
		return bCheckForSurface;
	}

	void GetDefaultFootstepFX(FBaseFX& outFX) const
	{
		outFX = DefaultFootstepFX;
	}

	bool TryGetFootstepFXBySurfaceType(const EPhysicalSurface& inSurface, FBaseFX& outFX) const
	{
		if (FootstepEffectsBySurface.Contains(inSurface)) {
			outFX = *FootstepEffectsBySurface.Find(inSurface);
			return true;
		}
		outFX = DefaultFootstepFX;
		return false;
	}

	bool TryGetDamageEffectsByHitReactionAndDamageType(const FGameplayTag& HitReaction,
		const TSubclassOf<UDamageType>& damageType, FBaseFX& outFX)
	{
		FEffectByDamageType* effectList;
		if (HitReaction == FGameplayTag()) {
			effectList = DamageEffectsByHitReaction.FindByKey(UACFFunctionLibrary::GetDefaultHitState());
		}
		else {
			effectList = DamageEffectsByHitReaction.FindByKey(HitReaction);
		}

		if (!effectList) {
			return false;
		}

		if (effectList->EffectByDamageType.Contains(damageType)) {
			outFX = *effectList->EffectByDamageType.Find(damageType);
			return true;
		}
		else {
			for (auto& currentDam : effectList->EffectByDamageType) {
				if (damageType->IsChildOf(currentDam.Key)) {
					outFX = currentDam.Value;
					return true;
				}
			}
		}

		return false;
	}

	/** Returns the FX configured for a given damage-avoided reaction tag (e.g. parry, dodge). */
	bool TryGetDamageAvoidedFX(const FGameplayTag& avoidedTag, FBaseFX& outFX) const
	{
		if (DamageAvoidedEffects.Contains(avoidedTag)) {
			outFX = *DamageAvoidedEffects.Find(avoidedTag);
			return true;
		}
		return false;
	}
};
