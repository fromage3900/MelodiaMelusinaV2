// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Game/ACFFunctionLibrary.h"
#include "Components/ACFInteractableComponent.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "ACFActionsFunctionLibrary.h"
#include "ACFDeveloperSettings.h"
#include "ACFGASDeveloperSettings.h"
#include "ACFLegacyStatisticsComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include "ACFTeamsConfigDataAsset.h"
#include "ACMCollisionManagerComponent.h"
#include "ACMEffectsDispatcherComponent.h"
#include "ARSTypes.h"
#include "Actors/ACFCharacter.h"
#include "Camera/CameraShakeBase.h"
#include "Components//ACFTeamManagerComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Game/ACFDamageCalculation.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFGameMode.h"
#include "Game/ACFGameState.h"
#include "Game/ACFPlayerController.h"
#include "Game/ACFTypes.h"
#include "Items/ACFWorldItem.h"
#include "Logging.h"
#include "Sound/SoundClass.h"
#include "UI/ACFHUD.h"
#include <Components/AudioComponent.h>
#include <Curves/CurveFloat.h>
#include <Engine/DataTable.h>
#include <Engine/LevelStreaming.h>
#include <GameFramework/Actor.h>
#include <GameplayTagContainer.h>
#include <GameplayTagsManager.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>
#include <NavigationSystem.h>
#include <Sound/SoundCue.h>
#include "Engine/World.h"
#include <Engine/Engine.h>
#include <GameFramework/MovementComponent.h>

// Chooser includes
#include "Chooser.h"
#include "IObjectChooser.h"
#include "IChooserColumn.h"
#include "ObjectChooser_Asset.h"
#include "OutputFloatColumn.h"


EACFDirection UACFFunctionLibrary::GetActorsRelativeDirection(const AActor* hitDealer, const AActor* receiver)
{
    if (!hitDealer || !receiver) {
        UE_LOG(ACFLog, Error, TEXT("INVALID HitReceiver or Dealer! - UACFFunctionLibrary::GetActorsRelativeDirection "));

        return EACFDirection::Back;
    }

    const FVector damageDealerRelative = hitDealer->GetActorLocation()
        - receiver->GetActorLocation();

    const FVector hitDir = damageDealerRelative.GetUnsafeNormal();
    return GetDirectionFromInput(receiver, hitDir);
}

FVector UACFFunctionLibrary::GetActorsRelativeDirectionVector(const AActor* source, const AActor* target)
{
	if (source && target) {
		const FVector damageDealerRelative = source->GetActorLocation() - target->GetActorLocation();

		return damageDealerRelative.GetUnsafeNormal();
	}

	return FVector();
}

EACFDirection UACFFunctionLibrary::GetDirectionFromInput(const AActor* actor, const FVector& direction)
{

    if (!actor) {
        UE_LOG(ACFLog, Error, TEXT("INVALID ACTOR! - UACFFunctionLibrary::GetDirectionFromInput "));

        return EACFDirection::Front;
    }
    const float forwardDot = FVector::DotProduct(actor->GetActorForwardVector(), direction);
    const float rightDot = FVector::DotProduct(actor->GetActorRightVector(), direction);
    if (forwardDot >= 0.2f) {
        return EACFDirection::Front;
    } else if (rightDot >= 0.707f) {
        return EACFDirection::Right;
    } else if (rightDot <= -0.707f) {
        return EACFDirection::Left;

    } else {
        return EACFDirection::Back;
    }
}

