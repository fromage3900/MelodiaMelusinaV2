// MelodiaWardrobe — slot-swap runtime component (Decision 044 re-host).

#include "MelodiaWardrobeComponent.h"
#include "MelodiaWardrobeSubsystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"

UMelodiaWardrobeComponent::UMelodiaWardrobeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaWardrobeComponent::BeginPlay()
{
	Super::BeginPlay();
	ApplyWardrobeState();
}

void UMelodiaWardrobeComponent::ApplyWardrobeState()
{
	TSet<EMelodiaWardrobeSlot> ClaimedSlots;

	// Restore the equipped state the narrative record says we own (Decision 043
	// save/load): apply each equipped cosmetic's mesh to its slot.
	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		const FMelodiaWardrobeState State = Wardrobe->GetState();
		for (const TPair<EMelodiaWardrobeSlot, FName>& Pair : State.EquippedCosmeticIds)
		{
			// A saved slot is authoritative even if its catalog mesh is currently
			// unavailable; silently falling back would hide a broken save/catalog
			// reference.
			ClaimedSlots.Add(Pair.Key);
			if (USkeletalMesh* Mesh = Wardrobe->GetCosmeticMesh(Pair.Value))
			{
				if (!IsGarmentSkeletonCompatible(Mesh))
				{
					UE_LOG(LogTemp, Warning,
						TEXT("MELODIA_WARDROBE restore refused slot %d cosmetic %s: skeleton mismatch; "
							 "stale presentation hidden."),
						static_cast<int32>(Pair.Key), *Pair.Value.ToString());
					EquipGarment(Pair.Key, nullptr);
					continue;
				}

				EquipGarment(Pair.Key, Mesh);
				if (!IsSlotShowingMesh(Pair.Key, Mesh))
				{
					// A failed component creation or presentation bind must not
					// leave a previous save's garment visible for a slot claimed by
					// this broken record.
					EquipGarment(Pair.Key, nullptr);
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE slot %d holds saved cosmetic %s whose mesh will not "
						 "resolve; leaving the slot empty rather than substituting."),
					static_cast<int32>(Pair.Key), *Pair.Value.ToString());
				EquipGarment(Pair.Key, nullptr);
			}
		}

		// Slots an equipped garment replaces stay empty; defaults must not fill them.
		for (const EMelodiaWardrobeSlot Replaced : Wardrobe->GetReplacedSlots())
		{
			if (!ClaimedSlots.Contains(Replaced))
			{
				ClaimedSlots.Add(Replaced);
				EquipGarment(Replaced, nullptr);
			}
		}
	}

	// Fixed V2 defaults are presentation-only references. They are applied
	// only when the save has no explicit cosmetic for that slot, so the
	// narrative wardrobe remains the authority for player-selected cosmetics.
	for (const TPair<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMesh>>& Pair : DefaultGarmentMeshes)
	{
		if (!ClaimedSlots.Contains(Pair.Key) && Pair.Value)
		{
			ClaimedSlots.Add(Pair.Key);
			if (!IsGarmentSkeletonCompatible(Pair.Value))
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE default slot %d refused: skeleton mismatch; stale presentation hidden."),
					static_cast<int32>(Pair.Key));
				EquipGarment(Pair.Key, nullptr);
				continue;
			}

			EquipGarment(Pair.Key, Pair.Value);
			if (!IsSlotShowingMesh(Pair.Key, Pair.Value))
			{
				// A broken default must not leave a previous save's garment visible
				// merely because the current narrative record has no claim.
				EquipGarment(Pair.Key, nullptr);
			}
		}
	}

	// Anything this state does not claim must be cleared. On a re-apply (save restore)
	// a slot the new record leaves empty would otherwise keep showing the previous
	// save's garment.
	for (const TPair<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMeshComponent>>& Pair : SlotComponents)
	{
		if (!ClaimedSlots.Contains(Pair.Key) && Pair.Value)
		{
			Pair.Value->SetVisibility(false);
		}
	}

	// The restored equipped set may cover different body regions than whatever was
	// visible before the restore: re-derive the collapse from the record, not from
	// what happened to be equipped last frame.
	ApplyBodyRegionVisibility();
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::GetBodyMesh() const
{
	// A Character owns its body mesh directly; this is the player path.
	if (const ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner()))
	{
		if (USkeletalMeshComponent* CharacterMesh = OwningCharacter->GetMesh())
		{
			return CharacterMesh;
		}
	}

	// Battle and portfolio presenters are plain AActors, not Characters, so the cast above
	// returns null and every garment then fails IsGarmentSkeletonCompatible against a null
	// body -- which is why the presenter rendered with no shirt, boots or accessories while
	// its DefaultGarmentMeshes were fully configured. Resolve by component name first: a
	// presenter may also carry a template mannequin on its root SkeletalMesh component, and
	// picking that would compare garments against UE4_Mannequin_Skeleton and refuse them all.
	const AActor* OwningActor = GetOwner();
	if (!OwningActor)
	{
		return nullptr;
	}

	TArray<USkeletalMeshComponent*> Candidates;
	OwningActor->GetComponents<USkeletalMeshComponent>(Candidates);

	static const TCHAR* PreferredNames[] = { TEXT("MelusinaPresentationMesh"), TEXT("CharacterMesh0") };
	for (const TCHAR* Preferred : PreferredNames)
	{
		for (USkeletalMeshComponent* Candidate : Candidates)
		{
			if (Candidate && Candidate->GetSkeletalMeshAsset() && Candidate->GetName() == Preferred)
			{
				return Candidate;
			}
		}
	}

	// Last resort: the first component that actually has a mesh. Components with no asset
	// are skipped so a cleared placeholder slot never wins over the real body.
	for (USkeletalMeshComponent* Candidate : Candidates)
	{
		if (Candidate && Candidate->GetSkeletalMeshAsset())
		{
			return Candidate;
		}
	}

	return nullptr;
}

