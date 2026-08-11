#include "MelodiaWaterFluidZoneComponent.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "WaterBodyComponent.h"

UMelodiaWaterFluidZoneComponent::UMelodiaWaterFluidZoneComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
}

void UMelodiaWaterFluidZoneComponent::BeginPlay()
{
	Super::BeginPlay();

	GridResolution.X = FMath::Clamp(GridResolution.X, 4, 128);
	GridResolution.Y = FMath::Clamp(GridResolution.Y, 4, 128);
	FixedStepSeconds = FMath::Clamp(FixedStepSeconds, 0.001f, 0.1f);
	MaxSubstepsPerFrame = FMath::Clamp(MaxSubstepsPerFrame, 1, 4);
	WaveSpeed = FMath::Clamp(WaveSpeed, 0.1f, 50.0f);
	HeightDamping = FMath::Clamp(HeightDamping, 0.0f, 10.0f);
	MaxHeight = FMath::Max(0.0f, MaxHeight);
	ImpulseGain = FMath::Max(0.0f, ImpulseGain);
	Heights.SetNumZeroed(GridResolution.X * GridResolution.Y);
	Velocities.SetNumZeroed(Heights.Num());

	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
		if (WaterSubsystem)
		{
			WaterSubsystem->OnFluidImpulse.AddUniqueDynamic(this, &ThisClass::HandleFluidImpulse);
		}
	}

	UpdateTelemetry();
}

void UMelodiaWaterFluidZoneComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (WaterSubsystem)
	{
		WaterSubsystem->OnFluidImpulse.RemoveDynamic(this, &ThisClass::HandleFluidImpulse);
	}
	WaterSubsystem = nullptr;
	Heights.Reset();
	Velocities.Reset();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterFluidZoneComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!bEnabled || Heights.Num() == 0)
	{
		return;
	}

	Accumulator = FMath::Min(Accumulator + FMath::Max(0.0f, DeltaTime), FixedStepSeconds * MaxSubstepsPerFrame);
	int32 Substeps = 0;
	while (Accumulator >= FixedStepSeconds && Substeps < MaxSubstepsPerFrame)
	{
		StepSimulation(FixedStepSeconds);
		Accumulator -= FixedStepSeconds;
		++Substeps;
	}

	UpdateTelemetry();
	if (bWriteMaterialTelemetry)
	{
		WriteMaterialTelemetry();
	}
}

void UMelodiaWaterFluidZoneComponent::ResetSimulation()
{
	Heights.SetNumZeroed(GridResolution.X * GridResolution.Y);
	Velocities.SetNumZeroed(Heights.Num());
	Accumulator = 0.0f;
	UpdateTelemetry();
	WriteMaterialTelemetry();
}

float UMelodiaWaterFluidZoneComponent::GetHeightAtWorldLocation(const FVector& WorldLocation) const
{
	int32 X = 0;
	int32 Y = 0;
	if (!WorldToCell(WorldLocation, X, Y))
	{
		return 0.0f;
	}
	return Heights.IsValidIndex(GetCellIndex(X, Y)) ? Heights[GetCellIndex(X, Y)] : 0.0f;
}

void UMelodiaWaterFluidZoneComponent::HandleFluidImpulse(FMelodiaWaterFluidImpulse Impulse)
{
	if (!bEnabled || !AcceptsTier(Impulse.RequestedTier))
	{
		return;
	}
	if (!WaterBodyId.IsNone() && !Impulse.WaterBodyId.IsNone() && WaterBodyId != Impulse.WaterBodyId)
	{
		return;
	}

	int32 CenterX = 0;
	int32 CenterY = 0;
	if (!WorldToCell(Impulse.Location, CenterX, CenterY))
	{
		return;
	}

	const FVector LocalImpulse = GetOwner() ? GetOwner()->GetActorTransform().InverseTransformVectorNoScale(Impulse.Impulse) : Impulse.Impulse;
	const float RadiusCm = FMath::Max(1.0f, Impulse.Radius);
	const float CellWidth = (LocalHalfExtent.X * 2.0f) / FMath::Max(1, GridResolution.X);
	const float CellHeight = (LocalHalfExtent.Y * 2.0f) / FMath::Max(1, GridResolution.Y);
	const int32 RadiusX = FMath::Max(1, FMath::CeilToInt(RadiusCm / FMath::Max(1.0f, CellWidth)));
	const int32 RadiusY = FMath::Max(1, FMath::CeilToInt(RadiusCm / FMath::Max(1.0f, CellHeight)));

	for (int32 Y = CenterY - RadiusY; Y <= CenterY + RadiusY; ++Y)
	{
		for (int32 X = CenterX - RadiusX; X <= CenterX + RadiusX; ++X)
		{
			if (X < 0 || X >= GridResolution.X || Y < 0 || Y >= GridResolution.Y)
			{
				continue;
			}

			const float Dx = static_cast<float>(X - CenterX) / static_cast<float>(RadiusX);
			const float Dy = static_cast<float>(Y - CenterY) / static_cast<float>(RadiusY);
			const float Weight = FMath::Exp(-2.5f * (Dx * Dx + Dy * Dy));
			const int32 Index = GetCellIndex(X, Y);
			const float SignedImpulse = (LocalImpulse.Z * 0.01f) + (Impulse.Strength * 10.0f);
			Heights[Index] = FMath::Clamp(Heights[Index] + SignedImpulse * Weight * ImpulseGain, -MaxHeight, MaxHeight);
			Velocities[Index] += (LocalImpulse.Z * 0.005f + Impulse.Strength) * Weight * ImpulseGain;
		}
	}
}

int32 UMelodiaWaterFluidZoneComponent::GetCellIndex(int32 X, int32 Y) const
{
	return Y * GridResolution.X + X;
}

