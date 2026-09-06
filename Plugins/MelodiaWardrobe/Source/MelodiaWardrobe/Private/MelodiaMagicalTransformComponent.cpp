#include "MelodiaMagicalTransformComponent.h"

#include "Components/MeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Curves/CurveFloat.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "MelodiaTraversalComponent.h"
#include "MelodiaWardrobeComponent.h"
#include "MelodiaWardrobeSubsystem.h"

namespace
{
	/** Beat phase published by UMelodiaAudioReactivePresentationSubsystem. */
	const FName GBeatPhaseParameter{TEXT("BeatPhase")};
}

UMelodiaMagicalTransformComponent::UMelodiaMagicalTransformComponent()
{
	// Ticking is the exception, not the rule: the component only animates during a
	// transition or while a glide flare is easing. Everything else is event driven
	// off OnWardrobeChanged, so at rest this costs nothing.
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;

	RevealTrack = FMelodiaMagicalTransformTrack::MakeDefaultRevealTrack();

	// One case-insensitive substring is enough to catch every spelling the wing
	// slot has taken across exports: M_wing_001, ButterflyWing, Melusina_Wings.
	WingSlotNameFilters.Add(TEXT("wing"));

	// Real slot names from Melusina's current 33-slot body mesh
	// (Saved/Audit/melusina_slot_texture_sweep.json). Deliberately short: these
	// only shimmer, and a designer extends the list rather than the code.
	AccessorySlotNameFilters.Add(TEXT("bow"));
	AccessorySlotNameFilters.Add(TEXT("Iridescence"));

	// The decorative wardrobe slots. Accessories is first because that is where
	// the authored glide outfit lives (Cos_Accessories_MelusinaV2).
	AccessoryWardrobeSlots.Add(EMelodiaWardrobeSlot::Accessories);
	AccessoryWardrobeSlots.Add(EMelodiaWardrobeSlot::HairCharm);
	AccessoryWardrobeSlots.Add(EMelodiaWardrobeSlot::Trail);
}

void UMelodiaMagicalTransformComponent::BeginPlay()
{
	Super::BeginPlay();

	PaletteCollection = LoadObject<UMaterialParameterCollection>(
		nullptr, *MelodiaMagicalTransformMPC::CollectionPath.ToString());
	if (!PaletteCollection && bPublishToParameterCollection)
	{
		// Not fatal. The MID writes are the feature; the MPC mirror is only for
		// world-side effects, so a missing palette degrades to "no world pulse".
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_MAGICAL_TRANSFORM palette collection %s not found; "
				 "MPC mirror disabled, per-material reveal unaffected."),
			*MelodiaMagicalTransformMPC::CollectionPath.ToString());
	}

	// Claim before the first ApplyPose. The traversal component's own BeginPlay
	// calls SetWingPresentation(false), which writes Opacity 0 -- if that runs
	// after our first write and we have not claimed, the reveal starts erased.
	if (bClaimWingOpacityFromTraversal)
	{
		if (UMelodiaTraversalComponent* Traversal = GetTraversalComponent())
		{
			Traversal->SetWingPresentationOwnedExternally(true);
			bClaimedTraversalWingOpacity = true;
			Traversal->OnGlideStateChanged.AddUniqueDynamic(
				this, &UMelodiaMagicalTransformComponent::HandleGlideStateChanged);
		}
	}

	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		Wardrobe->OnWardrobeChanged.AddUniqueDynamic(
			this, &UMelodiaMagicalTransformComponent::HandleWardrobeChanged);
	}
	else
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_MAGICAL_TRANSFORM no wardrobe subsystem on %s; the reveal "
				 "will only respond to explicit PlayReveal/PlayConceal calls."),
			*GetNameSafe(GetOwner()));
	}

	ResolveBindings();

	// Snap, do not animate: on level load the outfit came out of the save and
	// there is no unlock moment to celebrate. bAnimateOnBeginPlay opts an
	// authored scene into the transformation instead.
	SyncToWardrobeState(bAnimateOnBeginPlay);
}

void UMelodiaMagicalTransformComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		Wardrobe->OnWardrobeChanged.RemoveDynamic(
			this, &UMelodiaMagicalTransformComponent::HandleWardrobeChanged);
	}

	if (UMelodiaTraversalComponent* Traversal = GetTraversalComponent())
	{
		Traversal->OnGlideStateChanged.RemoveDynamic(
			this, &UMelodiaMagicalTransformComponent::HandleGlideStateChanged);

		// Hand wing opacity back. Without this, tearing this component off a live
		// pawn leaves the traversal component permanently refusing to drive the
		// wings and nothing driving them at all.
		if (bClaimedTraversalWingOpacity)
		{
			Traversal->SetWingPresentationOwnedExternally(false);
			bClaimedTraversalWingOpacity = false;
		}
	}

	Bindings.Reset();
	HideableWingComponents.Reset();

	Super::EndPlay(EndPlayReason);
}

// ── Discovery ────────────────────────────────────────────────────────────────

USkeletalMeshComponent* UMelodiaMagicalTransformComponent::GetBodyMesh() const
{
	const ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
	return OwningCharacter ? OwningCharacter->GetMesh() : nullptr;
}

UMelodiaTraversalComponent* UMelodiaMagicalTransformComponent::GetTraversalComponent() const
{
	const AActor* Owner = GetOwner();
	return Owner ? Owner->FindComponentByClass<UMelodiaTraversalComponent>() : nullptr;
}

bool UMelodiaMagicalTransformComponent::ClassifySlot(const FName SlotName, bool& bOutIsWing) const
{
	bOutIsWing = false;
	if (SlotName.IsNone())
	{
		return false;
	}

	const FString SlotString = SlotName.ToString();

	// Wing wins over accessory when a name matches both. A slot that is wing
	// geometry must have its opacity driven, and silently demoting it to
	// "shimmer only" would leave the wings permanently visible.
	for (const FName Filter : WingSlotNameFilters)
	{
		if (!Filter.IsNone() && SlotString.Contains(Filter.ToString(), ESearchCase::IgnoreCase))
		{
			bOutIsWing = true;
			return true;
		}
	}

	for (const FName Filter : AccessorySlotNameFilters)
	{
		if (!Filter.IsNone() && SlotString.Contains(Filter.ToString(), ESearchCase::IgnoreCase))
		{
			return true;
		}
	}

	return false;
}

void UMelodiaMagicalTransformComponent::CollectFromMeshComponent(
	UMeshComponent* Mesh, const bool bForceWing, const bool bTagDiscovered,
	const bool bIncludeUnmatchedSlots)
{
	if (!IsValid(Mesh))
	{
		return;
	}

	const TArray<FName> SlotNames = Mesh->GetMaterialSlotNames();
	const int32 MaterialCount = Mesh->GetNumMaterials();

	for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
	{
		const FName SlotName = SlotNames.IsValidIndex(MaterialIndex)
			? SlotNames[MaterialIndex]
			: FName(*FString::Printf(TEXT("index_%d"), MaterialIndex));

		// Wing-ness is always decided by slot name even when the whole component
		// participates, so a garment that ships its own wing section still gets
		// opacity control rather than merely shimmering.
		bool bIsWing = false;
		const bool bMatched = ClassifySlot(SlotName, bIsWing);
		bIsWing = bIsWing || bForceWing;

		if (!bMatched && !bForceWing && !bIncludeUnmatchedSlots)
		{
			continue;
		}

		// MID creation is the claim. It replaces whatever MI was on the slot with a
		// dynamic child of it, so the authored look is preserved and only the
		// transform parameters become writable.
		UMaterialInstanceDynamic* Mid = Mesh->CreateAndSetMaterialInstanceDynamic(MaterialIndex);
		if (!Mid)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_MAGICAL_TRANSFORM could not create a MID for slot %s "
					 "(index %d) on %s; that slot will not participate."),
				*SlotName.ToString(), MaterialIndex, *GetNameSafe(Mesh));
			continue;
		}

		FMelodiaMagicalTransformBinding Binding;
		Binding.Material = Mid;
		Binding.SlotName = SlotName;
		Binding.bIsWing = bIsWing;
		Bindings.Add(Binding);
	}

	// Only tag-discovered components are hideable. A wing living as a material
	// slot on the body mesh shares its component with her face -- hiding that
	// component to conceal a wing would delete the character.
	if (bTagDiscovered && bForceWing)
	{
		HideableWingComponents.Add(Mesh);
	}
}

