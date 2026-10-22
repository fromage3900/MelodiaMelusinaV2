#include "MelodiaDressingSubsystem.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "MelodiaDressingCatalog.h"
#include "PhysicalMaterials/PhysicalMaterial.h"

namespace MelodiaDressing
{
	/** The tag every actor this pass places carries, so a later pass can find them. */
	static const FName ArtPassTag(TEXT("MelodiaArtPass"));

	/** Golden angle in radians - spreads placed props evenly without clumping. */
	static constexpr float GoldenAngle = 2.39996323f;

	/** How far from the focus the first prop lands, in cm. */
	static constexpr float FirstRingRadius = 120.f;

	/** How much further out each successive prop lands, in cm. */
	static constexpr float RingStep = 28.f;

	/** How high above the focus a prop is spawned before it is dropped, in cm. */
	static constexpr float SpawnLift = 35.f;
}

bool UMelodiaDressingSubsystem::DressHeroClutter(AActor* CameraFocus, const FName& FamilyTag, const int32 Count)
{
	if (!CameraFocus || Count <= 0)
	{
		return false;
	}

	const UMelodiaDressingCatalog* Catalog = LoadDressingCatalog();
	if (!Catalog)
	{
		UE_LOG(LogTemp, Log, TEXT("[Dressing] no catalogue at %s - nothing placed"),
			*GetDressingCatalogPath().ToString());
		return false;
	}

	const FMelodiaDressingFamily* Family = Catalog->FindFamilyByArtistTag(FamilyTag);
	if (!Family)
	{
		UE_LOG(LogTemp, Log, TEXT("[Dressing] unknown family '%s' (the catalogue holds %d families)"),
			*FamilyTag.ToString(), Catalog->FamilyCount());
		return false;
	}

	UWorld* World = CameraFocus->GetWorld();
	if (!World)
	{
		return false;
	}

	ActiveFamily = FamilyTag;

	const FVector FocusLocation = CameraFocus->GetActorLocation();
	TArray<AActor*> ToSettle;

	int32 Placed = 0;
	int32 Index = 0;
	for (const FMelodiaDressingProp& Prop : Family->Props)
	{
		if (Placed >= Count)
		{
			break;
		}
		UStaticMesh* Mesh = Prop.Mesh.LoadSynchronous();
		if (!Mesh)
		{
			continue;
		}
		UMaterialInterface* Material = Prop.MaterialOverride.LoadSynchronous();

		for (int32 Copy = 0; Copy < Prop.Count && Placed < Count; ++Copy, ++Index)
		{
			const float Radius = MelodiaDressing::FirstRingRadius + MelodiaDressing::RingStep * Index;
			const float Angle = Index * MelodiaDressing::GoldenAngle;
			const FVector Location = FocusLocation + FVector(
				Radius * FMath::Cos(Angle),
				Radius * FMath::Sin(Angle),
				MelodiaDressing::SpawnLift);

			FActorSpawnParameters SpawnParameters;
			SpawnParameters.SpawnCollisionHandlingOverride =
				ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
			SpawnParameters.ObjectFlags |= RF_Transient;

			AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
				AStaticMeshActor::StaticClass(), Location, FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f),
				SpawnParameters);
			if (!Actor)
			{
				continue;
			}

			Actor->Tags.AddUnique(MelodiaDressing::ArtPassTag);
			Actor->Tags.AddUnique(Family->ArtistTag);
			Actor->Tags.AddUnique(Prop.PropTag);

			if (UStaticMeshComponent* Component = Actor->GetStaticMeshComponent())
			{
				Component->SetMobility(EComponentMobility::Movable);
				Component->SetStaticMesh(Mesh);
				if (Material)
				{
					Component->SetMaterial(0, Material);
				}
			}

			if (Prop.bSettlesUnderGravity)
			{
				ToSettle.Add(Actor);
			}
			++Placed;
		}
	}

	// The settling props are dropped, not posed.
	if (ToSettle.Num() > 0)
	{
		PhysicallyDrop(ToSettle, FVector::ZeroVector, 0.25f);
	}

	UE_LOG(LogTemp, Log, TEXT("[Dressing] DressHeroClutter family=%s placed=%d (of %d requested, %d settling) around %s"),
		*FamilyTag.ToString(), Placed, Count, ToSettle.Num(), *CameraFocus->GetName());
	return Placed > 0;
}

