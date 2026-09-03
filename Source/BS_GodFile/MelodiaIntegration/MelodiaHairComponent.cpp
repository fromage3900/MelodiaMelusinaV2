#include "MelodiaHairComponent.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimBlueprintGeneratedClass.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UnrealType.h"

UMelodiaHairComponent::UMelodiaHairComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SetGenerateOverlapEvents(false);

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> HairMesh(
		TEXT("/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair.SK_MelusinaHair"));
	if (HairMesh.Succeeded())
	{
		SetSkeletalMesh(HairMesh.Object);
	}

	static ConstructorHelpers::FClassFinder<UAnimInstance> HairAnim(
		TEXT("/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"));
	if (HairAnim.Succeeded())
	{
		// Cache only. Installing the anim instance here would start the graph
		// ticking before BindToOwnerMesh() assigns its SourceMeshComponent.
		HairAnimClass = HairAnim.Class;
	}
}

void UMelodiaHairComponent::BeginPlay()
{
	Super::BeginPlay();

	// Actor components begin before their owning Blueprint's BeginPlay graph.
	// The battle adapter's graph first hides its inherited mannequin mesh and
	// then exposes MelusinaPresentationMesh through the stock SkeletalMesh
	// variable. Binding here used to redirect that variable too early, causing
	// the adapter to hide Melusina's visible body and leave only her hair.
	// Defer exactly one game-thread tick so the stock graph completes first.
	if (UWorld* World = GetWorld())
	{
		TWeakObjectPtr<UMelodiaHairComponent> WeakThis(this);
		World->GetTimerManager().SetTimerForNextTick([WeakThis]()
		{
			if (UMelodiaHairComponent* Component = WeakThis.Get())
			{
				Component->BindToOwnerMesh();
			}
		});
	}
	else
	{
		BindToOwnerMesh();
	}
}

void UMelodiaHairComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	RestoreOwnerMeshReference();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaHairComponent::OnUnregister()
{
	RestoreOwnerMeshReference();
	Super::OnUnregister();
}

