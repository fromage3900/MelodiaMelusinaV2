#include "PCGControlLivePreviewComponent.h"

#include "Components/ActorComponent.h"
#include "EngineUtils.h"
#include "Misc/Crc.h"
#include "PCGComponent.h"
#include "PCGGraph.h"
#include "UObject/UnrealType.h"

namespace PCGControlLivePreviewPrivate
{
	static const FName ControlProperties[] = {
		TEXT("Depth"),
		TEXT("Density"),
		TEXT("WalkWidth"),
		TEXT("ArrayCount"),
		TEXT("ArraySpacing"),
		TEXT("ResampleSpacing"),
		TEXT("ScaleMin"),
		TEXT("ScaleMax"),
		TEXT("CullDistance"),
		TEXT("StencilValue"),
		TEXT("WriteCustomDepth"),
	};
}

UPCGControlLivePreviewComponent::UPCGControlLivePreviewComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_DuringPhysics;
#if WITH_EDITOR
	bTickInEditor = true;
#endif
}

void UPCGControlLivePreviewComponent::BeginPlay()
{
	Super::BeginPlay();
	LastControlFingerprint = BuildControlFingerprint();
	TimeSinceChange = 0.0f;
}

void UPCGControlLivePreviewComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	#if WITH_EDITOR
	if (GIsEditor && !bTickInEditorPreview)
	{
		return;
	}
	#endif
	if (!bEnabled || !GetOwner())
	{
		return;
	}

	TimeSinceChange += FMath::Max(0.0f, DeltaTime);
	const uint32 Fingerprint = BuildControlFingerprint();
	if (Fingerprint != LastControlFingerprint)
	{
		LastControlFingerprint = Fingerprint;
		TimeSinceChange = 0.0f;
		bRegenerationPending = true;
	}

	if (bRegenerationPending && TimeSinceChange >= FMath::Max(0.05f, ChangeDebounceSeconds))
	{
		DiscoverAndRegenerate();
		bRegenerationPending = false;
		TimeSinceChange = 0.0f;
	}
}

void UPCGControlLivePreviewComponent::RequestRegeneration()
{
	if (!bEnabled)
	{
		return;
	}
	bRegenerationPending = true;
	TimeSinceChange = FMath::Max(0.0f, ChangeDebounceSeconds);
}

void UPCGControlLivePreviewComponent::SetLivePreviewEnabled(const bool bInEnabled)
{
	bEnabled = bInEnabled;
	if (bEnabled)
	{
		LastControlFingerprint = BuildControlFingerprint();
		RequestRegeneration();
	}
	else
	{
		bRegenerationPending = false;
	}
}

uint32 UPCGControlLivePreviewComponent::BuildControlFingerprint() const
{
	const AActor* Owner = GetOwner();
	if (!Owner)
	{
		return 0;
	}

	uint32 Hash = 0;
	for (const FName PropertyName : PCGControlLivePreviewPrivate::ControlProperties)
	{
		const FProperty* Property = FindFProperty<FProperty>(Owner->GetClass(), PropertyName);
		if (!Property)
		{
			continue;
		}
		const void* ValueAddress = Property->ContainerPtrToValuePtr<void>(Owner);
		Hash = HashCombine(Hash, GetTypeHash(PropertyName));
		Hash = HashCombine(Hash, GetTypeHash(Property->GetCPPType()));
		Hash = HashCombine(Hash, FCrc::MemCrc32(ValueAddress, Property->GetSize()));
	}
	return Hash;
}

bool UPCGControlLivePreviewComponent::IsGraphAllowed(const UPCGComponent* Component) const
{
	if (!Component || !Component->GetGraph())
	{
		return false;
	}
	return GraphNameFilter.IsEmpty() || Component->GetGraph()->GetName().Contains(GraphNameFilter);
}

void UPCGControlLivePreviewComponent::DiscoverAndRegenerate()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	TArray<UPCGComponent*> Candidates;
	for (const TObjectPtr<UPCGComponent>& Target : TargetComponents)
	{
		if (Target && IsGraphAllowed(Target))
		{
			Candidates.AddUnique(Target.Get());
		}
	}

	if (Candidates.Num() == 0)
	{
		const FVector Origin = GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Actor = *It;
			if (!Actor || (DiscoveryRadius > 0.0f && FVector::DistSquared(Origin, Actor->GetActorLocation()) > FMath::Square(DiscoveryRadius)))
			{
				continue;
			}
			TArray<UPCGComponent*> Components;
			Actor->GetComponents<UPCGComponent>(Components);
			for (UPCGComponent* Component : Components)
			{
				if (IsGraphAllowed(Component))
				{
					Candidates.AddUnique(Component);
				}
			}
		}
	}

	LastRegeneratedComponentCount = 0;
	for (UPCGComponent* Component : Candidates)
	{
		if (Component)
		{
			Component->Generate(true);
			++LastRegeneratedComponentCount;
		}
	}
}