void UMelodiaMagicalTransformComponent::ResolveBindings()
{
	Bindings.Reset();
	HideableWingComponents.Reset();

	// 1. The body mesh: ONLY the named slots. This is the no-new-mesh route, and
	//    it is the one place unmatched slots must be skipped -- claiming every slot
	//    here would put her face and hair under the transform.
	CollectFromMeshComponent(
		GetBodyMesh(), /*bForceWing=*/false, /*bTagDiscovered=*/false,
		/*bIncludeUnmatchedSlots=*/false);

	// 2. Wardrobe slot components for the decorative slots. The whole garment IS
	//    the accessory, so every material participates regardless of its name.
	if (const AActor* Owner = GetOwner())
	{
		if (const UMelodiaWardrobeComponent* WardrobeComponent =
			Owner->FindComponentByClass<UMelodiaWardrobeComponent>())
		{
			for (const EMelodiaWardrobeSlot Slot : AccessoryWardrobeSlots)
			{
				// Not hideable: hiding the component would fight
				// UMelodiaWardrobeComponent, which owns slot visibility as its
				// unequip mechanism (EquipGarment(Slot, nullptr) hides rather than
				// destroys). Two owners of one visibility flag is the bug this
				// whole component exists to avoid.
				CollectFromMeshComponent(
					WardrobeComponent->GetSlotComponent(Slot),
					/*bForceWing=*/false, /*bTagDiscovered=*/false,
					/*bIncludeUnmatchedSlots=*/true);
			}
		}
	}

	// 3. Tagged mesh components. The escape hatch for the day wings become their
	//    own mesh, and the bridge to any already-authored MelodiaWings component.
	if (AActor* Owner = GetOwner())
	{
		const UMeshComponent* BodyMesh = GetBodyMesh();
		TArray<UMeshComponent*> MeshComponents;
		Owner->GetComponents<UMeshComponent>(MeshComponents);
		for (UMeshComponent* Candidate : MeshComponents)
		{
			// Skipping the body mesh here is what keeps step 1's filtering
			// meaningful: a tag on the body mesh would otherwise re-claim all 33
			// slots and drag the whole character into the dissolve.
			if (!IsValid(Candidate) || Candidate == BodyMesh)
			{
				continue;
			}
			if (!WingComponentTag.IsNone() && Candidate->ComponentHasTag(WingComponentTag))
			{
				CollectFromMeshComponent(
					Candidate, /*bForceWing=*/true, /*bTagDiscovered=*/true,
					/*bIncludeUnmatchedSlots=*/true);
			}
			else if (!AccessoryComponentTag.IsNone() && Candidate->ComponentHasTag(AccessoryComponentTag))
			{
				// bIncludeUnmatchedSlots matters here: a component tagged as an
				// accessory is an accessory whatever its slots happen to be named,
				// and filtering by name would have it claim nothing at all.
				CollectFromMeshComponent(
					Candidate, /*bForceWing=*/false, /*bTagDiscovered=*/true,
					/*bIncludeUnmatchedSlots=*/true);
			}
		}
	}

	if (Bindings.IsEmpty() && !bWarnedNoBindings)
	{
		bWarnedNoBindings = true;

		// This is THE failure mode worth shouting about. Setting a scalar on a
		// material that does not expose it is silent, and claiming zero materials
		// is silent too, so a mis-spelled filter produces a feature that appears
		// to work and does nothing. Say so once, loudly, with the filters echoed.
		FString Filters;
		for (const FName Filter : WingSlotNameFilters)
		{
			Filters += Filter.ToString() + TEXT(" ");
		}
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_MAGICAL_TRANSFORM claimed 0 materials on %s. No reveal will be "
				 "visible. Wing slot filters were [%s]; check them against the body mesh's "
				 "material slot names, or tag a wing mesh component '%s'."),
			*GetNameSafe(GetOwner()), *Filters.TrimEnd(), *WingComponentTag.ToString());
	}
}

