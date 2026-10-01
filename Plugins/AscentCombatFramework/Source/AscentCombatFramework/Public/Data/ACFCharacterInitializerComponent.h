// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Game/ACFTypes.h"
#include "ACFCharacterInitializerComponent.generated.h"

class UACFCharacterDataAsset;
class AACFCharacter;

/**
 * * Component that initializes an ACF character from a UACFCharacterDataAsset.
 * Applies stats, abilities, equipment, appearance, team and fragments. Set CharacterInitDataAsset
 * and CharacterInitLevel in the Details panel; the owning AACFCharacter calls Init automatically when bAutoInit is true.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFCharacterInitializerComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UACFCharacterInitializerComponent();

	/**
	 * * Initializes the character from the Data Asset and Level set on this component.
	 * Uses CharacterInitDataAsset and CharacterInitLevel. No parameters required.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void Init();

	/**
	 * * Initializes the character from an explicit Data Asset and level.
	 * @param charData The character Data Asset to apply (stats, appearance, equipment, etc.).
	 * @param Level The level to set for stats and scaling.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void InitFromDataAsset(UACFCharacterDataAsset* charData, int32 Level);

	/**
	 * * Applies mesh, materials and anim instance from the current CharacterDataAsset to all matching skeletal components.
	 * @param bOverrideAnimInstance If true, replaces the anim instance class on each mesh.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ApplyAllMeshData(bool bOverrideAnimInstance = true);

	/**
	 * * Applies only appearance (mesh components) from the given Data Asset.
	 * @param charData The Data Asset containing MeshComponents to apply.
	 * @param bOverrideAnimInstance If true, replaces the anim instance class on each mesh.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ApplyAppearanceFromDataAsset(UACFCharacterDataAsset* charData, bool bOverrideAnimInstance = true);

	/**
	 * * Returns the Data Asset currently applied (after init or replication).
	 * @return The resolved Character Data Asset, or nullptr if not yet initialized.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFCharacterDataAsset* GetCharacterDataAsset() { return CharacterDataAsset; }

	/**
	 * * Returns the Data Asset set in the Details panel for auto-init.
	 * @return The Character Init Data Asset property value.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFCharacterDataAsset* GetAutoInitDataAsset() const { return CharacterInitDataAsset; }

	/**
	 * * Returns the level set in the Details panel for auto-init.
	 * @return The Character Init Level property value.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	int32 GetAutoInitLevel() const { return CharacterInitLevel; }

	/** Applies the given mesh/appearance array to the owner's skeletal components. */
	void ApplyAppearence(const TArray<FSkeletalMeshComponentData>& appearence, bool bOverrideAnimInstance = true);

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;

	/** Re-applies appearance from CharacterInitDataAsset to the owner in the editor.
	 *  Useful after editing the data asset to preview the changes on the placed actor. */
	UFUNCTION(CallInEditor, Category = "ACF")
	void ApplyAppearanceInEditor();
#endif

protected:
	virtual void InitializeComponent() override;
	virtual void BeginPlay() override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	void InternalHandleServerInit(int32 Level, bool bApplyAppearance = true);
	void InternalHandleClientInit(bool bApplyAppearance = true);

	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void HandleServerInit();
	virtual void HandleServerInit_Implementation() {}

	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void HandleClientInit();
	virtual void HandleClientInit_Implementation() {}

	/** Data Asset used to initialize this character. Set in the Details panel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TObjectPtr<UACFCharacterDataAsset> CharacterInitDataAsset;

	/** Level applied when initializing from CharacterInitDataAsset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF", meta = (ClampMin = "1", ClampMax = "100", EditCondition = "CharacterInitDataAsset != nullptr"))
	int32 CharacterInitLevel = 1;

	void ApplyMeshDataToComponent(USkeletalMeshComponent* Component, const FSkeletalMeshComponentData& MeshData, bool bOverrideAnimInstance);

	/** Resolved Data Asset after init. Replicated as a hard asset reference so clients
	 *  receive the same data asset without needing the Asset Manager registration. */
	UPROPERTY(ReplicatedUsing = OnRep_CharacterDataAsset, BlueprintReadOnly, Category = "ACF|Character Data")
	UACFCharacterDataAsset* CharacterDataAsset;

	UFUNCTION()
	void OnRep_CharacterDataAsset();

	/** Cached owner as AACFCharacter. */
	UPROPERTY(Category = ACF, BlueprintReadOnly)
	AACFCharacter* OwningPawn;

	void ApplyFragmentsData();
	void ApplyEquipData();
	/** Reads CapsuleHalfHeight/CapsuleRadius from CharacterDataAsset and applies them to the owner's UCapsuleComponent. */
	void ApplyCapsuleSize();
	/** Re-broadcasts OnEquipmentChanged so the AnimBP layers get re-linked even when there is no starting weapon. */
	void RefreshAnimationLayers();

private:
	bool bAppliedAutoAppearanceBeforeBeginPlay = false;
};