bool UMelodiaDressingSubsystem::PhysicallyDrop(const TArray<AActor*>& Actors, const FVector DropOffset, const float Restitution)
{
	if (Actors.Num() == 0)
	{
		return false;
	}

	// One transient physical material carries the restitution for every dropped
	// body. It is never written to Content - it is a runtime override.
	UPhysicalMaterial* PhysicalMaterial = NewObject<UPhysicalMaterial>(GetTransientPackage());
	if (PhysicalMaterial)
	{
		PhysicalMaterial->Restitution = FMath::Clamp(Restitution, 0.f, 1.f);
	}

	int32 Dropped = 0;
	for (AActor* Actor : Actors)
	{
		if (!Actor)
		{
			continue;
		}
		UPrimitiveComponent* Root = Cast<UPrimitiveComponent>(Actor->GetRootComponent());
		if (!Root)
		{
			continue;
		}

		Root->SetMobility(EComponentMobility::Movable);
		if (PhysicalMaterial)
		{
			Root->SetPhysMaterialOverride(PhysicalMaterial);
		}
		Root->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Root->SetSimulatePhysics(true);
		Root->SetPhysicsLinearVelocity(FVector::ZeroVector);
		Root->SetPhysicsAngularVelocityInDegrees(FVector::ZeroVector);

		if (!DropOffset.IsNearlyZero())
		{
			Actor->AddActorWorldOffset(DropOffset, false, nullptr, ETeleportType::TeleportPhysics);
		}
		++Dropped;
	}

	UE_LOG(LogTemp, Log, TEXT("[Dressing] PhysicallyDrop dropped=%d of %d offset=%s restitution=%.2f"),
		Dropped, Actors.Num(), *DropOffset.ToString(), Restitution);
	return Dropped > 0;
}

TArray<AActor*> UMelodiaDressingSubsystem::FindCompositionOccluders(AActor* CameraFocus, const float Radius, const int32 MaxReports)
{
	TArray<AActor*> Out;
	if (!CameraFocus || MaxReports <= 0 || Radius <= 0.f)
	{
		return Out;
	}
	UWorld* World = CameraFocus->GetWorld();
	if (!World)
	{
		return Out;
	}

	const FVector Origin = CameraFocus->GetActorLocation();
	const FVector Forward = CameraFocus->GetActorForwardVector();
	// The framing cone: 45 degrees either side of the focus's forward axis.
	const float CosHalfAngle = FMath::Cos(FMath::DegreesToRadians(45.f));

	for (TActorIterator<AActor> It(World); It && Out.Num() < MaxReports; ++It)
	{
		AActor* Other = *It;
		if (!Other || Other == CameraFocus)
		{
			continue;
		}
		// Only props can occlude a frame: world settings, lights, volumes and
		// the artist's own interactables are not dressing.
		if (!Other->GetClass()->IsChildOf(AStaticMeshActor::StaticClass()))
		{
			continue;
		}

		const FVector To = Other->GetActorLocation() - Origin;
		const float Distance = To.Size();
		if (Distance > Radius || Distance < KINDA_SMALL_NUMBER)
		{
			continue;
		}
		if (FVector::DotProduct(To / Distance, Forward) < CosHalfAngle)
		{
			continue;
		}
		Out.Add(Other);
	}

	UE_LOG(LogTemp, Log, TEXT("[Dressing] FindCompositionOccluders radius=%.1f reported=%d (report only - nothing was moved)"),
		Radius, Out.Num());
	return Out;
}

FSoftObjectPath UMelodiaDressingSubsystem::GetDressingCatalogPath() const
{
	// The hero-prop dressing catalog (DataAsset keyed by FGameplayTag family).
	// Not invented on disk yet - the class is UMelodiaDressingCatalog and the
	// content is specs/p0/melusina_dressing_catalog.v1.json.
	// Guardrail: no Content/_PROJECT/ writes.
	return FSoftObjectPath(TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaDressingCatalog"));
}

UMelodiaDressingCatalog* UMelodiaDressingSubsystem::LoadDressingCatalog() const
{
	const FSoftObjectPath Path = GetDressingCatalogPath();
	if (!Path.IsValid())
	{
		return nullptr;
	}
	return Cast<UMelodiaDressingCatalog>(Path.TryLoad());
}