void UMelodiaMagicalTransformComponent::RefreshAccessoryMaterials()
{
	ResolveBindings();

	// Re-apply immediately. A garment equipped after the reveal completed must
	// inherit the revealed pose, or it arrives at its material default and is the
	// one piece of the costume that is visibly wrong.
	ApplyPose(EvaluateCurrentPose());
}

int32 UMelodiaMagicalTransformComponent::GetClaimedWingMaterialCount() const
{
	int32 Count = 0;
	for (const FMelodiaMagicalTransformBinding& Binding : Bindings)
	{
		if (Binding.bIsWing)
		{
			++Count;
		}
	}
	return Count;
}

// ── Trigger ──────────────────────────────────────────────────────────────────

bool UMelodiaMagicalTransformComponent::IsTriggerCapabilityActive() const
{
	const UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);

	// Fail closed, matching the wardrobe's own capability contract: no authority
	// means no capability, so the wings stay off rather than appearing for free.
	return Wardrobe && Wardrobe->IsCapabilityActive(TriggerCapability, CapabilityContextId);
}

void UMelodiaMagicalTransformComponent::HandleWardrobeChanged(
	const EMelodiaWardrobeSlot Slot, const FName CosmeticId)
{
	// Re-resolve first: this broadcast is how we learn a wardrobe slot component
	// was created, and its materials cannot be claimed before it exists.
	if (AccessoryWardrobeSlots.Contains(Slot))
	{
		ResolveBindings();
	}

	SyncToWardrobeState(/*bAllowAnimation=*/true);
}

void UMelodiaMagicalTransformComponent::SyncToWardrobeState(const bool bAllowAnimation)
{
	const bool bShouldBeRevealed = IsTriggerCapabilityActive();

	// Only edges do anything. OnWardrobeChanged fires on every grant, equip and
	// unequip, and most of those do not change capability at all -- re-playing the
	// transformation on each would make a hair-charm swap restart the henshin.
	if (bShouldBeRevealed && Phase != EMelodiaMagicalTransformPhase::Revealed
		&& Phase != EMelodiaMagicalTransformPhase::Revealing)
	{
		if (bAllowAnimation)
		{
			PlayReveal();
		}
		else
		{
			SnapToPhase(EMelodiaMagicalTransformPhase::Revealed);
		}
	}
	else if (!bShouldBeRevealed && Phase != EMelodiaMagicalTransformPhase::Dormant
		&& Phase != EMelodiaMagicalTransformPhase::Concealing)
	{
		if (bAllowAnimation)
		{
			PlayConceal();
		}
		else
		{
			SnapToPhase(EMelodiaMagicalTransformPhase::Dormant);
		}
	}
	else if (!bAllowAnimation)
	{
		// Same phase, but a snap was requested: re-apply so freshly claimed
		// materials pick up the held pose.
		ApplyPose(EvaluateCurrentPose());
	}
}

void UMelodiaMagicalTransformComponent::HandleGlideStateChanged(const bool bIsGliding)
{
	bGlideFlareTarget = bIsGliding;
	UpdateTickEnabled();
}

// ── Playback ─────────────────────────────────────────────────────────────────

void UMelodiaMagicalTransformComponent::PlayReveal()
{
	if (Phase == EMelodiaMagicalTransformPhase::Revealing
		|| Phase == EMelodiaMagicalTransformPhase::Revealed)
	{
		return;
	}

	// NormalizedTime is left where it is on purpose. Reversing out of a conceal
	// resumes forward from the current point instead of restarting from 0.
	SetPhase(EMelodiaMagicalTransformPhase::Revealing);
	UpdateTickEnabled();
	ApplyPose(EvaluateCurrentPose());
}

void UMelodiaMagicalTransformComponent::PlayConceal()
{
	if (Phase == EMelodiaMagicalTransformPhase::Concealing
		|| Phase == EMelodiaMagicalTransformPhase::Dormant)
	{
		return;
	}

	SetPhase(EMelodiaMagicalTransformPhase::Concealing);
	UpdateTickEnabled();
	ApplyPose(EvaluateCurrentPose());
}

