#include "MelodiaTokenWalletSubsystem.h"

UMelodiaTokenWalletSubsystem::UMelodiaTokenWalletSubsystem()
{
}

UMelodiaTokenWalletSubsystem::~UMelodiaTokenWalletSubsystem()
{
}

FMelodiaWalletSnapshot UMelodiaTokenWalletSubsystem::GetSnapshot() const
{
    FMelodiaWalletSnapshot Snapshot;
    Snapshot.GoldenTokens = GoldenTokens;
    return Snapshot;
}

bool UMelodiaTokenWalletSubsystem::TrySpendGolden(int32 Count)
{
    if (GoldenTokens >= Count)
    {
        GoldenTokens -= Count;
        // Broadcast the change ( Blueprints can bind to OnGoldenChanged )
        return true;
    }
    return false;
}

void UMelodiaTokenWalletSubsystem::RefundGolden(int32 Count)
{
    GoldenTokens += Count;
}