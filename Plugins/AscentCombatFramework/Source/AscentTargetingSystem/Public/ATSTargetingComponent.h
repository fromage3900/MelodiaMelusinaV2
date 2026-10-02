// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ATSBaseTargetComponent.h"
#include "ATSTargetingFilter.h"
#include "CCMTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <Components/SphereComponent.h>

#include "ATSTargetingComponent.generated.h"

class APlayerCameraManager;
class APawn;
class AActor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTargetingStateChanged, bool, bIsTargeting);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTargetChanged, const class AActor*, targetActor);

UENUM(BlueprintType)
enum class ETargetingType : uint8 {
    EDontLock = 0 UMETA(DisplayName = "Don't Lock Camera"),
    EMagneticLock UMETA(DisplayName = "Adjust Camera Lock with Magnetism"),
    EMagneticLockYawOnly UMETA(DisplayName = "Adjust Camera Yaw Lock On Target"),
};

UENUM(BlueprintType)
enum class ETargetingDirection : uint8 {
    ELeft = 0 UMETA(DisplayName = "Left"),
    ERight UMETA(DisplayName = "Right"),
    EUp UMETA(DisplayName = "Up"),
    EDown UMETA(DisplayName = "Down"),
};

UENUM(BlueprintType)
enum class ETargetSelectionType : uint8 {
    ENearestTarget = 0 UMETA(DisplayName = "Choose Lower Distance "),
    EForwardTarget = 1 UMETA(DisplayName = "Choose Lower Degrees From Forward"),
};

