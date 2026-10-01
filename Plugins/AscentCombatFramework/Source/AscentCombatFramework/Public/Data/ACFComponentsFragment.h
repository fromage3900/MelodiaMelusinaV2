// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include "Components/ActorComponent.h"
#include "ACFComponentsFragment.generated.h"

/**
 * Fragment that adds ActorComponents to the pawn at initialization time.
 * Components are created with RF_Transient and registered on both server and client.
 * Useful for attaching gameplay components (e.g. custom AI, interaction, audio) via DataAsset
 * without modifying the base character Blueprint.
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class ASCENTCOMBATFRAMEWORK_API UACFComponentsFragment : public UACFCharacterFragment
{
	GENERATED_BODY()

public:
	/** Components to add to the pawn. Each class is instantiated once if not already present. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TArray<TSubclassOf<UActorComponent>> ComponentsToAdd;

	virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
