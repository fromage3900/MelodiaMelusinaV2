// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Commands/ACFBaseCommand.h"
#include "CoreMinimal.h"

#include "ACFFollowMeCommand.generated.h"

class USplineComponent;
class UACFSplineFollowerComponent;

/**
 * Simple command that triggers spline following using the SplineFollowerComponent
 */
UCLASS()
class AIFRAMEWORK_API UACFFollowMeCommand : public UACFBaseCommand {
    GENERATED_BODY()

public:
    UACFFollowMeCommand();

    /** Setup command parameters */
    UFUNCTION(BlueprintCallable, Category = "Follow Me Command")
    void SetupCommand(USplineComponent* InSpline, APawn* InTargetPawn);

    /** Override base command functions */
    virtual void ExecuteCommand_Implementation(class AACFAIController* controller);

    virtual void EndCommand_Implementation(class AACFAIController* controller);

protected:
    /** The spline to follow */
    UPROPERTY()
    TObjectPtr<USplineComponent> SplinePath;

    /** The pawn to wait for */
    UPROPERTY()
    TObjectPtr<APawn> TargetPawn;

    /** Reference to the spline follower component */
    UPROPERTY()
    TObjectPtr<UACFSplineFollowerComponent> SplineFollowerComponent;

private:
    /** Called when spline following is completed */
    UFUNCTION()
    void HandleSplineCompleted();

    /** Called when following is stopped for any reason */
    UFUNCTION()
    void HandleFollowingStopped();
};
