// Test-only listener for the wallet's changed event.
//
// FMelodiaWalletChanged is a DYNAMIC multicast delegate, so it can only bind a UFUNCTION on a
// UObject — AddLambda does not compile against it. That constraint is deliberate on the
// delegate (Blueprints must be able to bind it), so the test side needs a real UObject rather
// than a weaker delegate type.
//
// Compiled only for automation builds; nothing in the shipping game references it.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "MelodiaTokenWalletSubsystem.h"
#include "MelodiaEconomyTestListener.generated.h"

/**
 * Counts OnWalletChanged broadcasts and keeps the most recent snapshot.
 *
 * The count is the interesting part: the wallet's contract is "exactly once per ACCEPTED
 * transaction, never on a rejection", and that is only testable by counting.
 */
UCLASS()
class UMelodiaEconomyTestListener : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY()
	int32 EventCount = 0;

	UPROPERTY()
	FMelodiaWalletSnapshot LastSnapshot;

	UFUNCTION()
	void HandleWalletChanged(const FMelodiaWalletSnapshot& Snapshot)
	{
		++EventCount;
		LastSnapshot = Snapshot;
	}

	void ListenTo(UMelodiaTokenWalletSubsystem* Wallet)
	{
		if (Wallet)
		{
			Wallet->OnWalletChanged.AddDynamic(this, &UMelodiaEconomyTestListener::HandleWalletChanged);
		}
	}
};
