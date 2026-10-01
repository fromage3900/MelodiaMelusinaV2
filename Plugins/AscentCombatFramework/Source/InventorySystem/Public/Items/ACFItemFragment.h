// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"

#include "ACFItemFragment.generated.h"

/*
 * Base class for item fragments used to compose item definitions in ACF Inventory System.
 * Can be extended in Blueprint to add custom data to items.
 */
UCLASS(Abstract, Blueprintable, EditInlineNew, DefaultToInstanced)
class INVENTORYSYSTEM_API UACFItemFragment : public UObject {
	GENERATED_BODY()

public:
	// Default constructor for the item fragment class.
	UACFItemFragment() {};


	/**
	 * Called when the owning item is equipped. Apply stat modifiers, GAS effects,
	 * register tick delegates, etc. here.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void ApplyFragment(APawn* pawnOwner, UACFItem* itemOwner);

	/**
	 * Called when the owning item is unequipped / removed.
	 * Clean up any effects or handles created in ApplyFragment.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void RemoveFragment(APawn* pawnOwner, UACFItem* itemOwner);
	virtual void RemoveFragment_Implementation(APawn* pawnOwner, UACFItem* itemOwner) {}

	/** Gets the Actor that owns this fragment (walks the outer chain). */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ACF|Fragment")
	AActor* GetOwningActor() const { return GetTypedOuter<AActor>(); }

	// ========================================================================
	// UObject Networking Overrides (enables opt-in replication)
	// ========================================================================

	virtual bool IsSupportedForNetworking() const override { return true; }
	virtual UWorld* GetWorld() const override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual int32 GetFunctionCallspace(UFunction* Function, FFrame* Stack) override;
	virtual bool CallRemoteFunction(UFunction* Function, void* Parms, struct FOutParmRec* OutParms, FFrame* Stack) override;
};