void UMelodiaHairComponent::BindToOwnerMesh()
{
	AActor* Owner = GetOwner();
	ACharacter* Character = Cast<ACharacter>(Owner);
	USkeletalMeshComponent* BodyMesh = Character ? Character->GetMesh() : nullptr;
	bool bUsingPresentationMesh = false;

	// JRPG battle units retain their inherited mechanics mesh while rendering Melusina
	// through a separate presentation mesh. Prefer that mesh when present so the
	// hair copies Melusina's pose rather than the hidden mannequin's pose. Battle
	// units derive from Actor rather than Character, so this must inspect the
	// generic actor component list instead of returning early outside exploration.
	if (Owner)
	{
		TArray<USkeletalMeshComponent*> MeshComponents;
		Owner->GetComponents(MeshComponents);
		for (USkeletalMeshComponent* Candidate : MeshComponents)
		{
			if (!IsValid(Candidate) || Candidate == this)
			{
				continue;
			}
			if (IsValid(Candidate) && Candidate->GetName().Contains(TEXT("MelusinaPresentationMesh")))
			{
				BodyMesh = Candidate;
				bUsingPresentationMesh = true;
				break;
			}
			if (!BodyMesh)
			{
				BodyMesh = Candidate;
			}
		}
	}

	if (!BodyMesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaHairComponent: owner %s has no body skeletal mesh."), *GetNameSafe(GetOwner()));
		return;
	}

	// Stock JRPG skill Blueprints read the owning unit's generated `SkeletalMesh`
	// component variable when they play a montage. The presentation adapter keeps
	// that mannequin component hidden, so redirect only this instance-level reference
	// to Melusina's visible mesh. Combat logic remains entirely stock while montage
	// notifies are emitted by the visible AnimInstance.
	if (bUsingPresentationMesh)
	{
		FObjectPropertyBase* MechanicsMeshProperty =
			FindFProperty<FObjectPropertyBase>(GetOwner()->GetClass(), TEXT("SkeletalMesh"));
		if (MechanicsMeshProperty &&
			MechanicsMeshProperty->PropertyClass->IsChildOf(USkeletalMeshComponent::StaticClass()))
		{
			UObject* PreviousMesh = MechanicsMeshProperty->GetObjectPropertyValue_InContainer(GetOwner());
			if (PreviousMesh != BodyMesh)
			{
				OriginalMechanicsMesh = Cast<USkeletalMeshComponent>(PreviousMesh);
				RedirectedPresentationMesh = BodyMesh;
				MechanicsMeshProperty->SetObjectPropertyValue_InContainer(GetOwner(), BodyMesh);

				// The stock component remains alive for stock actor/component
				// contracts, but its mannequin render must not overlap Melusina.
				// Do not propagate to children: target widgets/camera anchors retain
				// their stock visibility and attachment behavior.
				if (USkeletalMeshComponent* OriginalMesh = OriginalMechanicsMesh.Get())
				{
					bOriginalMechanicsMeshWasVisible = OriginalMesh->IsVisible();
					bOriginalMechanicsMeshWasHiddenInGame = OriginalMesh->bHiddenInGame;
					OriginalMesh->SetVisibility(false, false);
					OriginalMesh->SetHiddenInGame(true, false);
				}
				UE_LOG(LogTemp, Log, TEXT("MELUSINA_JRPG_MESH_REDIRECT owner=%s from=%s to=%s"),
					*GetNameSafe(GetOwner()), *GetNameSafe(PreviousMesh), *GetNameSafe(BodyMesh));
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MelodiaHairComponent: owner %s has no compatible SkeletalMesh property to redirect."),
				*GetNameSafe(GetOwner()));
		}
	}

	// Socket the hair to the head bone, then cancel that bone's bind-pose transform.
	//
	// The hair mesh is authored in character space (origin at the character root),
	// not head space. Parenting it to head_x therefore stacks head_x's bind transform
	// on top of geometry that already accounts for it -- which is the ~3ft offset and
	// the wrong rotation: head height plus the bone's own axis convention.
	//
	// Setting the relative transform to the inverse of head_x's bind-pose
	// component-space transform cancels exactly that. At bind pose the hair lands
	// where it was authored; from then on it inherits the head's animated delta, so
	// it sticks to her head. Computed from the skeleton -- no dialled-in numbers.
	static const FName HeadBone(TEXT("head_x"));
	const int32 HeadBoneIndex = BodyMesh->GetBoneIndex(HeadBone);
	const USkeletalMesh* BodyAsset = BodyMesh->GetSkeletalMeshAsset();

	if (HeadBoneIndex != INDEX_NONE && BodyAsset)
	{
		AttachToComponent(BodyMesh, FAttachmentTransformRules::KeepRelativeTransform, HeadBone);

		const FTransform HeadBindComponentSpace(BodyAsset->GetComposedRefPoseMatrix(HeadBoneIndex));
		SetRelativeTransform(HeadBindComponentSpace.Inverse());

		UE_LOG(LogTemp, Log, TEXT("MELUSINA_HAIR_SOCKET bone=%s bind_cs_loc=%s bind_cs_rot=%s (inverse applied)"),
			*HeadBone.ToString(),
			*HeadBindComponentSpace.GetLocation().ToCompactString(),
			*HeadBindComponentSpace.GetRotation().Rotator().ToCompactString());
	}
	else
	{
		// No head bone: parent to the mesh root and leave the authored transform alone.
		AttachToComponent(BodyMesh, FAttachmentTransformRules::KeepRelativeTransform, NAME_None);
		UE_LOG(LogTemp, Warning,
			TEXT("MELUSINA_HAIR_SOCKET: body mesh %s has no 'head_x' bone; parented to mesh root instead."),
			*GetNameSafe(BodyAsset));
	}

	const FName AttachBone = (HeadBoneIndex != INDEX_NONE) ? HeadBone : NAME_None;

	SetLeaderPoseComponent(nullptr);

	// Install the AnimBP here rather than in the constructor: this is the same
	// call stack that assigns SourceMeshComponent below, so the graph never ticks
	// with a null source mesh. InitAnim(true) then instantiates it.
	if (HairAnimClass)
	{
		SetAnimationMode(EAnimationMode::AnimationBlueprint);
		SetAnimInstanceClass(HairAnimClass);
	}

	InitAnim(true);

	UAnimInstance* HairAnimInstance = GetAnimInstance();
	FObjectPropertyBase* SourceMeshProperty = HairAnimInstance
		? FindFProperty<FObjectPropertyBase>(HairAnimInstance->GetClass(), TEXT("SourceMeshComponent"))
		: nullptr;
	if (!SourceMeshProperty)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaHairComponent: hair AnimBP is missing SourceMeshComponent."));
		return;
	}

	SourceMeshProperty->SetObjectPropertyValue_InContainer(HairAnimInstance, BodyMesh);

	UE_LOG(LogTemp, Log,
		TEXT("MELUSINA_HAIR_BOUND owner=%s body_comp=%s hair_comp=%s anim=%s attach_bone=%s"),
		*GetNameSafe(GetOwner()), *BodyMesh->GetName(), *GetName(),
		*GetNameSafe(HairAnimInstance->GetClass()), *AttachBone.ToString());
}

void UMelodiaHairComponent::RestoreOwnerMeshReference()
{
	AActor* Owner = GetOwner();
	USkeletalMeshComponent* OriginalMesh = OriginalMechanicsMesh.Get();
	USkeletalMeshComponent* PresentationMesh = RedirectedPresentationMesh.Get();
	if (!IsValid(Owner) || !IsValid(OriginalMesh) || !IsValid(PresentationMesh))
	{
		return;
	}

	FObjectPropertyBase* MechanicsMeshProperty =
		FindFProperty<FObjectPropertyBase>(Owner->GetClass(), TEXT("SkeletalMesh"));
	if (!MechanicsMeshProperty ||
		!MechanicsMeshProperty->PropertyClass->IsChildOf(USkeletalMeshComponent::StaticClass()))
	{
		return;
	}

	if (MechanicsMeshProperty->GetObjectPropertyValue_InContainer(Owner) == PresentationMesh)
	{
		MechanicsMeshProperty->SetObjectPropertyValue_InContainer(Owner, OriginalMesh);
		OriginalMesh->SetVisibility(bOriginalMechanicsMeshWasVisible, false);
		OriginalMesh->SetHiddenInGame(bOriginalMechanicsMeshWasHiddenInGame, false);
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_JRPG_MESH_RESTORE owner=%s to=%s"),
			*GetNameSafe(Owner), *GetNameSafe(OriginalMesh));
	}

	OriginalMechanicsMesh.Reset();
	RedirectedPresentationMesh.Reset();
	bOriginalMechanicsMeshWasVisible = true;
	bOriginalMechanicsMeshWasHiddenInGame = false;
}
