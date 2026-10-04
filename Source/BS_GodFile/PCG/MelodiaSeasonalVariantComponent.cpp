#include "MelodiaSeasonalVariantComponent.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "EngineUtils.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "UObject/UnrealType.h"

namespace
{
	const TCHAR* PalettePath = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
	// Cumulative days before each month in a non-leap year.
	constexpr int32 DaysBeforeMonth[12] = { 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334 };
	// Day of year of the March equinox (Mar 20) = start of spring.
	constexpr float SpringStartDoy = 79.0f;
	constexpr float DaysPerSeason = 91.31f;

	float WrapSeason(const float V)
	{
		return V - 4.0f * FMath::FloorToFloat(V / 4.0f);
	}
}

UMelodiaSeasonalVariantComponent::UMelodiaSeasonalVariantComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UMelodiaSeasonalVariantComponent::BeginPlay()
{
	Super::BeginPlay();
	PaletteMPC = Cast<UMaterialParameterCollection>(StaticLoadObject(UMaterialParameterCollection::StaticClass(), nullptr, PalettePath));
	DisplayedPosition = ResolveTargetPosition(); // start on the right season, no sweep from spring
	CachedTarget = DisplayedPosition;
	Rescan();
	Apply();
}

void UMelodiaSeasonalVariantComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	RestoreAll();
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaSeasonalVariantComponent::ReadSkyDate(int32& OutMonth, int32& OutDay)
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	if (!SkyActor.IsValid())
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->GetClass()->GetName().StartsWith(TEXT("Ultra_Dynamic_Sky")))
			{
				SkyActor = *It;
				break;
			}
		}
	}
	const AActor* Sky = SkyActor.Get();
	if (!Sky)
	{
		return false;
	}
	const FNumericProperty* MonthProp = CastField<FNumericProperty>(Sky->GetClass()->FindPropertyByName(TEXT("Month")));
	const FNumericProperty* DayProp = CastField<FNumericProperty>(Sky->GetClass()->FindPropertyByName(TEXT("Day")));
	if (!MonthProp || !DayProp || !MonthProp->IsInteger() || !DayProp->IsInteger())
	{
		return false;
	}
	OutMonth = static_cast<int32>(MonthProp->GetSignedIntPropertyValue(MonthProp->ContainerPtrToValuePtr<void>(Sky)));
	OutDay = static_cast<int32>(DayProp->GetSignedIntPropertyValue(DayProp->ContainerPtrToValuePtr<void>(Sky)));
	return true;
}

float UMelodiaSeasonalVariantComponent::ResolveTargetPosition()
{
	float Position = SeasonPosition;
	int32 Month = 0;
	int32 Day = 0;
	if (Source == EMelodiaSeasonSource::UltraDynamicSky && ReadSkyDate(Month, Day))
	{
		const int32 M = FMath::Clamp(Month, 1, 12);
		const float Doy = static_cast<float>(DaysBeforeMonth[M - 1] + FMath::Clamp(Day, 1, 31));
		Position = (Doy - SpringStartDoy) / DaysPerSeason;
	}
	if (bSouthernHemisphere)
	{
		Position += 2.0f;
	}
	return WrapSeason(Position);
}

EMelodiaSeason UMelodiaSeasonalVariantComponent::GetDominantSeason() const
{
	return static_cast<EMelodiaSeason>(FMath::Clamp(FMath::FloorToInt(WrapSeason(DisplayedPosition) + 0.5f) % 4, 0, 3));
}

void UMelodiaSeasonalVariantComponent::Track(UInstancedStaticMeshComponent* Comp)
{
	if (!Comp || !Profile || Tracked.Num() >= MaxComponents)
	{
		return;
	}
	for (const FTrackedComp& T : Tracked)
	{
		if (T.Comp.Get() == Comp)
		{
			return;
		}
	}
	FTrackedComp& T = Tracked.AddDefaulted_GetRef();
	T.Comp = Comp;
	T.OriginalMesh = Comp->GetStaticMesh();
	const int32 Slots = Comp->GetNumMaterials();
	for (int32 i = 0; i < Slots; ++i)
	{
		UMaterialInterface* Original = Comp->GetMaterial(i);
		T.OriginalMaterials.Add(Original);
		if (!Original)
		{
			continue;
		}
		if (FSharedMID* Entry = GetOrCreateShared(Original))
		{
			if (UMaterialInstanceDynamic* MID = Entry->MID.Get())
			{
				Comp->SetMaterial(i, MID);
			}
		}
	}
	AppliedPosition = -1.0f; // new component: force an apply
}

