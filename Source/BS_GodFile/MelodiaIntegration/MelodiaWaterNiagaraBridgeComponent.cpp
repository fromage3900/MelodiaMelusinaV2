#include "MelodiaWaterNiagaraBridgeComponent.h"

#include "Engine/World.h"
#include "NiagaraComponent.h"
#include "NiagaraComponentPoolMethodEnum.h"
#include "NiagaraDataChannelAccessor.h"
#include "NiagaraDataChannelAsset.h"
#include "NiagaraDataChannelFunctionLibrary.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterProfile.h"
#include "UObject/ConstructorHelpers.h"

UMelodiaWaterNiagaraBridgeComponent::UMelodiaWaterNiagaraBridgeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> RippleFinder(
		TEXT("/Game/Melodia/VFX/NS_Melusina_Ripple.NS_Melusina_Ripple"));
	if (RippleFinder.Succeeded())
	{
		RippleSystem = RippleFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> SplashFinder(
		TEXT("/Game/Melodia/VFX/NS_Melusina_Splash.NS_Melusina_Splash"));
	if (SplashFinder.Succeeded())
	{
		SplashSystem = SplashFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UMelodiaWaterProfile> ProfileFinder(
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default"));
	if (ProfileFinder.Succeeded())
	{
		Profile = ProfileFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UMaterialParameterCollection> QuantumPaletteFinder(
		TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"));
	if (QuantumPaletteFinder.Succeeded())
	{
		QuantumPaletteMPC = QuantumPaletteFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> QuantumReactionFinder(
		TEXT("/Game/Melodia/VFX/NS_Melusina_ChaosDrift.NS_Melusina_ChaosDrift"));
	if (QuantumReactionFinder.Succeeded())
	{
		QuantumReactionSystem = QuantumReactionFinder.Object;
	}
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> QuantumEntropyFinder(
		TEXT("/Game/Melodia/VFX/NS_Melusina_EntropyDust.NS_Melusina_EntropyDust"));
	if (QuantumEntropyFinder.Succeeded())
	{
		QuantumEntropySystem = QuantumEntropyFinder.Object;
	}
}

void UMelodiaWaterNiagaraBridgeComponent::BeginPlay()
{
	Super::BeginPlay();

	if (Profile)
	{
		if (!ContactDataChannel)
		{
			ContactDataChannel = Profile->ContactDataChannel.LoadSynchronous();
		}
		if (!ContactSystem)
		{
			ContactSystem = Profile->ContactSystem.LoadSynchronous();
		}
		if (!RippleSystem)
		{
			RippleSystem = Profile->RippleSystem.LoadSynchronous();
		}
		if (!SplashSystem)
		{
			SplashSystem = Profile->SplashSystem.LoadSynchronous();
		}
		if (Profile->MaxContactsPerSecond > 0)
		{
			MaxDataChannelWritesPerSecond = Profile->MaxContactsPerSecond;
		}
		if (!QuantumReactionSystem)
		{
			QuantumReactionSystem = Profile->QuantumReactionSystem.LoadSynchronous();
		}
		if (!QuantumEntropySystem)
		{
			QuantumEntropySystem = Profile->QuantumEntropySystem.LoadSynchronous();
		}
		bUseQuantumReactionVFX = bUseQuantumReactionVFX && Profile->bUseQuantumReactionVFX;
		MaxQuantumReactionEventsPerSecond = FMath::Max(0, Profile->MaxQuantumReactionEventsPerSecond);
	}

	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
		if (WaterSubsystem)
		{
			WaterSubsystem->OnContactEvent.AddUniqueDynamic(this, &ThisClass::HandleWaterContact);
		}
	}
}

void UMelodiaWaterNiagaraBridgeComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	DataChannelContactsConsumedThisFrame = 0;
	if (bConsumeContactDataChannel && IsValid(ContactDataChannel))
	{
		ConsumeContactDataChannel();
	}
}

void UMelodiaWaterNiagaraBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (WaterSubsystem)
	{
		WaterSubsystem->OnContactEvent.RemoveDynamic(this, &ThisClass::HandleWaterContact);
		WaterSubsystem = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterNiagaraBridgeComponent::HandleWaterContact(FMelodiaWaterContactEvent Event)
{
	if (bOnlySpawnForOwner && Event.SourceActor != GetOwner())
	{
		return;
	}

	const bool bHasDataChannel = bWriteContactDataChannel && IsValid(ContactDataChannel);
	const bool bPublishedToDataChannel = bHasDataChannel && CanWriteContactToDataChannel(Event)
		? WriteContactToDataChannel(Event)
		: false;
	if (!bPublishedToDataChannel
		&& (bSpawnDirectContactEffects || (bFallbackToDirectWhenDataChannelUnavailable && !bHasDataChannel)))
	{
		SpawnDirectContactVFX(Event);
	}

	SpawnQuantumReactionVFX(Event);
}

void UMelodiaWaterNiagaraBridgeComponent::SpawnDirectContactVFX(const FMelodiaWaterContactEvent& Event)
{

	UNiagaraSystem* System = ResolveSystemForEvent(Event.EventType);
	if (!IsValid(System) || Event.Intensity < MinimumIntensity || !ShouldSpawnForEvent(Event.EventType))
	{
		return;
	}

	const FVector Normal = Event.Sample.SurfaceNormal.IsNearlyZero()
		? FVector::UpVector
		: Event.Sample.SurfaceNormal.GetSafeNormal();
	UNiagaraComponent* NiagaraComponent = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
		this,
		System,
		Event.ContactLocation,
		Normal.Rotation(),
		FVector::OneVector,
		true,
		true,
		ENCPoolMethod::AutoRelease,
		true);
	if (!NiagaraComponent)
	{
		return;
	}

	NiagaraComponent->SetVariableFloat(RadiusParameter, Event.Radius);
	NiagaraComponent->SetVariableFloat(IntensityParameter, Event.Intensity);
	NiagaraComponent->SetVariableFloat(ImmersionParameter, Event.Sample.Immersion);
	NiagaraComponent->SetVariableVec3(VelocityParameter, Event.ImpactVelocity);
}

void UMelodiaWaterNiagaraBridgeComponent::ConsumeContactDataChannel()
{
	if (!GetWorld() || !IsValid(ContactDataChannel) || LastConsumedDataChannelFrame == GFrameCounter)
	{
		return;
	}
	LastConsumedDataChannelFrame = GFrameCounter;

	const FNiagaraDataChannelSearchParameters SearchParameters(
		GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector);
	UNiagaraDataChannelReader* Reader = UNiagaraDataChannelLibrary::ReadFromNiagaraDataChannel(
		this,
		ContactDataChannel,
		SearchParameters,
		true);
	if (!Reader)
	{
		return;
	}

	const int32 ReadCount = FMath::Min(Reader->Num(), FMath::Max(1, MaxDataChannelReadsPerTick));
	for (int32 Index = 0; Index < ReadCount; ++Index)
	{
		bool bPositionValid = false;
		bool bVelocityValid = false;
		bool bRadiusValid = false;
		bool bIntensityValid = false;
		bool bImmersionValid = false;
		bool bWaterBodyValid = false;
		bool bEventTypeValid = false;
		bool bRandomSeedValid = false;

		FMelodiaWaterContactEvent Event;
		Event.ContactLocation = Reader->ReadPosition(DataChannelPosition, Index, bPositionValid);
		Event.ImpactVelocity = Reader->ReadVector(DataChannelVelocity, Index, bVelocityValid);
		Event.Radius = static_cast<float>(Reader->ReadFloat(DataChannelRadius, Index, bRadiusValid));
		Event.Intensity = static_cast<float>(Reader->ReadFloat(DataChannelIntensity, Index, bIntensityValid));
		Event.Sample.Immersion = static_cast<float>(Reader->ReadFloat(DataChannelImmersion, Index, bImmersionValid));
		Event.Sample.WaterBodyIndex = Reader->ReadInt(DataChannelWaterBodyIndex, Index, bWaterBodyValid);
		const int32 EventTypeValue = Reader->ReadInt(DataChannelEventType, Index, bEventTypeValid);
		Event.RandomSeed = Reader->ReadInt(DataChannelRandomSeed, Index, bRandomSeedValid);

		if (!bPositionValid || !bVelocityValid || !bRadiusValid || !bIntensityValid
			|| !bImmersionValid || !bWaterBodyValid || !bEventTypeValid || !bRandomSeedValid)
		{
			continue;
		}

		Event.EventType = static_cast<EMelodiaWaterContactType>(FMath::Clamp(
			EventTypeValue,
			static_cast<int32>(EMelodiaWaterContactType::ProximityEntered),
			static_cast<int32>(EMelodiaWaterContactType::WaterImpact)));
		Event.Sample.bValid = true;
		Event.Sample.bSurfaceValid = true;
		Event.SourceActor = GetOwner();

		if (Event.Intensity >= MinimumIntensity && ShouldSpawnForEvent(Event.EventType))
		{
			SpawnDirectContactVFX(Event);
			++DataChannelContactsConsumedThisFrame;
		}
	}

	// No Reader->Cleanup() here: UNiagaraDataChannelReader::Cleanup is declared but
	// not NIAGARA_API-exported, so calling it from this module fails to link
	// (LNK2019). It is an internal lifecycle method -- the reader is a UObject and
	// is collected normally, so there is nothing to release by hand.
}

void UMelodiaWaterNiagaraBridgeComponent::ReadQuantumPresentation(
	float& OutChoice,
	float& OutSeed,
	float& OutBackend,
	float& OutPulse,
	FLinearColor& OutColor) const
{
	OutChoice = 0.0f;
	OutSeed = 0.0f;
	OutBackend = 0.0f;
	OutPulse = 0.0f;
	OutColor = FLinearColor::White;

	if (!GetWorld() || !QuantumPaletteMPC)
	{
		return;
	}

	UMaterialParameterCollectionInstance* Instance = GetWorld()->GetParameterCollectionInstance(QuantumPaletteMPC);
	if (!Instance)
	{
		return;
	}

	Instance->GetScalarParameterValue(FName("QuantumChoice"), OutChoice);
	Instance->GetScalarParameterValue(FName("QuantumSeed"), OutSeed);
	Instance->GetScalarParameterValue(FName("QuantumBackend"), OutBackend);
	Instance->GetScalarParameterValue(FName("QuantumPulse"), OutPulse);
	Instance->GetVectorParameterValue(FName("QuantumReactionColor"), OutColor);
}

bool UMelodiaWaterNiagaraBridgeComponent::CanSpawnQuantumReaction(const FMelodiaWaterContactEvent& Event)
{
	if (!bUseQuantumReactionVFX || (!QuantumReactionSystem && !QuantumEntropySystem))
	{
		return false;
	}

	switch (Event.EventType)
	{
	case EMelodiaWaterContactType::SurfaceEntry:
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::DiveStarted:
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::WaterImpact:
		break;
	default:
		return false;
	}

	float Choice = 0.0f;
	float Seed = 0.0f;
	float Backend = 0.0f;
	ReadQuantumPresentation(Choice, Seed, Backend, LastQuantumPulse, LastQuantumReactionColor);
	if (LastQuantumPulse < QuantumPulseThreshold)
	{
		return false;
	}

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	if (QuantumWindowStart <= 0.0f || Now - QuantumWindowStart >= 1.0f)
	{
		QuantumWindowStart = Now;
		QuantumReactionsThisWindow = 0;
	}

	return QuantumReactionsThisWindow < MaxQuantumReactionEventsPerSecond;
}

void UMelodiaWaterNiagaraBridgeComponent::SpawnQuantumReactionVFX(const FMelodiaWaterContactEvent& Event)
{
	if (!CanSpawnQuantumReaction(Event) || !GetWorld())
	{
		return;
	}

	float Choice = 0.0f;
	float Seed = 0.0f;
	float Backend = 0.0f;
	float Pulse = LastQuantumPulse;
	FLinearColor Color = LastQuantumReactionColor;
	ReadQuantumPresentation(Choice, Seed, Backend, Pulse, Color);

	UNiagaraSystem* System = QuantumReactionSystem;
	if ((Event.EventType == EMelodiaWaterContactType::SurfaceEntry
		|| Event.EventType == EMelodiaWaterContactType::WaterImpact
		|| Event.EventType == EMelodiaWaterContactType::DiveStarted)
		&& QuantumEntropySystem)
	{
		System = QuantumEntropySystem;
	}
	if (!System)
	{
		return;
	}

	const FVector Normal = Event.Sample.SurfaceNormal.IsNearlyZero()
		? FVector::UpVector
		: Event.Sample.SurfaceNormal.GetSafeNormal();
	UNiagaraComponent* NiagaraComponent = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
		this,
		System,
		Event.ContactLocation,
		Normal.Rotation(),
		FVector::OneVector,
		true,
		true,
		ENCPoolMethod::AutoRelease,
		true);
	if (!NiagaraComponent)
	{
		return;
	}

	NiagaraComponent->SetVariableLinearColor(QuantumReactionColorParameter, Color);
	NiagaraComponent->SetVariableFloat(QuantumPulseParameter, Pulse);
	NiagaraComponent->SetVariableFloat(QuantumChoiceParameter, Choice);
	NiagaraComponent->SetVariableFloat(QuantumSeedParameter, Seed);
	NiagaraComponent->SetVariableFloat(QuantumBackendParameter, Backend);
	NiagaraComponent->SetVariableFloat(FName("User.QuantumChoiceInv"), 1.0f - Choice);
	++QuantumReactionsThisWindow;
	LastQuantumPulse = Pulse;
	LastQuantumReactionColor = Color;
}

bool UMelodiaWaterNiagaraBridgeComponent::CanWriteContactToDataChannel(const FMelodiaWaterContactEvent& Event)
{
	if (!bWriteContactDataChannel || !IsValid(ContactDataChannel) || Event.Intensity <= 0.0f)
	{
		return false;
	}

	const float CurrentTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	if (CurrentTime - DataChannelWindowStart >= 1.0f)
	{
		DataChannelWindowStart = CurrentTime;
		DataChannelWritesThisWindow = 0;
	}

	if (DataChannelWritesThisWindow >= FMath::Max(1, MaxDataChannelWritesPerSecond))
	{
		return false;
	}

	++DataChannelWritesThisWindow;
	return true;
}

bool UMelodiaWaterNiagaraBridgeComponent::WriteContactToDataChannel(const FMelodiaWaterContactEvent& Event)
{
	if (!GetWorld() || !IsValid(ContactDataChannel))
	{
		return false;
	}

	const FNiagaraDataChannelSearchParameters SearchParameters(Event.ContactLocation);
	UNiagaraDataChannelWriter* Writer = UNiagaraDataChannelLibrary::WriteToNiagaraDataChannel(
		this,
		ContactDataChannel,
		SearchParameters,
		1,
		true,
		true,
		true,
		TEXT("MelodiaWaterContact"));
	if (!Writer)
	{
		return false;
	}

	Writer->WritePosition(DataChannelPosition, 0, Event.ContactLocation);
	Writer->WriteVector(DataChannelVelocity, 0, Event.ImpactVelocity);
	Writer->WriteFloat(DataChannelRadius, 0, Event.Radius);
	Writer->WriteFloat(DataChannelIntensity, 0, Event.Intensity);
	Writer->WriteFloat(DataChannelImmersion, 0, Event.Sample.Immersion);
	Writer->WriteInt(DataChannelWaterBodyIndex, 0, Event.Sample.WaterBodyIndex);
	Writer->WriteInt(DataChannelEventType, 0, static_cast<int32>(Event.EventType));
	Writer->WriteInt(DataChannelRandomSeed, 0, Event.RandomSeed);
	return true;
}

UNiagaraSystem* UMelodiaWaterNiagaraBridgeComponent::ResolveSystemForEvent(EMelodiaWaterContactType EventType) const
{
	if (ContactSystem)
	{
		return ContactSystem;
	}

	switch (EventType)
	{
	case EMelodiaWaterContactType::SurfaceEntry:
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::WaterImpact:
		return SplashSystem ? SplashSystem : RippleSystem;
	case EMelodiaWaterContactType::DiveStarted:
		return UnderwaterSystem ? UnderwaterSystem : RippleSystem;
	default:
		return RippleSystem;
	}
}

bool UMelodiaWaterNiagaraBridgeComponent::ShouldSpawnForEvent(EMelodiaWaterContactType EventType) const
{
	switch (EventType)
	{
	case EMelodiaWaterContactType::SurfaceEntry:
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::SwimStarted:
	case EMelodiaWaterContactType::DiveStarted:
	case EMelodiaWaterContactType::Ripple:
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::Footstep:
	case EMelodiaWaterContactType::WaterImpact:
		return true;
	default:
		return false;
	}
}
