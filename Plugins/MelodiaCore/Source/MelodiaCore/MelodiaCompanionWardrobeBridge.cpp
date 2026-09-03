#include "MelodiaCompanionWardrobeBridge.h"

namespace
{
	void SetCompanionWardrobeValidationError(FText* OutError, const TCHAR* Message)
	{
		if (OutError)
		{
			*OutError = FText::FromString(Message);
		}
	}
}

bool FMelodiaCompanionWardrobeProfile::IsValid(FText* OutError) const
{
	if (OutError)
	{
		*OutError = FText::GetEmpty();
	}

	if (ProfileId.IsNone())
	{
		SetCompanionWardrobeValidationError(OutError, TEXT("ProfileId must not be None."));
		return false;
	}

	if (PreferredCosmeticIds.IsEmpty())
	{
		SetCompanionWardrobeValidationError(OutError, TEXT("PreferredCosmeticIds must contain at least one candidate."));
		return false;
	}

	for (const FName CosmeticId : PreferredCosmeticIds)
	{
		if (CosmeticId.IsNone())
		{
			SetCompanionWardrobeValidationError(OutError, TEXT("PreferredCosmeticIds must not contain None."));
			return false;
		}
	}

	if (!bAllowPrototypeGrant)
	{
		// Prototype fields are ignored when the opt-in is false. This allows one
		// profile asset to carry an explicitly disabled prototype recipe without
		// accidentally making it executable.
		return true;
	}

	if (PrototypeGrantCosmeticId.IsNone() || PrototypeGrantId.IsNone())
	{
		SetCompanionWardrobeValidationError(
			OutError,
			TEXT("Prototype grants require both PrototypeGrantCosmeticId and PrototypeGrantId."));
		return false;
	}

	if (!PreferredCosmeticIds.Contains(PrototypeGrantCosmeticId))
	{
		SetCompanionWardrobeValidationError(
			OutError,
			TEXT("PrototypeGrantCosmeticId must be one of the preferred candidates."));
		return false;
	}

	return true;
}

UMelodiaCompanionWardrobeBridge::UMelodiaCompanionWardrobeBridge()
{
	PrimaryComponentTick.bCanEverTick = false;
}

bool UMelodiaCompanionWardrobeBridge::SetWardrobeProvider(UActorComponent* NewProvider)
{
	if (!NewProvider)
	{
		WardrobeProvider = nullptr;
		LastRequestResult = EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider;
		return false;
	}

	if (!NewProvider->GetClass()->ImplementsInterface(UMelodiaCompanionWardrobeInterface::StaticClass()))
	{
		WardrobeProvider = nullptr;
		LastRequestResult = EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider;
		return false;
	}

	WardrobeProvider = NewProvider;
	return true;
}

bool UMelodiaCompanionWardrobeBridge::HasWardrobeProvider() const
{
	return WardrobeProvider
		&& WardrobeProvider->GetClass()->ImplementsInterface(UMelodiaCompanionWardrobeInterface::StaticClass());
}

EMelodiaCompanionWardrobeRequestResult UMelodiaCompanionWardrobeBridge::RequestPresentation()
{
	return RequestPresentationWithProfile(PresentationProfile);
}

EMelodiaCompanionWardrobeRequestResult UMelodiaCompanionWardrobeBridge::RequestPresentationWithProfile(
	const FMelodiaCompanionWardrobeProfile& Profile)
{
	FText ValidationError;
	if (!Profile.IsValid(&ValidationError))
	{
		LastRequestResult = EMelodiaCompanionWardrobeRequestResult::RejectedInvalidProfile;
		return LastRequestResult;
	}

	if (!HasWardrobeProvider())
	{
		LastRequestResult = EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider;
		return LastRequestResult;
	}

	LastRequestResult = IMelodiaCompanionWardrobeInterface::Execute_RequestCompanionWardrobe(
		WardrobeProvider,
		Profile);
	return LastRequestResult;
}