bool UMelodiaWardrobeComponent::IsGarmentSkeletonCompatible(const USkeletalMesh* GarmentMesh) const
{
	if (!GarmentMesh)
	{
		return false;
	}

	const USkeletalMeshComponent* BodyMesh = GetBodyMesh();
	const USkeletalMesh* BodyAsset = BodyMesh ? BodyMesh->GetSkeletalMeshAsset() : nullptr;
	if (!BodyAsset)
	{
		return false;
	}

	// Leader-pose sharing copies the body's bone transforms by index. A garment built
	// on a different USkeleton still renders, just wrongly -- so this has to be an
	// explicit refusal, not a best-effort attach.
	return GarmentMesh->GetSkeleton() == BodyAsset->GetSkeleton();
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::FindOrCreateSlotComponent(
	const EMelodiaWardrobeSlot Slot, USkeletalMesh* InitialMesh)
{
	if (TObjectPtr<USkeletalMeshComponent>* Existing = SlotComponents.Find(Slot))
	{
		return *Existing;
	}

	// Owner is addressed as AActor, not ACharacter: presenters are plain Actors and a
	// Character cast here would refuse to build any slot for them. NewObject and
	// AddInstanceComponent below both take AActor, so nothing else needs a Character.
	AActor* OwningActor = GetOwner();
	USkeletalMeshComponent* BodyMesh = GetBodyMesh();
	if (!OwningActor || !BodyMesh)
	{
		return nullptr;
	}

	const FName ComponentName = *FString::Printf(TEXT("WardrobeSlot_%s"), *UEnum::GetValueAsString(Slot));
	// Adopt the authored hat instead of adding a second visible copy. It is already
	// actor-owned and registered. Other intentional same-mesh components are untouched.
	USkeletalMeshComponent* SlotComp = nullptr;
	if (Slot == EMelodiaWardrobeSlot::Hat)
	{
		for (UActorComponent* Component : OwningActor->GetComponents())
		{
			USkeletalMeshComponent* Authored = Cast<USkeletalMeshComponent>(Component);
			if (Authored && Authored != BodyMesh && Authored->GetFName() == FName(TEXT("HatMesh"))
				&& Authored->GetSkeletalMeshAsset() == InitialMesh)
			{
				SlotComp = Authored;
				break;
			}
		}
	}
	const bool bAdopted = SlotComp != nullptr;
	if (!SlotComp)
	{
		SlotComp = NewObject<USkeletalMeshComponent>(OwningActor, ComponentName);
	}

	// Garments are pure presentation. A SkeletalMeshComponent defaults to query+physics
	// collision, so without this each equipped piece added an extra collider to the
	// pawn -- overlap volumes and traces would hit the dress before the character.
	SlotComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SlotComp->SetCollisionProfileName(TEXT("NoCollision"));
	SlotComp->SetGenerateOverlapEvents(false);
	SlotComp->CanCharacterStepUpOn = ECB_No;

	// Full-skeleton garments already deform in body component space via LeaderPose.
	// A bone socket would apply that bone transform again and detach the silhouette.
	if (bAdopted)
	{
		SlotComp->AttachToComponent(BodyMesh, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		SlotComp->SetRelativeTransform(FTransform::Identity);
	}
	else
	{
		SlotComp->SetupAttachment(BodyMesh);
	}

	// Garments are part of the hero silhouette: write the same custom depth/stencil as the
	// body, so post-process passes that key off the hero stencil (the storybook outline skips
	// stencil 4 because heroes carry inverted-hull outlines) treat the dress like the skin.
	SlotComp->SetRenderCustomDepth(BodyMesh->bRenderCustomDepth);
	SlotComp->SetCustomDepthStencilValue(BodyMesh->CustomDepthStencilValue);

	// Order matters: the mesh must exist before the leader-pose binding, or the
	// binding is built against an empty component and the garment never follows the
	// body until something reassigns it.
	SlotComp->SetSkeletalMesh(InitialMesh);

	// Same technique as the hair's leader-pose sharing: the garment shares the
	// body's bone transforms directly rather than running its own animation.
	SlotComp->SetLeaderPoseComponent(BodyMesh);

	if (!bAdopted)
	{
		SlotComp->RegisterComponent();
	}

	// Register with the actor's instance-component list. NewObject + RegisterComponent
	// alone leaves the component outside the owner's bookkeeping: it does not appear in
	// GetComponents(), is not serialised with the actor, and is not torn down with it.
	if (!bAdopted)
	{
		OwningActor->AddInstanceComponent(SlotComp);
	}

	SlotComponents.Add(Slot, SlotComp);
	return SlotComp;
}

void UMelodiaWardrobeComponent::EquipGarment(const EMelodiaWardrobeSlot Slot, USkeletalMesh* GarmentMesh)
{
	// Unequip: hide an existing slot without destroying it, so re-equipping is cheap.
	// Never create a component just to hide it.
	if (!GarmentMesh)
	{
		if (USkeletalMeshComponent* Existing = GetSlotComponent(Slot))
		{
			Existing->SetVisibility(false);
		}
		return;
	}

	if (!IsGarmentSkeletonCompatible(GarmentMesh))
	{
		UE_LOG(LogTemp, Error,
			TEXT("MELODIA_WARDROBE slot %d refused garment %s: skeleton does not match the body "
				 "mesh, so leader-pose sharing would deform it. Slot left unchanged."),
			static_cast<int32>(Slot), *GetNameSafe(GarmentMesh));
		return;
	}

	USkeletalMeshComponent* SlotComp = FindOrCreateSlotComponent(Slot, GarmentMesh);
	if (!SlotComp)
	{
		return;
	}

	// On the create path FindOrCreateSlotComponent already applied the mesh in the
	// correct order; this covers the swap-an-existing-slot case.
	if (SlotComp->GetSkeletalMeshAsset() != GarmentMesh)
	{
		SlotComp->SetSkeletalMesh(GarmentMesh);
	}
	SlotComp->SetVisibility(true);

	// The skirt is Melusina's performance surface: her rhythm grades play back on it as
	// Chladni figures. Re-registered on every garment change so the new cloth carries it.
	if (Slot == EMelodiaWardrobeSlot::Skirt && GetWorld() && GetWorld()->IsGameWorld())
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->RegisterPerformanceSurface(SlotComp);
		}
	}
}

