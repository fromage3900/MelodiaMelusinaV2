#include "MelodiaOpeningStateComponent.h"

void UMelodiaResonanceBondComponent::SetBondState(const EMelodiaResonanceBondState NewState)
{
	if (BondState == NewState)
	{
		return;
	}

	BondState = NewState;
	OnBondStateChanged.Broadcast(BondState);
}

bool UMelodiaResonanceBondComponent::IsSongcraftEmpowered() const
{
	return BondState == EMelodiaResonanceBondState::Resonant;
}

void UMelodiaDissonanceComponent::SetDissonanceTier(const EMelodiaDissonanceTier NewTier, const float NewSongcraftScalar)
{
	Tier = NewTier;
	SongcraftScalar = FMath::Clamp(NewSongcraftScalar, 0.0f, 2.0f);
	OnTierChanged.Broadcast(Tier);
}
