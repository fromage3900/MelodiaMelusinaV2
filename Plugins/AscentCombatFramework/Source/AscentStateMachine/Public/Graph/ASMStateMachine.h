// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AGSGraph.h"
#include "ASMStateMachine.generated.h"

/**
 * 
 */
UENUM()
enum class EFSMState : uint8
{
	/** Node is enabled. */
	Started,
	/** Node is disabled. */
	NotStarted,

};

UCLASS()
class ASCENTSTATEMACHINE_API UASMStateMachine : public UAGSGraph
{
	GENERATED_BODY()

private:

	EFSMState Enabled = EFSMState::NotStarted;

	UPROPERTY()
	class AActor* fsmOwner;

	UPROPERTY()
	class UASMStateNode* currentState;

	bool bPrintDebug = false;

protected:

	virtual bool ActivateNode(class UAGSGraphNode* node) override;

public:

	UASMStateMachine();

	void StartFSM(class AActor* inOwner, const bool bPrintDebugInfo = false);

	void Internal_Start();

	bool TriggerTransition(const FGameplayTag& transition);

	void StopFSM();

	FName GetCurrentStateName() const;
	class UASMBaseFSMState* GetCurrentState() const;
	
	bool IsActive() const {
		return Enabled == EFSMState::Started;
	}

	class AActor* GetFSMOwner() const {
		return fsmOwner;
	}

	void DispatchTick(float DeltaTime);

	UWorld* GetWorld() const override { return fsmOwner ? fsmOwner->GetWorld() : nullptr; }

};