EACFDirection UACFFunctionLibrary::GetDirection8FromInput(const AActor* actor, const FVector& direction)
{
    if (!actor) {
        UE_LOG(ACFLog, Error, TEXT("INVALID ACTOR! - UACFFunctionLibrary::GetDirection8FromInput "));
        return EACFDirection::Front;
    }

    const float forwardDot = FVector::DotProduct(actor->GetActorForwardVector(), direction);
    const float rightDot = FVector::DotProduct(actor->GetActorRightVector(), direction);

    // 8-direction detection using octants (22.5° threshold for each cardinal direction)
    // Thresholds: cos(22.5°) ≈ 0.924, cos(67.5°) ≈ 0.383

    if (forwardDot >= 0.924f) {
        // Front (337.5° - 22.5°)
        return EACFDirection::Front;
    } else if (forwardDot >= 0.383f && rightDot >= 0.383f) {
        // Front-Right (22.5° - 67.5°)
        return EACFDirection::FrontRight;
    } else if (rightDot >= 0.924f) {
        // Right (67.5° - 112.5°)
        return EACFDirection::Right;
    } else if (forwardDot <= -0.383f && rightDot >= 0.383f) {
        // Back-Right (112.5° - 157.5°)
        return EACFDirection::BackRight;
    } else if (forwardDot <= -0.924f) {
        // Back (157.5° - 202.5°)
        return EACFDirection::Back;
    } else if (forwardDot <= -0.383f && rightDot <= -0.383f) {
        // Back-Left (202.5° - 247.5°)
        return EACFDirection::BackLeft;
    } else if (rightDot <= -0.924f) {
        // Left (247.5° - 292.5°)
        return EACFDirection::Left;
    } else {
        // Front-Left (292.5° - 337.5°)
        return EACFDirection::FrontLeft;
    }
}

EACFDirection UACFFunctionLibrary::GetHitDirectionByHitResult(const AActor* hitDealer, const FHitResult& hitResult)
{
    ensure(hitDealer);

    AActor* receiver = hitResult.GetActor();

    return GetActorsRelativeDirection(hitDealer, receiver);
}

FVector UACFFunctionLibrary::GetActorsRelativeDirectionFromDamageEvent(const FACFDamageEvent& damageEvent)
{
    const AActor* source = damageEvent.DamageDealer;
    const AActor* target = damageEvent.DamageReceiver;
    return GetActorsRelativeDirectionVector(source, target);

}

FVector UACFFunctionLibrary::GetActorsOppositeRelativeDirection(const FACFDamageEvent& damageEvent)
{
    return -GetActorsRelativeDirectionFromDamageEvent(damageEvent);
}

FGameplayTag UACFFunctionLibrary::GetDefaultDeathState()
{
    UACFDeveloperSettings* settings = GetMutableDefault<UACFDeveloperSettings>();

    if (settings) {
        return settings->DefaultDeathState;
    }

    return FGameplayTag();
}

FGameplayTag UACFFunctionLibrary::GetDefaultHitState()
{
    UACFDeveloperSettings* settings = GetMutableDefault<UACFDeveloperSettings>();

    if (settings) {
        return settings->DefaultHitState;
    }

    return FGameplayTag();
}

FGameplayTag UACFFunctionLibrary::GetHealthTag()
{
    const UACFGASDeveloperSettings* settings = GetDefault<UACFGASDeveloperSettings>();

    if (settings) {
        return settings->GetHealthTag();
    }

    return FGameplayTag();
}


float UACFFunctionLibrary::ReduceDamageByPercentage(float Damage, float Percentage)
{
    const float _deviation = Damage * Percentage / 100;
    return FMath::Clamp(Damage - _deviation, 0.f, BIG_NUMBER);
}

void UACFFunctionLibrary::PlayImpactEffect(const FImpactEffect& effect, const FVector& impactLocation, class AActor* instigator, const UObject* WorldContextObject)
{

    if (effect.CameraShake && effect.bShouldShakeCamera && WorldContextObject) {
        UGameplayStatics::PlayWorldCameraShake(WorldContextObject, effect.CameraShake, impactLocation, 0.f, effect.ShakeRadius, effect.ShakeFalloff);
    }

    if (effect.bShouldMakeDamage && instigator) {
        UACMCollisionManagerComponent* collComp = instigator->FindComponentByClass<UACMCollisionManagerComponent>();

        if (!collComp) {
            return;
        }

        collComp->StartTimedSingleTrace(effect.DamageTraceName, effect.DamageTraceDuration);
    }
}

