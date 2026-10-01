// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFDamageType.h"
#include "ACFTypes.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>

#include "ACFFunctionLibrary.generated.h"

class AACFCharacter;
struct FAttributesSet;
struct FStartingItem;
class UARSStatisticsComponent;
class UACMCollisionManagerComponent;
class UMovementComponent;
class AActor;

enum class EAIState : uint8;

/**
 *  UACFFunctionLibrary
 *  A utility Blueprint Function Library that provides helper functions for various gameplay mechanics in the
 *  Ascent Combat Framework (ACF). This library includes functions for damage calculation, directional hit detection,
 *  battle types, distance calculations, character interactions, and game state retrieval.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFFunctionLibrary : public UBlueprintFunctionLibrary {
	GENERATED_BODY()

public:
	// Determines the hit direction based on the attacker (hitDealer) and the hit result.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetHitDirectionByHitResult(const AActor* hitDealer, const FHitResult& hitResult);

	// Gets the relative direction vector of a damage event.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FVector GetActorsRelativeDirectionFromDamageEvent(const FACFDamageEvent& damageEvent);

	// Gets the relative direction vector for 2 actors
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FVector GetActorsRelativeDirectionVector(const AActor* source, const AActor* target);

	// Determines the relative direction of a hit based on the attacker's and receiver's positions.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetActorsRelativeDirection(const AActor* hitDealer, const AActor* receiver);

	// Determines movement direction based on input.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetDirectionFromInput(const AActor* actor, const FVector& direction);

	// Determines 8-direction movement based on input (Front, FrontRight, Right, BackRight, Back, BackLeft, Left, FrontLeft)
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetDirection8FromInput(const AActor* actor, const FVector& direction);

	// Gets the opposite relative direction of a given damage event.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FVector GetActorsOppositeRelativeDirection(const FACFDamageEvent& damageEvent);

	// Retrieves the default gameplay tag representing the death state.
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayTag GetDefaultDeathState();

	// Retrieves the default gameplay tag representing the hit state.
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayTag GetDefaultHitState();

	// Retrieves the gameplay tag associated with health.
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static FGameplayTag GetHealthTag();



	// Reduces a given damage amount by a specified percentage.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float ReduceDamageByPercentage(float Damage, float Percentage);

	// Plays an impact effect at a given location.
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static void PlayImpactEffect(const FImpactEffect& effect, const FVector& impactLocation, class AActor* instigator, const UObject* WorldContextObject);

	// Plays an action effect locally for a given character.
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static void PlayActionEffectLocally(const FActionEffect& effect, class ACharacter* instigator, const UObject* WorldContextObject,FComponentFX& outComps);

	// Plays a footstep effect for a given pawn and foot bone.
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static void PlayFootstepEffect(class APawn* instigator, FName footBone, const UObject* WorldContextObject);

	// Retrieves the current battle type from the game world.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static EBattleType GetBattleType(const UObject* WorldContextObject);

	// Determines if two teams are enemies.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool AreEnemyTeams(const UObject* WorldContextObject, const FGameplayTag& SelfTeam, const FGameplayTag& TargetTeam);


	// Calculates the distance between two actors.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float CalculateDistanceBetweenActors(const AActor* characterA, const AActor* characterB);

	// Computes a point at a specified distance and direction from an actor.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static FVector GetPointAtDirectionAndDistanceFromActor(const AActor* targetActor, const FVector& direction, float distance, bool bShowDebug = false);

	// Computes the distance between two characters, considering their extents.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float CalculateDistanceBetweenCharactersExtents(const ACharacter* characterA, const ACharacter* characterB);

	// Retrieves the extent (bounding box size) of a character.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float GetCharacterExtent(const ACharacter* characterA);

	// Calculates the distance from a character to a point, considering the character's extent.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float GetCharacterDistantToPointConsideringExtent(const ACharacter* characterA, const FVector& point);

	// Computes the angle between two vectors.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static float CalculateAngleBetweenVectors(const FVector& vectorA, const FVector& vectorB);

	// Retrieves the ACF HUD.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class AACFHUD* GetACFHUD(const UObject* WorldContextObject);

	// Retrieves the local ACF player controller.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class AACFPlayerController* GetLocalACFPlayerController(const UObject* WorldContextObject);

	// Retrieves the ACF game mode (server-only).
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class AACFGameMode* GetACFGameMode(const UObject* WorldContextObject);

	// Retrieves the ACF game state.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class AACFGameState* GetACFGameState(const UObject* WorldContextObject);

	// Retrieves the local ACF player character.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class AACFCharacter* GetLocalACFPlayerCharacter(const UObject* WorldContextObject);

	// Retrieves the ACF team manager component.
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static class UACFTeamManagerComponent* GetACFTeamManager(const UObject* WorldContextObject);

	// Determines if an action should be executed based on action chances and character stats.
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool ShouldExecuteAction(const FActionChances& action, const AACFCharacter* characterOwner);

	// Retrieves character attributes.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool GetCharacterAttributes(const TSubclassOf<class AACFCharacter>& characterClass, FAttributesSet& outData, bool bInitialize = true);

	// Retrieves the character's statistics component.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static UARSStatisticsComponent* GetCharacterStatisticComp(const TSubclassOf<class AACFCharacter>& characterClass, bool bInitialize = true);

	// Retrieves character defaults.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static AACFCharacter* GetCharacterDefaults(const TSubclassOf<class AACFCharacter>& characterClass);

	// Retrieves character starting items.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool GetCharacterStartingItems(const TSubclassOf<class AACFCharacter>& characterClass, TArray<FStartingItem>& outItems);

	// Retrieves a character's name.
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool GetCharacterName(const TSubclassOf<class AACFCharacter>& characterClass, FText& outName);

	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
	static AActor* FindNearestActorOfClass(const UObject* WorldContextObject, TSubclassOf<class AActor> actorToFind, AActor* origin);

	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static int32 ExtractIndexWithProbability(const TArray<float>& weights);

	/**
	 * Determines whether the pawn's view direction (control rotation) is oriented to the right of its current forward direction.
	 *
	 * @param Pawn The pawn whose view direction and orientation are used for comparison.
	 * @return true if the view is to the right, false if to the left. Returns false on failure.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool IsLookingRightRelativeToPawn(const APawn* Pawn);

	/**
	 * Checks whether the velocity of the given MovementComponent is directed toward the target actor,
	 * within the specified angular tolerance. Also outputs a [0..1] directional alignment value.
	 *
	 * @param MovementComp       The movement component whose velocity is evaluated.
	 * @param TargetActor        The actor used as the reference destination.
	 * @param ToleranceDegrees   Maximum allowed angle (in degrees) between the velocity and the direction to target.
	 * @param OutAlignment       [0..1] dot product between the velocity direction and the direction to target.
	 *                           1.0 = perfectly toward, 0.0 = perpendicular or moving away.
	 * @return true if the velocity points toward TargetActor within the given tolerance, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static bool IsVelocityTowardActor(const UMovementComponent* MovementComp, const AActor* TargetActor, float ToleranceDegrees, float& OutAlignment);

	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool IsShippingBuild();
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool IsEditor();

	/** Returns true if the project is configured as a demo version (ACF Project Settings > Packaging > bIsDemoVersion). Use this to tailor behavior in packaged builds. */
	UFUNCTION(BlueprintPure, Category = ACFLibrary)
	static bool IsDemoVersion();

	/** Returns the display name of an interactable actor.
	 *  Checks UACFInteractableComponent first; falls back to IACFInteractableInterface. */
	UFUNCTION(BlueprintPure, Category = "ACFLibrary|Interaction")
	static FText GetInteractableNameFromActor(AActor* Actor);

	/** Returns the collision manager component(s) for the given actor based on damage/trail target type (owner body, main hand, offhand, or both weapons). Uses FindComponentByClass. */
	UFUNCTION(BlueprintPure, Category = "ACF|Collision")
	static TArray<UACMCollisionManagerComponent*> GetCollisionManagersFromActor(const AActor* Owner, EDamageActivationType DamageType);

	// ========== Chooser Utilities ==========

	/**
	 * Recursively iterates through a Chooser table (including nested choosers) and builds a map
	 * of all AnimMontage assets found to their associated float values from a specified output column.
	 *
	 * @param ChooserTable The root chooser table to traverse
	 * @param FloatOutputColumnIndex The index of the float output column to extract values from (defaults to 0)
	 * @param OutMontageWeightMap The resulting map of UAnimMontage* -> float weight values
	 * @return True if the operation succeeded and found at least one montage
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Chooser")
	static bool BuildMontageWeightMapFromChooser(
		class UChooserTable* ChooserTable,
		int32 FloatOutputColumnIndex,
		TMap<UAnimMontage*, float>& OutMontageWeightMap);

	/**
	 * Similar to BuildMontageWeightMapFromChooser but returns all UObject assets (not just montages).
	 * Useful for generic asset extraction from chooser tables.
	 *
	 * @param ChooserTable The root chooser table to traverse
	 * @param FloatOutputColumnIndex The index of the float output column to extract values from
	 * @param OutAssetWeightMap The resulting map of UObject* -> float weight values
	 * @return True if the operation succeeded and found at least one asset
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Chooser")
	static bool BuildAssetWeightMapFromChooser(
		class UChooserTable* ChooserTable,
		int32 FloatOutputColumnIndex,
		TMap<UObject*, float>& OutAssetWeightMap);

private:
	/**
	 * Internal recursive helper that traverses chooser tables and extracts asset-weight pairs.
	 * Handles nested choosers automatically.
	 */
	static void RecursivelyExtractAssetWeights(
		const class UChooserTable* Chooser,
		int32 FloatOutputColumnIndex,
		TMap<UObject*, float>& OutMap);

	/**
	 * Extracts the float value from a specific output column and row in a chooser table.
	 * Returns 0.0 if the column is not a valid output float column or index is out of bounds.
	 */
	static float GetFloatValueFromOutputColumn(
		const class UChooserTable* Chooser,
		int32 ColumnIndex,
		int32 RowIndex);

};