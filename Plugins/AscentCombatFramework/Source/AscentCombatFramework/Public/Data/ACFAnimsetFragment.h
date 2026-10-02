// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"

#include "ACFAnimsetFragment.generated.h"

class UACFAnimsetDataAsset;

/**
 * Character fragment that applies an ACFAnimsetDataAsset to the pawn's ACFAnimInstance at
 * initialisation time. Add it to UACFCharacterDataAsset::Fragments to set (or hot-swap) the
 * full animation profile — movesets, overlays, rider layers, IK layer, and climbing layer —
 * driven purely from data without touching Blueprint or C++ anim instance defaults.
 *
 * The fragment is also safe to re-apply at runtime: call ApplyFragment on an already-spawned
 * pawn to swap the entire animation set on the fly (e.g. after an equipment change or
 * a class-change ability).
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class ASCENTCOMBATFRAMEWORK_API UACFAnimsetFragment : public UACFCharacterFragment
{
    GENERATED_BODY()

public:
    // The animset data asset to apply to the character's animation instance
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Animset")
    TObjectPtr<UACFAnimsetDataAsset> AnimsetData;

    virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