void UACFFunctionLibrary::PlayActionEffectLocally(const FActionEffect& effect, class ACharacter* instigator, const UObject* WorldContextObject,FComponentFX& outComps)
{
    AGameStateBase* gameState = UGameplayStatics::GetGameState(WorldContextObject);

    if (gameState) {
        UACMEffectsDispatcherComponent* EffectComp = gameState->FindComponentByClass<UACMEffectsDispatcherComponent>();
        if (EffectComp) {
            EffectComp->PlayActionEffectLocally(effect, instigator,outComps);
            return;
        }
        ensure(EffectComp);
    }

    UE_LOG(ACFLog, Warning, TEXT("Missing ACFGameState! - UACFFunctionLibrary "));
}

void UACFFunctionLibrary::PlayFootstepEffect(class APawn* instigator, FName footBone /*= NAME_None*/, const UObject* WorldContextObject)
{
    UACFEffectsManagerComponent* effectsComp = instigator->FindComponentByClass<UACFEffectsManagerComponent>();
    if (effectsComp) {
        effectsComp->TriggerFootstepFX(footBone);
    }
}

EBattleType UACFFunctionLibrary::GetBattleType(const UObject* WorldContextObject)
{
    const AGameStateBase* gameState = UGameplayStatics::GetGameState(WorldContextObject);

    if (gameState) {
        return gameState->FindComponentByClass<UACFTeamManagerComponent>()->GetBattleType();
    } else {
        UE_LOG(ACFLog, Warning, TEXT("Trying to get battle type from client! COnfigurations must be done on server!! - UACFFunctionLibrary "));
    }
    return EBattleType::ETeamBased;
}

bool UACFFunctionLibrary::AreEnemyTeams(const UObject* WorldContextObject, const FGameplayTag& SelfTeam, const FGameplayTag& TargetTeam)
{
    if (const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull)) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            return TeamSubsystem->AreTeamsHostile(SelfTeam, TargetTeam);
        }
    }
    UE_LOG(ACFLog, Error, TEXT("Missing ACFGameState! - UACFFunctionLibrary::AreEnemyTeams "));
    return false;
}

float UACFFunctionLibrary::CalculateDistanceBetweenActors(const AActor* characterA, const AActor* characterB)
{
    const ACharacter* owner = Cast<ACharacter>(characterA);
    const ACharacter* target = Cast<ACharacter>(characterB);

    if (owner && target) {
        return CalculateDistanceBetweenCharactersExtents(owner, target);
    }
    return owner->GetDistanceTo(target);
}

FVector UACFFunctionLibrary::GetPointAtDirectionAndDistanceFromActor(const AActor* targetActor, const FVector& direction, float distance, bool bShowDebug /*= false*/)
{
    if (!targetActor) {
        return FVector();
    }
    const FVector actorLoc = targetActor->GetActorLocation();
    FVector normalizedDir = direction;

    normalizedDir.Normalize();
    const FVector additivePos = (normalizedDir * distance);
    FVector targetPos = actorLoc + additivePos;
    targetPos.Z = targetActor->GetActorLocation().Z;

    if (bShowDebug) {
        UKismetSystemLibrary::DrawDebugSphere(targetActor, targetPos, 100.f, 12, FLinearColor::Yellow, 1.f, 1.f);
    }

    return targetPos;
}

float UACFFunctionLibrary::CalculateDistanceBetweenCharactersExtents(const ACharacter* characterA, const ACharacter* characterB)
{
    if (characterA && characterB) {
        const FBox aBox = characterA->GetMesh()->Bounds.GetBox();
        const FBox bBox = characterB->GetMesh()->Bounds.GetBox();

        const float dist = characterA->GetDistanceTo(characterB);
        return dist - aBox.GetExtent().X - bBox.GetExtent().X;
    }
    return -1.f;
}

