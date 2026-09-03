#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/**
 * Melodia Token Wallet Subsystem — decision 020/029g.
 * Single source of truth for Melody Golden tokens; all gacha/shop plugins
 * must use this authority to avoid second-authority hazard.
 */
class MELODIATOKENWALLET_API UMelodiaTokenWalletSubsystem : public USubsystem
{
    GENERATED_BODY()
public:
    UMelodiaTokenWalletSubsystem();
    ~UMelodiaTokenWalletSubsystem() override;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Wallet state
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    /** Current count of Golden tokens the player owns. */
    UPROPERTY(BlueprintReadOnly, Category = "Melodia|TokenWallet")
    int32 GoldenTokens = 500; // Starting endowment

    /** Read-only snapshot of current wallet state. */
    UFUNCTION(BlueprintCallable, Category = "Melodia|TokenWallet")
    FMelodiaWalletSnapshot GetSnapshot() const;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Transactions
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    /** Attempt to spend GoldenTokens. Returns true on success, false if insufficient funds. */
    UFUNCTION(BlueprintCallable, Category = "Melodia|TokenWallet")
    bool TrySpendGolden(int32 Count);

    /** Refund previously spent GoldenTokens. */
    UFUNCTION(BlueprintCallable, Category = "Melodia|TokenWallet")
    void RefundGolden(int32 Count);

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Events
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    UDelegateHandle OnGoldenChanged;
};