bool UMelodiaWardrobeComponent::EquipCosmetic(const FName CosmeticId)
{
	UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (!Wardrobe)
	{
		return false;
	}

	// Presentation preflight must happen before the authority writes the equipped
	// map. A catalog record can be valid while its mesh is incompatible with the
	// pawn's body skeleton; persisting that selection would create an equipped
	// cosmetic that can never be presented.
	USkeletalMesh* Mesh = Wardrobe->GetCosmeticMesh(CosmeticId);
	if (!Mesh || !IsGarmentSkeletonCompatible(Mesh))
	{
		return false;
	}

	const EMelodiaWardrobeSlot Slot = Wardrobe->GetSlotForCosmetic(CosmeticId);
	const FName PreviousCosmeticId = Wardrobe->GetEquipped(Slot);

	// Authority first after the component-local presentation preflight: the
	// canonical narrative record remains the only durable wardrobe state.
	if (!Wardrobe->EquipCosmetic(CosmeticId))
	{
		return false;
	}

	EquipGarment(Slot, Mesh);

	// EquipGarment can still fail if the owner/body component disappears during
	// teardown. Roll the canonical map back to the previous selection rather than
	// reporting success with a state the player cannot see.
	if (IsSlotShowingMesh(Slot, Mesh))
	{
		// Re-derive every slot from the record: the equip may have cleared replaced slots
		// or taken off a garment that replaced this one.
		ApplyWardrobeState();
		return true;
	}

	if (PreviousCosmeticId.IsNone())
	{
		Wardrobe->UnequipSlot(Slot);
		EquipGarment(Slot, nullptr);
	}
	else if (USkeletalMesh* PreviousMesh = Wardrobe->GetCosmeticMesh(PreviousCosmeticId))
	{
		Wardrobe->EquipCosmetic(PreviousCosmeticId);
		EquipGarment(Slot, PreviousMesh);
	}
	else
	{
		Wardrobe->UnequipSlot(Slot);
		EquipGarment(Slot, nullptr);
	}
	return false;
}