float UACFFunctionLibrary::GetCharacterExtent(const ACharacter* characterA)
{
    if (characterA) {
        const FBox aBox = characterA->GetMesh()->Bounds.GetBox();
        return aBox.GetExtent().X;
    }
    return -1.f;
}

float UACFFunctionLibrary::GetCharacterDistantToPointConsideringExtent(const ACharacter* characterA, const FVector& point)
{
    if (characterA) {
        const FBox aBox = characterA->GetMesh()->Bounds.GetBox();

        const float dist = FVector::Dist(characterA->GetActorLocation(), point);
        return dist - aBox.GetExtent().X;
    }
    return -1.f;
}

float UACFFunctionLibrary::CalculateAngleBetweenVectors(const FVector& vectorA, const FVector& vectorB)
{
    return FMath::RadiansToDegrees(acosf(FVector::DotProduct(vectorA, vectorB)));
}

class AACFHUD* UACFFunctionLibrary::GetACFHUD(const UObject* WorldContextObject)
{
    APlayerController* playerController = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
    if (playerController) {
        return Cast<AACFHUD>(playerController->GetHUD());
    }
    return nullptr;
}

class AACFPlayerController* UACFFunctionLibrary::GetLocalACFPlayerController(const UObject* WorldContextObject)
{
    return Cast<AACFPlayerController>(UGameplayStatics::GetPlayerController(WorldContextObject, 0));
}

class AACFGameMode* UACFFunctionLibrary::GetACFGameMode(const UObject* WorldContextObject)
{
    return Cast<AACFGameMode>(UGameplayStatics::GetGameMode(WorldContextObject));
}

class AACFGameState* UACFFunctionLibrary::GetACFGameState(const UObject* WorldContextObject)
{
    return Cast<AACFGameState>(UGameplayStatics::GetGameState(WorldContextObject));
}

class AACFCharacter* UACFFunctionLibrary::GetLocalACFPlayerCharacter(const UObject* WorldContextObject)
{
    return Cast<AACFCharacter>(UGameplayStatics::GetPlayerCharacter(WorldContextObject, 0));
}

UACFTeamManagerComponent* UACFFunctionLibrary::GetACFTeamManager(const UObject* WorldContextObject)
{
    AACFGameState* GameState = GetACFGameState(WorldContextObject);
    if (GameState) {
      return GameState->GetTeamManager();
    }
    UE_LOG(ACFLog, Error, TEXT("Missing Game State - UACFFunctionLibrary::GetACFTeamManager"));
    return nullptr;
}

bool UACFFunctionLibrary::ShouldExecuteAction(const FActionChances& action, const AACFCharacter* characterOwner)
{
    return characterOwner && characterOwner->GetActionsComponent() && characterOwner->GetActionsComponent()->CanExecuteAbility(action.ActionTag) && ((uint8)characterOwner->GetRelativeTargetDirection(characterOwner->GetTarget()) == (uint8)action.AllowedFromDirection || action.AllowedFromDirection == EActionDirection::EveryDirection);
}

bool UACFFunctionLibrary::GetCharacterAttributes(const TSubclassOf<class AACFCharacter>& characterClass, FAttributesSet& outData, bool bInitialize)
{

    UACFLegacyStatisticsComponent* statComp = Cast<UACFLegacyStatisticsComponent>(UACFFunctionLibrary::GetCharacterStatisticComp(characterClass, bInitialize));
    if (statComp) {

        outData = statComp->GetCurrentAttributeSet();
        return true;
    }

    return false;
}

UARSStatisticsComponent* UACFFunctionLibrary::GetCharacterStatisticComp(const TSubclassOf<class AACFCharacter>& characterClass, bool bInitialize /*= true*/)
{
    AACFCharacter* charInstance = GetCharacterDefaults(characterClass);
    if (charInstance) {
        UARSStatisticsComponent* statComp = charInstance->GetStatisticsComponent();
        if (statComp) {
            statComp->InitializeAttributeSet();
            if (bInitialize) {
                UACFEquipmentComponent* EquipmentComp = charInstance->GetEquipmentComponent();
                if (EquipmentComp) {
                    EquipmentComp->SetMainMesh(charInstance->GetMainMesh(), false);
                    EquipmentComp->InitializeStartingItems();
                }
            }

            return statComp;
        }
    }
    return nullptr;
}

