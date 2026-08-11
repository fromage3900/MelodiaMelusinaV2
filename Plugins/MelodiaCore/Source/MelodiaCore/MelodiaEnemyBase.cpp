#include "MelodiaEnemyBase.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"

AMelodiaEnemyBase::AMelodiaEnemyBase()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AMelodiaEnemyBase::OnMelodiaEnemyIntentStarted_Implementation(FName EnemyId, FName IntentId)
{
	PlayEnemyMontage(IntentTelegraphMontage);
}

void AMelodiaEnemyBase::OnMelodiaEnemyHit_Implementation(FName EnemyId, float Damage, EMelodiaRhythmGrade RhythmGrade)
{
	PlayEnemyMontage(HitReactionMontage);
}

void AMelodiaEnemyBase::OnMelodiaEnemyBroken_Implementation(FName EnemyId)
{
	PlayEnemyMontage(BrokenMontage);
}

void AMelodiaEnemyBase::OnMelodiaEnemyDefeated_Implementation(FName EnemyId)
{
	PlayEnemyMontage(DefeatedMontage);
}

void AMelodiaEnemyBase::PlayEnemyMontage(UAnimMontage* Montage) const
{
	if (!Montage)
	{
		return;
	}

	const USkeletalMeshComponent* Mesh = FindComponentByClass<USkeletalMeshComponent>();
	UAnimInstance* AnimInstance = Mesh ? Mesh->GetAnimInstance() : nullptr;
	if (AnimInstance)
	{
		AnimInstance->Montage_Play(Montage);
	}
}