bool UMelodiaWardrobeComponent::ApplyCosmeticPresentation(const FName CosmeticId)
{
	if (CosmeticId.IsNone())
	{
		return false;
	}

	UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (!Wardrobe || !Wardrobe->IsOwned(CosmeticId))
	{
		// Companion presentation is fail-closed: an unowned id is not a request
		// to acquire anything, and no narrative record is touched here.
		return false;
	}

	USkeletalMesh* Mesh = Wardrobe->GetCosmeticMesh(CosmeticId);
	if (!Mesh || !IsGarmentSkeletonCompatible(Mesh))
	{
		return false;
	}

	const EMelodiaWardrobeSlot Slot = Wardrobe->GetSlotForCosmetic(CosmeticId);
	EquipGarment(Slot, Mesh);
	return IsSlotShowingMesh(Slot, Mesh);
}

EMelodiaCompanionWardrobeRequestResult UMelodiaWardrobeComponent::RequestCompanionWardrobe_Implementation(
	const FMelodiaCompanionWardrobeProfile& Profile)
{
	FText ValidationError;
	if (!Profile.IsValid(&ValidationError))
	{
		return EMelodiaCompanionWardrobeRequestResult::RejectedInvalidProfile;
	}

	UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (!Wardrobe)
	{
		return EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider;
	}

	// Default path: read ownership and catalog data, then apply the mesh directly.
	// ApplyCosmeticPresentation deliberately does not call EquipCosmetic, because
	// equipping is a durable player choice and would write the canonical record.
	for (const FName CosmeticId : Profile.PreferredCosmeticIds)
	{
		if (Wardrobe->IsOwned(CosmeticId) && ApplyCosmeticPresentation(CosmeticId))
		{
			return EMelodiaCompanionWardrobeRequestResult::AppliedOwnedCosmetic;
		}
	}

	if (!Profile.bAllowPrototypeGrant)
	{
		return EMelodiaCompanionWardrobeRequestResult::RejectedNoOwnedCosmetic;
	}

	// The profile validator requires the cosmetic and receipt to be explicit and
	// requires the cosmetic to be in the preferred list. This is the only branch
	// allowed to call GrantCosmetic, preserving the wardrobe subsystem as the sole
	// ownership/save authority while keeping accidental grants impossible.
	if (!Wardrobe->GrantCosmetic(Profile.PrototypeGrantCosmeticId, Profile.PrototypeGrantId))
	{
		return EMelodiaCompanionWardrobeRequestResult::RejectedPrototypeGrantFailed;
	}

	return ApplyCosmeticPresentation(Profile.PrototypeGrantCosmeticId)
		? EMelodiaCompanionWardrobeRequestResult::GrantedAndAppliedPrototypeCosmetic
		: EMelodiaCompanionWardrobeRequestResult::RejectedPresentationFailed;
}