AACFCharacter* UACFFunctionLibrary::GetCharacterDefaults(const TSubclassOf<class AACFCharacter>& characterClass)
{
    if (characterClass) {
        return Cast<AACFCharacter>(characterClass.GetDefaultObject());
    }
    return nullptr;
}

bool UACFFunctionLibrary::GetCharacterStartingItems(const TSubclassOf<class AACFCharacter>& characterClass, TArray<FStartingItem>& outItems)
{
    AACFCharacter* charInstance = GetCharacterDefaults(characterClass);
    if (charInstance) {
        UACFEquipmentComponent* EquipmentComp = charInstance->GetEquipmentComponent();
        if (EquipmentComp) {
            outItems = EquipmentComp->GetStartingItems();
            return true;
        }
    }
    return false;
}

bool UACFFunctionLibrary::GetCharacterName(const TSubclassOf<class AACFCharacter>& characterClass, FText& outName)
{
    AACFCharacter* charInstance = GetCharacterDefaults(characterClass);
    if (charInstance) {
        outName = charInstance->GetCharacterName();
        return true;
    }
    return false;
}

AActor* UACFFunctionLibrary::FindNearestActorOfClass(const UObject* WorldContextObject, TSubclassOf<class AActor> actorToFind, AActor* origin)
{
    TArray<AActor*> outActors;
    UGameplayStatics::GetAllActorsOfClass(WorldContextObject, actorToFind, outActors);
    TArray<AActor*> finalActors;
    for (AActor* actor : outActors) {
        if (actor->IsA(actorToFind)) {
            finalActors.Add(actor);
        }
    }

    float minDistance = BIG_NUMBER;
    AActor* bestActor = nullptr;
    for (AActor* actor : finalActors) {
        const float bestDistance = actor->GetDistanceTo(origin);
        if (bestDistance < minDistance) {
            bestActor = actor;
            minDistance = bestDistance;
        }
    }

    return bestActor;
}

int32 UACFFunctionLibrary::ExtractIndexWithProbability(const TArray<float>& weights)
{
    float sumWeight = 0;

    for (const auto& weight : weights) {
        sumWeight += weight;
    }

    float choosen = FMath::FRandRange(0.f, sumWeight);
    float currentSum = 0.f;

    for (int32 index = 0; index < weights.Num(); ++index) {
        currentSum += weights[index];
        if (choosen < currentSum) {
            return index;
        }
    }
    return -1;
}

bool UACFFunctionLibrary::IsLookingRightRelativeToPawn(const APawn* Pawn)
{
    if (!Pawn) {
        return false;
    }

    AController* Controller = Pawn->GetController();
    if (!Controller) {
        return false;
    }

    FVector ViewDirection = Controller->GetControlRotation().Vector();
    FVector RightDirection = Pawn->GetActorRightVector();

    // Project to horizontal plane
    ViewDirection.Z = 0.f;
    RightDirection.Z = 0.f;

    ViewDirection.Normalize();
    RightDirection.Normalize();

    float Dot = FVector::DotProduct(ViewDirection, RightDirection);
    return Dot > 0.f;
}

bool UACFFunctionLibrary::IsVelocityTowardActor(const UMovementComponent* MovementComp, const AActor* TargetActor, float ToleranceDegrees, float& OutAlignment)
{
    OutAlignment = 0.f;

    if (!MovementComp || !TargetActor) {
        return false;
    }

    const AActor* Owner = MovementComp->GetOwner();
    if (!Owner) {
        return false;
    }

    const FVector Velocity = MovementComp->Velocity;
    if (Velocity.IsNearlyZero()) {
        return false;
    }

    const FVector ToTarget = TargetActor->GetActorLocation() - Owner->GetActorLocation();
    if (ToTarget.IsNearlyZero()) {
        return false;
    }

    const float DotProduct = FVector::DotProduct(Velocity.GetUnsafeNormal(), ToTarget.GetUnsafeNormal());
    OutAlignment = FMath::Max(0.f, DotProduct);

    const float CosThreshold = FMath::Cos(FMath::DegreesToRadians(FMath::Clamp(ToleranceDegrees, 0.f, 180.f)));
    return DotProduct >= CosThreshold;
}