bool UMelodiaWaterFluidZoneComponent::WorldToCell(const FVector& WorldLocation, int32& OutX, int32& OutY) const
{
	if (!GetOwner() || GridResolution.X <= 0 || GridResolution.Y <= 0)
	{
		return false;
	}

	const FVector LocalLocation = GetOwner()->GetActorTransform().InverseTransformPosition(WorldLocation);
	const float NormalizedX = (LocalLocation.X + LocalHalfExtent.X) / FMath::Max(1.0f, LocalHalfExtent.X * 2.0f);
	const float NormalizedY = (LocalLocation.Y + LocalHalfExtent.Y) / FMath::Max(1.0f, LocalHalfExtent.Y * 2.0f);
	if (NormalizedX < 0.0f || NormalizedX > 1.0f || NormalizedY < 0.0f || NormalizedY > 1.0f)
	{
		return false;
	}

	OutX = FMath::Clamp(FMath::FloorToInt(NormalizedX * GridResolution.X), 0, GridResolution.X - 1);
	OutY = FMath::Clamp(FMath::FloorToInt(NormalizedY * GridResolution.Y), 0, GridResolution.Y - 1);
	return true;
}

FVector UMelodiaWaterFluidZoneComponent::CellToWorld(int32 X, int32 Y) const
{
	const float U = (static_cast<float>(X) + 0.5f) / static_cast<float>(FMath::Max(1, GridResolution.X));
	const float V = (static_cast<float>(Y) + 0.5f) / static_cast<float>(FMath::Max(1, GridResolution.Y));
	const FVector LocalLocation(
		FMath::Lerp(-LocalHalfExtent.X, LocalHalfExtent.X, U),
		FMath::Lerp(-LocalHalfExtent.Y, LocalHalfExtent.Y, V),
		0.0f);
	return GetOwner() ? GetOwner()->GetActorTransform().TransformPosition(LocalLocation) : LocalLocation;
}

void UMelodiaWaterFluidZoneComponent::StepSimulation(float StepSeconds)
{
	if (GridResolution.X < 2 || GridResolution.Y < 2)
	{
		return;
	}

	TArray<float> NextVelocities = Velocities;
	const float WaveAcceleration = WaveSpeed * WaveSpeed;
	for (int32 Y = 0; Y < GridResolution.Y; ++Y)
	{
		for (int32 X = 0; X < GridResolution.X; ++X)
		{
			const int32 Index = GetCellIndex(X, Y);
			const int32 Left = GetCellIndex(FMath::Max(0, X - 1), Y);
			const int32 Right = GetCellIndex(FMath::Min(GridResolution.X - 1, X + 1), Y);
			const int32 Down = GetCellIndex(X, FMath::Max(0, Y - 1));
			const int32 Up = GetCellIndex(X, FMath::Min(GridResolution.Y - 1, Y + 1));
			const float Laplacian = Heights[Left] + Heights[Right] + Heights[Down] + Heights[Up] - (4.0f * Heights[Index]);
			const float DampedVelocity = Velocities[Index] * FMath::Exp(-HeightDamping * StepSeconds);
			NextVelocities[Index] = DampedVelocity + (Laplacian * WaveAcceleration * StepSeconds);
		}
	}

	for (int32 Index = 0; Index < Heights.Num(); ++Index)
	{
		Velocities[Index] = NextVelocities[Index];
		Heights[Index] = FMath::Clamp(Heights[Index] + Velocities[Index] * StepSeconds, -MaxHeight, MaxHeight);
	}
}

void UMelodiaWaterFluidZoneComponent::UpdateTelemetry()
{
	float Energy = 0.0f;
	PeakHeight = 0.0f;
	int32 StrongestIndex = INDEX_NONE;
	for (int32 Index = 0; Index < Heights.Num(); ++Index)
	{
		Energy += FMath::Abs(Heights[Index]) + (FMath::Abs(Velocities[Index]) * 0.1f);
		if (FMath::Abs(Heights[Index]) > PeakHeight)
		{
			PeakHeight = FMath::Abs(Heights[Index]);
			StrongestIndex = Index;
		}
	}

	const float MaxPossibleEnergy = FMath::Max(1.0f, static_cast<float>(Heights.Num()) * MaxHeight);
	NormalizedEnergy = FMath::Clamp(Energy / MaxPossibleEnergy, 0.0f, 1.0f);
	if (StrongestIndex != INDEX_NONE)
	{
		StrongestWorldLocation = CellToWorld(StrongestIndex % GridResolution.X, StrongestIndex / GridResolution.X);
	}
}

void UMelodiaWaterFluidZoneComponent::WriteMaterialTelemetry()
{
	if (!GetOwner())
	{
		return;
	}

	if (UWaterBodyComponent* WaterBodyComponent = GetOwner()->FindComponentByClass<UWaterBodyComponent>())
	{
		if (UMaterialInstanceDynamic* WaterMaterial = WaterBodyComponent->GetWaterMaterialInstance())
		{
			WaterMaterial->SetScalarParameterValue(FluidEnergyParameter, NormalizedEnergy);
			WaterMaterial->SetScalarParameterValue(FluidPeakParameter, PeakHeight);
			WaterMaterial->SetVectorParameterValue(FluidCenterParameter, FLinearColor(StrongestWorldLocation.X, StrongestWorldLocation.Y, StrongestWorldLocation.Z, 1.0f));
		}
	}
}

bool UMelodiaWaterFluidZoneComponent::AcceptsTier(EMelodiaWaterSimulationTier RequestedTier) const
{
	return bAllowTierDowngrade || static_cast<uint8>(RequestedTier) <= static_cast<uint8>(SimulationTier);
}