void UMelodiaWardrobeComponent::UnequipSlot(const EMelodiaWardrobeSlot Slot)
{
	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		Wardrobe->UnequipSlot(Slot);
	}
	// Re-derive every slot from the record: taking off a garment that replaced other
	// slots (a full dress) must bring their defaults back, and the remaining equipped
	// set decides which body regions stay collapsed.
	ApplyWardrobeState();
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::GetSlotComponent(const EMelodiaWardrobeSlot Slot) const
{
	const TObjectPtr<USkeletalMeshComponent>* Found = SlotComponents.Find(Slot);
	return Found ? Found->Get() : nullptr;
}

bool UMelodiaWardrobeComponent::IsSlotEquipped(const EMelodiaWardrobeSlot Slot) const
{
	const USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot);
	return SlotComp && SlotComp->IsVisible() && SlotComp->GetSkeletalMeshAsset();
}

bool UMelodiaWardrobeComponent::IsSlotShowingMesh(
	const EMelodiaWardrobeSlot Slot, const USkeletalMesh* ExpectedMesh) const
{
	const USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot);
	return ExpectedMesh
		&& SlotComp
		&& SlotComp->IsVisible()
		&& SlotComp->GetSkeletalMeshAsset() == ExpectedMesh;
}

void UMelodiaWardrobeComponent::SetSlotMaterial(const EMelodiaWardrobeSlot Slot, const int32 MaterialIndex, UMaterialInterface* Material)
{
	if (USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot))
	{
		SlotComp->SetMaterial(MaterialIndex, Material);
	}
}

void UMelodiaWardrobeComponent::ApplyBodyRegionVisibility()
{
	USkeletalMeshComponent* BodyMesh = GetBodyMesh();
	const USkeletalMesh* BodyAsset = BodyMesh ? BodyMesh->GetSkeletalMeshAsset() : nullptr;
	if (!BodyMesh || !BodyAsset)
	{
		return;
	}

	UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (!Wardrobe)
	{
		return;
	}

	// Derive at call time from the equipped map (the authority); this component
	// only remembers what IT set last, so an unequip re-expands exactly what it
	// collapsed and nothing more.
	TSet<FName> DesiredHides;
	{
		const TArray<FName> Regions = Wardrobe->GetHiddenBodyRegions();
		DesiredHides.Reserve(Regions.Num());
		for (const FName Region : Regions)
		{
			DesiredHides.Add(Region);
		}
	}

	// Re-expand regions this component previously collapsed that the new equipped
	// set no longer covers. Only touch morphs we set -- a designer-authored
	// corrective morph on the same mesh is not ours to reset.
	for (const FName PreviouslyHidden : AppliedBodyRegionHides)
	{
		if (!DesiredHides.Contains(PreviouslyHidden))
		{
			BodyMesh->SetMorphTarget(PreviouslyHidden, 0.0f);
		}
	}

	for (const FName Region : DesiredHides)
	{
		// Presence check, not a guess: FindMorphTarget returns null when the body
		// mesh has not been re-authored with this region's hide morph yet.
		// That is an authoring-lag condition (region declared, morph pending), so
		// it degrades to "no collapse" -- never to a section-index hack.
		// (USkeletalMesh has no GetMorphTargetIndex in UE 5.8; the members are
		// FindMorphTarget / FindMorphTargetAndIndex, SkeletalMesh.h:2757-2758.)
		if (BodyAsset->FindMorphTarget(Region) == nullptr)
		{
			if (!WarnedMissingBodyRegionMorphs.Contains(Region))
			{
				WarnedMissingBodyRegionMorphs.Add(Region);
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE_CLIP body mesh %s has no region-hide morph '%s' yet; "
						 "region declared by the equipped set stays visible until the morph is authored."),
					*GetNameSafe(BodyAsset), *Region.ToString());
			}
			continue;
		}
		BodyMesh->SetMorphTarget(Region, 1.0f);
	}

	AppliedBodyRegionHides = DesiredHides;
}