bool UACFFunctionLibrary::IsShippingBuild()
{
#if UE_BUILD_SHIPPING
    return true;
#else
    return false;
#endif
}

bool UACFFunctionLibrary::IsEditor()
{
#if UE_EDITOR
    return true;
#else
    return false;
#endif
}

bool UACFFunctionLibrary::IsDemoVersion()
{
	const UACFDeveloperSettings* Settings = GetDefault<UACFDeveloperSettings>();
	return Settings ? Settings->bIsDemoVersion : false;
}

FText UACFFunctionLibrary::GetInteractableNameFromActor(AActor* Actor)
{
	if (!IsValid(Actor))
	{
		return FText::GetEmpty();
	}

	if (UACFInteractableComponent* Comp = Actor->FindComponentByClass<UACFInteractableComponent>())
	{
		return Comp->GetInteractableName();
	}

	if (Actor->GetClass()->ImplementsInterface(UACFInteractableInterface::StaticClass()))
	{
		return IACFInteractableInterface::Execute_GetInteractableName(Actor);
	}

	return FText::GetEmpty();
}

TArray<UACMCollisionManagerComponent*> UACFFunctionLibrary::GetCollisionManagersFromActor(const AActor* Owner, EDamageActivationType DamageType)
{
	TArray<UACMCollisionManagerComponent*> OutComponents;
	if (!Owner)
	{
		return OutComponents;
	}

	switch (DamageType)
	{
	case EDamageActivationType::EPhysical:
		if (UACMCollisionManagerComponent* Comp = Owner->FindComponentByClass<UACMCollisionManagerComponent>())
		{
			OutComponents.Add(Comp);
		}
		break;
	case EDamageActivationType::ERight:
		if (UACFEquipmentComponent* Equip = Owner->FindComponentByClass<UACFEquipmentComponent>())
		{
			if (AActor* Weapon = Equip->GetCurrentMainWeapon())
			{
				if (UACMCollisionManagerComponent* Comp = Weapon->FindComponentByClass<UACMCollisionManagerComponent>())
				{
					OutComponents.Add(Comp);
				}
			}
		}
		break;
	case EDamageActivationType::ELeft:
		if (UACFEquipmentComponent* Equip = Owner->FindComponentByClass<UACFEquipmentComponent>())
		{
			if (AActor* Weapon = Equip->GetCurrentOffhandWeapon())
			{
				if (UACMCollisionManagerComponent* Comp = Weapon->FindComponentByClass<UACMCollisionManagerComponent>())
				{
					OutComponents.Add(Comp);
				}
			}
		}
		break;
	case EDamageActivationType::EBoth:
		if (UACFEquipmentComponent* Equip = Owner->FindComponentByClass<UACFEquipmentComponent>())
		{
			if (AActor* Main = Equip->GetCurrentMainWeapon())
			{
				if (UACMCollisionManagerComponent* Comp = Main->FindComponentByClass<UACMCollisionManagerComponent>())
				{
					OutComponents.Add(Comp);
				}
			}
			if (AActor* Off = Equip->GetCurrentOffhandWeapon())
			{
				if (UACMCollisionManagerComponent* Comp = Off->FindComponentByClass<UACMCollisionManagerComponent>())
				{
					OutComponents.Add(Comp);
				}
			}
		}
		break;
	default:
		break;
	}
	return OutComponents;
}

// ========== Chooser Utilities Implementation ==========