UMelodiaSeasonalVariantComponent::FSharedMID* UMelodiaSeasonalVariantComponent::GetOrCreateShared(UMaterialInterface* Original)
{
	if (!Original || !Profile)
	{
		return nullptr;
	}
	if (FSharedMID* Existing = Shared.Find(Original))
	{
		if (Existing->MID.IsValid())
		{
			return Existing;
		}
	}
	UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Original, this);
	if (!MID)
	{
		return nullptr;
	}
	FSharedMID& Entry = Shared.FindOrAdd(Original);
	Entry = FSharedMID();
	Entry.MID = MID;
	for (const FName& Param : Profile->TintParameterNames)
	{
		FLinearColor C = FLinearColor::White;
		Entry.BaseColors.Add(MID->GetVectorParameterValue(Param, C) ? FLinearColor(C.R, C.G, C.B, 1.0f) : FLinearColor(0.0f, 0.0f, 0.0f, -1.0f));
	}
	FLinearColor Hue = FLinearColor::White;
	if (MID->GetVectorParameterValue(Profile->HueTintParameter, Hue))
	{
		Entry.BaseHueTint = FLinearColor(Hue.R, Hue.G, Hue.B, 1.0f);
	}
	float V = 0.0f;
	if (MID->GetScalarParameterValue(Profile->HueAmountParameter, V))
	{
		Entry.BaseAmount = V;
	}
	if (MID->GetScalarParameterValue(Profile->HueEmissiveParameter, V))
	{
		Entry.BaseEmissive = V;
	}
	return &Entry;
}

void UMelodiaSeasonalVariantComponent::Rescan()
{
	Tracked.RemoveAll([](const FTrackedComp& T) { return !T.Comp.IsValid(); });

	const UWorld* World = GetWorld();
	const AActor* Owner = GetOwner();
	if (!World || !Owner || !Profile)
	{
		return;
	}
	const FVector Center = Owner->GetActorLocation();
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor || Actor == Owner)
		{
			continue;
		}
		const bool bActorTagged = Actor->ActorHasTag(Profile->ReactiveTag);
		TInlineComponentArray<UInstancedStaticMeshComponent*> Comps;
		Actor->GetComponents(Comps);
		for (UInstancedStaticMeshComponent* Comp : Comps)
		{
			if (!Comp || Comp->GetInstanceCount() == 0)
			{
				continue;
			}
			if (!bAffectAllInstancedMeshes && !bActorTagged && !Comp->ComponentHasTag(Profile->ReactiveTag))
			{
				continue;
			}
			const FBoxSphereBounds B = Comp->Bounds;
			if (FVector::Dist(B.Origin, Center) > Radius + B.SphereRadius)
			{
				continue;
			}
			Track(Comp);
		}
	}
}

void UMelodiaSeasonalVariantComponent::RestoreAll()
{
	for (FTrackedComp& T : Tracked)
	{
		UInstancedStaticMeshComponent* Comp = T.Comp.Get();
		if (!Comp)
		{
			continue;
		}
		if (UStaticMesh* Mesh = T.OriginalMesh.Get())
		{
			if (Comp->GetStaticMesh() != Mesh)
			{
				Comp->SetStaticMesh(Mesh);
			}
		}
		for (int32 i = 0; i < T.OriginalMaterials.Num(); ++i)
		{
			if (UMaterialInterface* Original = T.OriginalMaterials[i].Get())
			{
				Comp->SetMaterial(i, Original);
			}
		}
	}
	Tracked.Reset();
	Shared.Reset();
}