void UMelodiaMagicalTransformComponent::SnapToPhase(const EMelodiaMagicalTransformPhase TargetPhase)
{
	switch (TargetPhase)
	{
	case EMelodiaMagicalTransformPhase::Revealed:
		NormalizedTime = 1.0f;
		break;
	case EMelodiaMagicalTransformPhase::Dormant:
		NormalizedTime = 0.0f;
		break;
	default:
		// Revealing/Concealing are not steady states; snapping "to" one is a
		// caller error. Treat it as the endpoint it is heading for rather than
		// leaving the component ticking toward a target it was never given.
		NormalizedTime = (TargetPhase == EMelodiaMagicalTransformPhase::Revealing) ? 1.0f : 0.0f;
		break;
	}

	SetPhase(NormalizedTime >= 1.0f
		? EMelodiaMagicalTransformPhase::Revealed
		: EMelodiaMagicalTransformPhase::Dormant);

	UpdateTickEnabled();
	ApplyPose(EvaluateCurrentPose());
}

void UMelodiaMagicalTransformComponent::SetPhase(const EMelodiaMagicalTransformPhase NewPhase)
{
	if (Phase == NewPhase)
	{
		return;
	}
	Phase = NewPhase;
	OnMagicalTransformPhaseChanged.Broadcast(Phase, Progress);
}

void UMelodiaMagicalTransformComponent::UpdateTickEnabled()
{
	// Tick while a transition runs, and while the glide flare is still easing
	// toward its target. Both have to be checked: a flare that started after the
	// transformation finished still needs frames to blend in.
	const bool bFlareSettled = FMath::IsNearlyEqual(
		GlideFlareAlpha, bGlideFlareTarget ? 1.0f : 0.0f, UE_KINDA_SMALL_NUMBER);

	SetComponentTickEnabled(IsTransitioning() || !bFlareSettled);
}

void UMelodiaMagicalTransformComponent::TickComponent(
	const float DeltaTime, const ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	AdvanceTransform(DeltaTime);
}

void UMelodiaMagicalTransformComponent::AdvanceTransform(const float DeltaSeconds)
{
	if (Phase == EMelodiaMagicalTransformPhase::Revealing)
	{
		const float Duration = FMath::Max(RevealDurationSeconds, UE_KINDA_SMALL_NUMBER);
		NormalizedTime = FMath::Min(NormalizedTime + DeltaSeconds / Duration, 1.0f);
		if (NormalizedTime >= 1.0f)
		{
			SetPhase(EMelodiaMagicalTransformPhase::Revealed);
		}
	}
	else if (Phase == EMelodiaMagicalTransformPhase::Concealing)
	{
		const float Duration = FMath::Max(ConcealDurationSeconds, UE_KINDA_SMALL_NUMBER);
		NormalizedTime = FMath::Max(NormalizedTime - DeltaSeconds / Duration, 0.0f);
		if (NormalizedTime <= 0.0f)
		{
			SetPhase(EMelodiaMagicalTransformPhase::Dormant);
		}
	}

	const float FlareTarget = bGlideFlareTarget ? 1.0f : 0.0f;
	GlideFlareAlpha = FMath::FInterpConstantTo(
		GlideFlareAlpha, FlareTarget, DeltaSeconds,
		1.0f / FMath::Max(GlideFlareBlendSeconds, UE_KINDA_SMALL_NUMBER));

	ApplyPose(EvaluateCurrentPose());
	UpdateTickEnabled();
}

// ── Evaluation and write ─────────────────────────────────────────────────────

FMelodiaMagicalTransformPose UMelodiaMagicalTransformComponent::EvaluateCurrentPose() const
{
	FMelodiaMagicalTransformPose Pose = RevealTrack.Evaluate(NormalizedTime);

	// The curve override replaces progress only. Dissolve, bloom and sparkle stay
	// on the keys so an animator can retime the reveal against a music cue without
	// having to re-author the look-dev channels to match.
	if (ProgressCurveOverride)
	{
		Pose.Progress = FMath::Clamp(
			ProgressCurveOverride->GetFloatValue(NormalizedTime), 0.0f, 1.0f);
	}

	return Pose;
}