bool UACFFunctionLibrary::BuildMontageWeightMapFromChooser(
    UChooserTable* ChooserTable,
    int32 FloatOutputColumnIndex,
    TMap<UAnimMontage*, float>& OutMontageWeightMap)
{
    if (!ChooserTable)
    {
        UE_LOG(LogTemp, Warning, TEXT("BuildMontageWeightMapFromChooser: ChooserTable is null"));
        return false;
    }

    TMap<UObject*, float> AssetWeightMap;
    RecursivelyExtractAssetWeights(ChooserTable, FloatOutputColumnIndex, AssetWeightMap);

    // Filter only AnimMontages
    OutMontageWeightMap.Empty();
    for (const auto& Pair : AssetWeightMap)
    {
        if (UAnimMontage* Montage = Cast<UAnimMontage>(Pair.Key))
        {
            OutMontageWeightMap.Add(Montage, Pair.Value);
        }
    }

    return OutMontageWeightMap.Num() > 0;
}

bool UACFFunctionLibrary::BuildAssetWeightMapFromChooser(
    UChooserTable* ChooserTable,
    int32 FloatOutputColumnIndex,
    TMap<UObject*, float>& OutAssetWeightMap)
{
    if (!ChooserTable)
    {
        UE_LOG(LogTemp, Warning, TEXT("BuildAssetWeightMapFromChooser: ChooserTable is null"));
        return false;
    }

    OutAssetWeightMap.Empty();
    RecursivelyExtractAssetWeights(ChooserTable, FloatOutputColumnIndex, OutAssetWeightMap);

    return OutAssetWeightMap.Num() > 0;
}