void UMelodiaSeasonalVariantComponent::TickComponent(const float DeltaTime, const ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld() || !Profile)
	{
		return; // never recolour authored foliage in the editor viewport
	}

	PollTimer += DeltaTime;
	if (PollTimer >= 0.5f)
	{
		PollTimer = 0.0f;
		CachedTarget = ResolveTargetPosition();
	}
	RescanTimer += DeltaTime;
	if (RescanTimer >= 3.0f)
	{
		RescanTimer = 0.0f;
		Rescan();
	}

	// Move the displayed position toward the target the short way round the year.
	const float Delta = WrapSeason(CachedTarget - DisplayedPosition + 6.0f) - 2.0f;
	const float MaxStep = TransitionSpeed * DeltaTime;
	DisplayedPosition = WrapSeason(DisplayedPosition + FMath::Clamp(Delta, -MaxStep, MaxStep));

	bool bDirty = false;
	if (FMath::Abs(DisplayedPosition - AppliedPosition) > 0.002f || AppliedPosition < 0.0f)
	{
		Apply();
		bDirty = true;
	}

	if (bAudioHueStrobe || bStrobeWasOn)
	{
		AudioTimer += DeltaTime;
		if (AudioTimer >= 1.0f / 30.0f)
		{
			UMaterialParameterCollectionInstance* Palette = PaletteMPC ? World->GetParameterCollectionInstance(PaletteMPC) : nullptr;
			TickAudioHue(AudioTimer, Palette);
			AudioTimer = 0.0f;
			bDirty = true;
		}
	}
	if (bDirty)
	{
		ApplyMaterialParams();
	}
}

void UMelodiaSeasonalVariantComponent::TickAudioHue(const float DeltaSeconds, UMaterialParameterCollectionInstance* Palette)
{
	float Pulse = 0.0f;
	float Bass = 0.0f;
	float Treble = 0.0f;
	if (Palette)
	{
		Palette->GetScalarParameterValue(FName(TEXT("BeatPulse")), Pulse);
		Palette->GetScalarParameterValue(FName(TEXT("Bass")), Bass);
		Palette->GetScalarParameterValue(FName(TEXT("Treble")), Treble);
	}
	Pulse = FMath::Clamp(Pulse, 0.0f, 1.0f);
	if (Pulse > 0.8f && LastBeatPulse < 0.5f)
	{
		HueIndex += 1.0f; // one golden-ratio hue step per beat
	}
	LastBeatPulse = Pulse;

	const float Alpha = 1.0f - FMath::Exp(-DeltaSeconds / 0.08f);
	BassSmoothed += (FMath::Clamp(Bass, 0.0f, 1.0f) - BassSmoothed) * Alpha;
	TrebleSmoothed += (FMath::Clamp(Treble, 0.0f, 1.0f) - TrebleSmoothed) * Alpha;
	BeatEnergy = FMath::Clamp(FMath::Max(Pulse * Pulse, BassSmoothed), 0.0f, 1.0f);

	// Hue wanders around the season tint's own hue; HueRange 1 = the whole wheel.
	const FLinearColor SeasonHSV = SeasonTintNow.LinearRGBToHSV();
	const float BaseHue = SeasonHSV.R / 360.0f;
	const float Step = HueIndex * 0.6180339887f;
	const float Offset = (Step - FMath::FloorToFloat(Step) - 0.5f) * HueRange + TrebleSmoothed * 0.08f;
	const float Hue = BaseHue + Offset;
	StrobeHue = Hue - FMath::FloorToFloat(Hue);
}