float UMelodiaMagicalTransformComponent::ReadBeatPulse() const
{
	if (!PaletteCollection || BeatModulationStrength <= 0.0f)
	{
		return 0.0f;
	}

	// GetWorld() rather than `this` as the world context: the Kismet helper takes a
	// non-const UObject* and this accessor is const by contract.
	const float BeatPhase = UKismetMaterialLibrary::GetScalarParameterValue(
		GetWorld(), PaletteCollection, GBeatPhaseParameter);

	// cos^2, not sin^2: BeatPhase is 0 ON the beat, so sin^2 peaks on the
	// off-beat. Same correction as UMelodiaAudioReactivePresentationSubsystem and
	// wire_audio_foliage_materials.py. With no music clock BeatPhase is 0, which
	// yields 1 here -- so it is scaled by strength and never fabricates a pulse.
	return FMath::Square(FMath::Cos(BeatPhase * PI));
}

void UMelodiaMagicalTransformComponent::ApplyPose(const FMelodiaMagicalTransformPose& Pose)
{
	Progress = Pose.Progress;

	const float BeatPulse = ReadBeatPulse();

	// Beat lifts the bloom between (1 - strength) and 1. It never touches
	// progress: a reveal whose completion depended on a beat would never finish
	// in silence, and the transformation has to be able to complete unscored.
	const float BeatGain = FMath::Lerp(1.0f - BeatModulationStrength, 1.0f, BeatPulse);

	// Flare is ADDED to the authored bloom, and scaled by progress so a glide
	// started mid-transformation cannot brighten wings that are not there yet.
	const float FlareBloom = GlideFlareBloom * GlideFlareAlpha * Pose.Progress;
	const float FinalBloom = Pose.Bloom * BeatGain + FlareBloom;

	for (const FMelodiaMagicalTransformBinding& Binding : Bindings)
	{
		UMaterialInstanceDynamic* Mid = Binding.Material;
		if (!IsValid(Mid))
		{
			continue;
		}

		Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Progress, Pose.Progress);
		Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Dissolve, Pose.Dissolve);
		Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Bloom, FinalBloom);
		Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Sparkle, Pose.Sparkle);
		Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Beat, BeatPulse);
		Mid->SetVectorParameterValue(MelodiaMagicalTransformParameter::Tint, WavefrontTint);

		// Opacity is wing-only. Driving it on the accessory slots would dissolve
		// her clothes along with revealing the wings.
		if (Binding.bIsWing)
		{
			Mid->SetScalarParameterValue(MelodiaMagicalTransformParameter::Opacity, Pose.Progress);

			// Both names, because the shared toon master exposes OpacityStrength
			// while a bespoke wing material is more likely to expose Opacity. The
			// unused one is a silent no-op, which is exactly what we want here.
			Mid->SetScalarParameterValue(
				MelodiaMagicalTransformParameter::OpacityStrength, Pose.Progress);
		}
	}

	// Fully concealed tag-discovered wing meshes are hidden outright so they stop
	// costing draw calls. Threshold, not exact zero: a mask at 0.001 renders
	// nothing but still submits geometry.
	const bool bWingVisible = Pose.Progress > UE_KINDA_SMALL_NUMBER;
	for (const TWeakObjectPtr<UMeshComponent>& WeakWing : HideableWingComponents)
	{
		if (UMeshComponent* Wing = WeakWing.Get())
		{
			if (Wing->IsVisible() != bWingVisible)
			{
				Wing->SetVisibility(bWingVisible, true);
				Wing->SetHiddenInGame(!bWingVisible, true);
			}
		}
	}

	if (bPublishToParameterCollection && PaletteCollection && GetWorld())
	{
		UKismetMaterialLibrary::SetScalarParameterValue(
			GetWorld(), PaletteCollection, MelodiaMagicalTransformMPC::Progress, Pose.Progress);

		// Flare mirrors the wavefront, not the bloom: bloom carries the glide term
		// and world-side post process should not brighten every time she glides.
		UKismetMaterialLibrary::SetScalarParameterValue(
			GetWorld(), PaletteCollection, MelodiaMagicalTransformMPC::Flare, Pose.Dissolve);
	}
}