void UACFFunctionLibrary::RecursivelyExtractAssetWeights(
    const UChooserTable* Chooser,
    int32 FloatOutputColumnIndex,
    TMap<UObject*, float>& OutMap)
{
    if (!Chooser)
    {
        return;
    }

    // Get the results array (handling both cooked and editor data)
    const TArray<FInstancedStruct>* ResultsArray = &Chooser->CookedResults;

#if WITH_EDITORONLY_DATA
    if (!Chooser->IsCookedData())
    {
        ResultsArray = &Chooser->ResultsStructs;
    }
#endif

    // Iterate through all rows
    const int32 NumRows = ResultsArray->Num();
    for (int32 RowIndex = 0; RowIndex < NumRows; ++RowIndex)
    {
        // Skip disabled rows
        if (Chooser->IsRowDisabled(RowIndex))
        {
            continue;
        }

        const FInstancedStruct& ResultStruct = (*ResultsArray)[RowIndex];
        if (!ResultStruct.IsValid())
        {
            continue;
        }

        const FObjectChooserBase* ChooserBase = ResultStruct.GetPtr<FObjectChooserBase>();
        if (!ChooserBase)
        {
            continue;
        }

        // Check if this is an asset chooser
        if (const FAssetChooser* AssetChooser = ResultStruct.GetPtr<FAssetChooser>())
        {
            if (UObject* Asset = AssetChooser->Asset)
            {
                // Extract the float value from the specified output column
                float Weight = GetFloatValueFromOutputColumn(Chooser, FloatOutputColumnIndex, RowIndex);

                // Add or update the map entry
                OutMap.Add(Asset, Weight);

                UE_LOG(LogTemp, Verbose, TEXT("ChooserUtility: Found asset %s with weight %.2f at row %d"),
                    *Asset->GetName(), Weight, RowIndex);
            }
        }
        // Check if this is a soft asset chooser
        else if (const FSoftAssetChooser* SoftAssetChooser = ResultStruct.GetPtr<FSoftAssetChooser>())
        {
            if (!SoftAssetChooser->Asset.IsNull())
            {
                // Try to load synchronously (or just get if already loaded)
                if (UObject* Asset = SoftAssetChooser->Asset.LoadSynchronous())
                {
                    float Weight = GetFloatValueFromOutputColumn(Chooser, FloatOutputColumnIndex, RowIndex);
                    OutMap.Add(Asset, Weight);

                    UE_LOG(LogTemp, Verbose, TEXT("ChooserUtility: Found soft asset %s with weight %.2f at row %d"),
                        *Asset->GetName(), Weight, RowIndex);
                }
            }
        }
        // Check if this is a nested chooser
        else if (const FNestedChooser* NestedChooser = ResultStruct.GetPtr<FNestedChooser>())
        {
            if (NestedChooser->Chooser)
            {
                UE_LOG(LogTemp, Verbose, TEXT("ChooserUtility: Recursing into nested chooser %s at row %d"),
                    *NestedChooser->Chooser->GetName(), RowIndex);

                // Recursively process the nested chooser
                RecursivelyExtractAssetWeights(NestedChooser->Chooser, FloatOutputColumnIndex, OutMap);
            }
        }
        // Check if this is an evaluate chooser (reference to another chooser asset)
        else if (const FEvaluateChooser* EvaluateChooser = ResultStruct.GetPtr<FEvaluateChooser>())
        {
            if (EvaluateChooser->Chooser)
            {
                UE_LOG(LogTemp, Verbose, TEXT("ChooserUtility: Recursing into evaluated chooser %s at row %d"),
                    *EvaluateChooser->Chooser->GetName(), RowIndex);

                // Recursively process the referenced chooser
                RecursivelyExtractAssetWeights(EvaluateChooser->Chooser, FloatOutputColumnIndex, OutMap);
            }
        }
    }

    // Also check the fallback result
    if (Chooser->FallbackResult.IsValid())
    {
        const FObjectChooserBase* FallbackBase = Chooser->FallbackResult.GetPtr<FObjectChooserBase>();

        if (const FAssetChooser* AssetChooser = Chooser->FallbackResult.GetPtr<FAssetChooser>())
        {
            if (UObject* Asset = AssetChooser->Asset)
            {
                // For fallback, use the fallback value from the column (special index -2)
                float Weight = GetFloatValueFromOutputColumn(Chooser, FloatOutputColumnIndex, ChooserColumn_SpecialIndex_Fallback);
                OutMap.Add(Asset, Weight);

                UE_LOG(LogTemp, Verbose, TEXT("ChooserUtility: Found fallback asset %s with weight %.2f"),
                    *Asset->GetName(), Weight);
            }
        }
        else if (const FNestedChooser* NestedChooser = Chooser->FallbackResult.GetPtr<FNestedChooser>())
        {
            if (NestedChooser->Chooser)
            {
                RecursivelyExtractAssetWeights(NestedChooser->Chooser, FloatOutputColumnIndex, OutMap);
            }
        }
        else if (const FEvaluateChooser* EvaluateChooser = Chooser->FallbackResult.GetPtr<FEvaluateChooser>())
        {
            if (EvaluateChooser->Chooser)
            {
                RecursivelyExtractAssetWeights(EvaluateChooser->Chooser, FloatOutputColumnIndex, OutMap);
            }
        }
    }
}

float UACFFunctionLibrary::GetFloatValueFromOutputColumn(
    const UChooserTable* Chooser,
    int32 ColumnIndex,
    int32 RowIndex)
{
    if (!Chooser || ColumnIndex < 0 || ColumnIndex >= Chooser->ColumnsStructs.Num())
    {
        return 0.0f;
    }

    const FInstancedStruct& ColumnStruct = Chooser->ColumnsStructs[ColumnIndex];
    if (!ColumnStruct.IsValid())
    {
        return 0.0f;
    }

    // Try to cast to FOutputFloatColumn (output column that stores values per row)
    if (const FOutputFloatColumn* OutputFloatColumn = ColumnStruct.GetPtr<FOutputFloatColumn>())
    {
        // Use the helper method that handles both regular rows and fallback
        return OutputFloatColumn->GetValueForIndex(RowIndex);
    }

    UE_LOG(LogTemp, Warning, TEXT("GetFloatValueFromOutputColumn: Column %d is not an OutputFloatColumn"), ColumnIndex);
    return 0.0f;
}