void UMelodiaSeasonalVariantComponent::Apply()
{
	if (!Profile || Profile->Looks.Num() == 0)
	{
		return;
	}
	AppliedPosition = DisplayedPosition;

	const float P = WrapSeason(DisplayedPosition);
	const int32 A = FMath::FloorToInt(P) % 4;
	const int32 B = (A + 1) % 4;
	const float Raw = P - FMath::FloorToFloat(P);
	const float Alpha = Raw * Raw * (3.0f - 2.0f * Raw); // smoothstep between seasons
	const int32 Last = Profile->Looks.Num() - 1;
	const FMelodiaSeasonLook& LookA = Profile->Looks[FMath::Min(A, Last)];
	const FMelodiaSeasonLook& LookB = Profile->Looks[FMath::Min(B, Last)];
	SeasonTintNow = FMath::Lerp(LookA.Tint, LookB.Tint, Alpha);
	SeasonStrengthNow = FMath::Lerp(LookA.TintStrength, LookB.TintStrength, Alpha);
	const FMelodiaSeasonLook& Dominant = Alpha < 0.5f ? LookA : LookB;

	// Instance change: swap the mesh while the dominant season defines a replacement; otherwise restore.
	for (FTrackedComp& T : Tracked)
	{
		UInstancedStaticMeshComponent* Comp = T.Comp.Get();
		UStaticMesh* Original = T.OriginalMesh.Get();
		if (!Comp || !Original)
		{
			continue;
		}
		UStaticMesh* Wanted = Original;
		for (const TPair<TSoftObjectPtr<UStaticMesh>, TSoftObjectPtr<UStaticMesh>>& Swap : Dominant.MeshSwaps)
		{
			if (Swap.Key.Get() == Original || Swap.Key.ToSoftObjectPath() == FSoftObjectPath(Original))
			{
				if (UStaticMesh* Replacement = Swap.Value.LoadSynchronous())
				{
					Wanted = Replacement;
				}
				break;
			}
		}
		if (Comp->GetStaticMesh() != Wanted)
		{
			Comp->SetStaticMesh(Wanted);
		}
	}
}

void UMelodiaSeasonalVariantComponent::ApplyMaterialParams()
{
	if (!Profile)
	{
		return;
	}
	const bool bStrobe = bAudioHueStrobe;
	const FLinearColor StrobeRGB = FLinearColor(StrobeHue * 360.0f, HueSaturation, 1.0f).HSVToLinearRGB();

	for (TPair<TWeakObjectPtr<UMaterialInterface>, FSharedMID>& Pair : Shared)
	{
		FSharedMID& Entry = Pair.Value;
		UMaterialInstanceDynamic* MID = Entry.MID.Get();
		if (!MID)
		{
			continue;
		}
		for (int32 i = 0; i < Profile->TintParameterNames.Num() && i < Entry.BaseColors.Num(); ++i)
		{
			const FLinearColor& Base = Entry.BaseColors[i];
			if (Base.A < 0.0f)
			{
				continue;
			}
			FLinearColor Out = FMath::Lerp(Base, SeasonTintNow, SeasonStrengthNow);
			if (bStrobe && Profile->TintParameterNames[i] == Profile->HueTintParameter)
			{
				Out = FMath::Lerp(StrobeRGB, Out, SeasonTintShare);
			}
			MID->SetVectorParameterValue(Profile->TintParameterNames[i], FLinearColor(Out.R, Out.G, Out.B, 1.0f));
		}
		if (bStrobe)
		{
			if (!Profile->TintParameterNames.Contains(Profile->HueTintParameter) && Entry.BaseHueTint.A >= 0.0f)
			{
				const FLinearColor Out = FMath::Lerp(StrobeRGB, FMath::Lerp(Entry.BaseHueTint, SeasonTintNow, SeasonStrengthNow), SeasonTintShare);
				MID->SetVectorParameterValue(Profile->HueTintParameter, FLinearColor(Out.R, Out.G, Out.B, 1.0f));
			}
			if (Entry.BaseAmount >= 0.0f)
			{
				MID->SetScalarParameterValue(Profile->HueAmountParameter, FMath::Clamp(Entry.BaseAmount + HueAmountGain * BeatEnergy, 0.0f, 1.0f));
			}
			if (Entry.BaseEmissive >= 0.0f)
			{
				MID->SetScalarParameterValue(Profile->HueEmissiveParameter, Entry.BaseEmissive * (1.0f + HueEmissiveGain * BeatEnergy));
			}
		}
		else if (bStrobeWasOn)
		{
			// Strobe switched off at runtime: hand the authored values back.
			if (Entry.BaseAmount >= 0.0f)
			{
				MID->SetScalarParameterValue(Profile->HueAmountParameter, Entry.BaseAmount);
			}
			if (Entry.BaseEmissive >= 0.0f)
			{
				MID->SetScalarParameterValue(Profile->HueEmissiveParameter, Entry.BaseEmissive);
			}
		}
	}
	bStrobeWasOn = bStrobe;
}
