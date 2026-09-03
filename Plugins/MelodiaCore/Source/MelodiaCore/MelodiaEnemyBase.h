#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaEnemyPresentationInterface.h"
#include "MelodiaEnemyBase.generated.h"

class UAnimMontage;
class USkeletalMeshComponent;
class UAnimInstance;

/** Native presentation shell for battle enemy actors. Blueprint enemy children (e.g.
 * BP_Enemy_SakuraPhantom) add their own SkeletalMeshComponent via SCS -- this base finds it
 * generically at runtime rather than declaring a native mesh component, so reparenting an
 * existing Actor-derived enemy Blueprint onto this class doesn't collide with per-enemy SCS
 * component names. */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaEnemyBase : public AActor, public IMelodiaEnemyPresentationInterface
{
	GENERATED_BODY()

public:
	AMelodiaEnemyBase();

	/** Played on OnMelodiaEnemyIntentStarted -- telegraphs the enemy's next attack. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Animation")
	TObjectPtr<UAnimMontage> IntentTelegraphMontage;

	/** Played on OnMelodiaEnemyHit -- reaction to taking damage. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Animation")
	TObjectPtr<UAnimMontage> HitReactionMontage;

	/** Played on OnMelodiaEnemyBroken -- stagger/vulnerable state. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Animation")
	TObjectPtr<UAnimMontage> BrokenMontage;

	/** Played on OnMelodiaEnemyDefeated -- death/dissolve animation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Animation")
	TObjectPtr<UAnimMontage> DefeatedMontage;

	virtual void OnMelodiaEnemyIntentStarted_Implementation(FName EnemyId, FName IntentId) override;
	virtual void OnMelodiaEnemyHit_Implementation(FName EnemyId, float Damage, EMelodiaRhythmGrade RhythmGrade) override;
	virtual void OnMelodiaEnemyBroken_Implementation(FName EnemyId) override;
	virtual void OnMelodiaEnemyDefeated_Implementation(FName EnemyId) override;

protected:
	/** Finds the enemy's own SkeletalMeshComponent (declared per-Blueprint via SCS) and plays
	 * Montage on it via its AnimInstance. No-op if Montage is unset or no mesh/anim instance found. */
	void PlayEnemyMontage(UAnimMontage* Montage) const;
};