UCLASS(ClassGroup = (ATS), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTTARGETINGSYSTEM_API UATSTargetingComponent : public UATSBaseTargetComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UATSTargetingComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /*InputThrashold to start looking for targets with input*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ATS)
    float InputTrasholdForSearch = .7f;

    /*MaxDistance for target detection*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ATS)
    float MaxTargetingDistance = 1500;

    /*MaxAngular distance from OwnerActor for target detection*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ATS)
    float MaxAngularDistanceDegree = 60.f;

    /*Select if you prefer to choose the nearest target or
    the one that is closer to your forward vector*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ATS)
    ETargetSelectionType TargetSelectionType;

    /*Select your targeting type:
    Dont Lock = does not affect camera
    Magnetic Lock = smooth camera lock on that interpolates thought the target
    MagneticYawOnly = Affects only yaw for the camera*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ATS)
    ETargetingType TargetingType = ETargetingType::EMagneticLock;

    /*If your target type is Magnetic Lock,
    this will be the strength of the magnetism*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ATS)
    float LockMagnetism = 15.f;

    /*Limit on camera pitch to avoid gimbal lock*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ATS)
    float BottomPitchLimitDegree = -15.f;

    /*Limit on camera pitch to avoid gimbal lock*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ATS)
    float UpperPitchLimitDegree = 75.f;

    UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ATS)
    TArray<TEnumAsByte<EObjectTypeQuery>> ObjectsToQuery;

    /*Filters to avoid an acotr from being targeted*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Instanced, Category = ATS)
    TArray<class UATSTargetingFilter*> TargetFilters;

    /*If your target sight to the target is interruptet by something, stop targeting*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ATS)
    bool bStopTargetingIfOutOfSight = true;

public:
    // Called every frame
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintPure, Category = ATS)
    float GetLockMagnetism() const { return LockMagnetism; }

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetLockMagnetism(float val) { LockMagnetism = val; }

    UFUNCTION(BlueprintPure, Category = ATS)
    ETargetingType GetTargetingType() const { return TargetingType; }

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetTargetingType(ETargetingType val) { TargetingType = val; }

    UFUNCTION(BlueprintPure, Category = ATS)
    float GetMaxAngularDistanceDegree() const { return MaxAngularDistanceDegree; }

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetMaxAngularDistanceDegree(float val) { MaxAngularDistanceDegree = val; }

    UFUNCTION(BlueprintPure, Category = ATS)
    ETargetSelectionType GetTargetSelectionType() const { return TargetSelectionType; }

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetTargetSelectionType(ETargetSelectionType val) { TargetSelectionType = val; }

    UFUNCTION(BlueprintPure, Category = ATS)
    float GetMaxTargetingDistance() const { return MaxTargetingDistance; }

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetMaxTargetingDistance(float val) { MaxTargetingDistance = val; }
    /*Use this to trigger targeting mode*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    void TriggerTargeting(bool bActivate);

    /*Used to add Filter for potential targets at runtime*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    void AddFilter(TSubclassOf<UATSTargetingFilter> filter);

    /*Used to remove a Filter for potential targets at runtime*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    bool RemoveFilter(TSubclassOf<UATSTargetingFilter> filterClass);

    UFUNCTION(BlueprintCallable, Category = ATS)
    void AddObjectType(TEnumAsByte<EObjectTypeQuery> inTraceChannel);

    UFUNCTION(BlueprintCallable, Category = ATS)
    void RemoveObjectType(TEnumAsByte<EObjectTypeQuery> inTraceChannel);

    /*Use this to toggle targeting mode*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    void ToggleTargeting();

    /*Used to search for another target on Left/right*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    void RightSearchTargetWithInput(float InputValue);

    /*Used to search for another target  Up/Down*/
    UFUNCTION(BlueprintCallable, Category = ATS)
    void UpSearchTargetWithInput(float InputValue);

    /*Returns true if targeting mode is currently active*/
    UFUNCTION(BlueprintPure, Category = ATS)
    FORCEINLINE bool IsTargetingEnabled() const { return bIsTargeting; }

    virtual void SetCurrentTarget(AActor* target) override;

    UFUNCTION(BlueprintCallable, Category = ATS)
    void SetOwnerReferences();

    UPROPERTY(BlueprintAssignable, Category = ATS)
    FOnTargetingStateChanged OnTargetingStateChanged;

    UPROPERTY(BlueprintAssignable, Category = ATS)
    FOnTargetChanged OnTargetChanged;

private:
    ELockType GetLockTypeByTargetingType(ETargetingType targetType);

    void PopulatePotentialTargetsArray();

    void SwitchTargetByDirection(ETargetingDirection direction);

    UATSTargetPointComponent* GetNearestTargetPoint(TArray<UATSTargetPointComponent*> points);

    UFUNCTION()
    void HandlePawnChanged(class APawn* newPawn);

    UFUNCTION()
    void ActivateTargeting();

    UFUNCTION()
    TArray<AActor*> GetAllTargetsByDirection(ETargetingDirection direction);

    UFUNCTION()
    bool TrySwitchPointOnCurrentTarget(ETargetingDirection direction);

    UFUNCTION()
    class AActor* GetNearestTarget(TArray<AActor*>& actorFilter);

    UFUNCTION()
    bool IsValidTarget(AActor* target);

    bool IsInFrontOfOwner(AActor* target);

    UFUNCTION()
    void UpdateTargeting(float deltaTime);

    UFUNCTION()
    void UpdateCurrentTargetPoint(UATSTargetPointComponent* inCurrentTargetPoint);

    void CleanCamera();

    UFUNCTION()
    class UATSTargetPointComponent* GetBestTargetPointForTarget(AActor* target);

    UFUNCTION()
    bool IsRightOfCurrentTarget(FVector locationToCheck);

    UFUNCTION()
    bool IsUpOfCurrentTarget(FVector locationToCheck);

    FName currentCameraEvent = NAME_None;

    UPROPERTY()
    TArray<AActor*> availableTargets;

    TObjectPtr<APawn> ControlledPawn;

    bool bCanTarget = true;

    float Xvalue;
    float YValue;
    float deadband = .3f;

    UPROPERTY()
    bool bIsTargeting = false;

    TObjectPtr<APlayerCameraManager> cameraManger;
};
