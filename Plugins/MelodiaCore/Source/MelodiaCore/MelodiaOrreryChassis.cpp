#include "MelodiaOrreryChassis.h"

#include "Blueprint/UserWidget.h"
#include "Components/Image.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// Beat-locked keys on the 128 BPM timeline (ms): latch = 1/8, bloom = 2/8, ignite = 1 beat, settle = 1.5 beats.
	constexpr float LatchMs = 117.0f;
	constexpr float BloomMs = 234.0f;
	constexpr float IgniteMs = 469.0f;
	constexpr float SettleMs = 703.0f;
	constexpr float CloseSpeed = 3.0f;
	constexpr float RingRadiusStep = 0.35f;
	const float RingTiltDegrees[] = {0.0f, 62.0f, -38.0f, 24.0f, -70.0f};

	float Ease(float X)
	{
		X = FMath::Clamp(X, 0.0f, 1.0f);
		return X * X * (3.0f - 2.0f * X);
	}

	float Bump(float T, float A, float B)
	{
		return FMath::Sin(PI * FMath::Clamp((T - A) / (B - A), 0.0f, 1.0f));
	}
}

AMelodiaOrreryChassis::AMelodiaOrreryChassis()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Core = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Core"));
	Core->SetupAttachment(Root);

	Backdrop = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Backdrop"));
	Backdrop->SetupAttachment(Root);
	Backdrop->SetRelativeLocation(FVector(-80.0f, 0.0f, 0.0f));
	Backdrop->SetRelativeRotation(FRotator(-90.0f, 0.0f, 0.0f));
	Backdrop->SetRelativeScale3D(FVector(4.0f));

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(150.0f, 60.0f, 80.0f));
	Light->SetIntensity(20000.0f);
	Light->SetAttenuationRadius(600.0f);

	Capture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("Capture"));
	Capture->SetupAttachment(Root);
	Capture->SetRelativeLocation(FVector(330.0f, 0.0f, 0.0f));
	Capture->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
	Capture->FOVAngle = 40.0f;
	Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	Capture->bCaptureEveryFrame = false;
	Capture->bCaptureOnMovement = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> RingFinder(TEXT("/Game/Melodia/UI/Orrery/Meshes/SM_OrreryRing.SM_OrreryRing"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> PetalFinder(TEXT("/Game/Melodia/UI/Orrery/Meshes/SM_OrreryPetal.SM_OrreryPetal"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CoreFinder(TEXT("/Game/Melodia/UI/Orrery/Meshes/SM_OrreryCore.SM_OrreryCore"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneFinder(TEXT("/Engine/BasicShapes/Plane.Plane"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> RingMatFinder(TEXT("/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Brass_FiligreeGold.MI_Brass_FiligreeGold"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> PetalMatFinder(TEXT("/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_Melusina_BaroqueTiara_RoseGoldFiligree.MI_T_Melusina_BaroqueTiara_RoseGoldFiligree"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> NebulaFinder(TEXT("/Game/EnvSandbox/Materials/Instances/Environment/Magical/MI_Universal_CelestialNebula.MI_Universal_CelestialNebula"));
	RingMesh = RingFinder.Object;
	PetalMesh = PetalFinder.Object;
	CoreMesh = CoreFinder.Object;
	RingMaterial = RingMatFinder.Object;
	PetalMaterial = PetalMatFinder.Object;
	CoreMaterial = NebulaFinder.Object;
	BackdropMaterial = NebulaFinder.Object;
	Core->SetStaticMesh(CoreMesh);
	Backdrop->SetStaticMesh(PlaneFinder.Object);
}

void AMelodiaOrreryChassis::BuildParts()
{
	for (UStaticMeshComponent* Ring : Rings) { if (Ring) { Ring->DestroyComponent(); } }
	for (USceneComponent* Pivot : PetalPivots) { if (Pivot) { Pivot->DestroyComponent(); } }
	Rings.Reset();
	PetalPivots.Reset();
	Petals.Reset();

	Core->SetStaticMesh(CoreMesh);
	Core->SetMaterial(0, CoreMaterial);
	Backdrop->SetMaterial(0, BackdropMaterial);

	for (int32 Index = 0; Index < RingCount; ++Index)
	{
		UStaticMeshComponent* Ring = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transient);
		Ring->SetStaticMesh(RingMesh);
		Ring->SetMaterial(0, RingMaterial);
		Ring->SetupAttachment(Root);
		Ring->RegisterComponent();
		Rings.Add(Ring);
	}
	for (int32 Index = 0; Index < PetalCount; ++Index)
	{
		USceneComponent* Pivot = NewObject<USceneComponent>(this, NAME_None, RF_Transient);
		Pivot->SetupAttachment(Root);
		Pivot->SetRelativeRotation(FRotator(0.0f, 0.0f, Index * 360.0f / PetalCount));
		Pivot->RegisterComponent();
		UStaticMeshComponent* Petal = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transient);
		Petal->SetStaticMesh(PetalMesh);
		Petal->SetMaterial(0, PetalMaterial);
		Petal->SetupAttachment(Pivot);
		Petal->SetRelativeLocation(FVector(0.0f, 10.0f, 0.0f));
		Petal->RegisterComponent();
		PetalPivots.Add(Pivot);
		Petals.Add(Petal);
	}
}

void AMelodiaOrreryChassis::BeginPlay()
{
	Super::BeginPlay();
	BuildParts();
	Palette = LoadObject<UMaterialParameterCollection>(nullptr,
		TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"));

	RenderTarget = UKismetRenderingLibrary::CreateRenderTarget2D(this, RenderTargetSize, RenderTargetSize, RTF_RGBA8);
	Capture->TextureTarget = RenderTarget;
	Capture->ShowOnlyActors.Reset();
	Capture->ShowOnlyActors.Add(this);
	BaseLightIntensity = Light->Intensity;

	TimelineMs = 0.0f;
	ApplyPose(0.0f, 0.0f);
	SetActorHiddenInGame(true);
}

void AMelodiaOrreryChassis::Open()
{
	bOpening = true;
	bWaitingForBeat = true;
	BeatWait = 0.0f;
	LastBeatPhase = ReadBeatPhase();
	SetActorHiddenInGame(false);
	Capture->bCaptureEveryFrame = true;
}

AMelodiaOrreryChassis* AMelodiaOrreryChassis::ShowInWidget(UObject* WorldContextObject, UUserWidget* Widget, FName ImageName)
{
	UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	UImage* Image = Widget ? Cast<UImage>(Widget->GetWidgetFromName(ImageName)) : nullptr;
	if (!World || !Image)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_ORRERY_UNFOLD no image '%s' on widget"), *ImageName.ToString());
		return nullptr;
	}
	AMelodiaOrreryChassis* Chassis = nullptr;
	for (TActorIterator<AMelodiaOrreryChassis> It(World); It; ++It)
	{
		Chassis = *It;
		break;
	}
	if (!Chassis)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Chassis = World->SpawnActor<AMelodiaOrreryChassis>(FVector(0.0f, 0.0f, -20000.0f), FRotator::ZeroRotator, Params);
	}
	if (Chassis)
	{
		Image->SetBrushResourceObject(Chassis->GetRenderTarget());
		Chassis->Open();
	}
	return Chassis;
}

void AMelodiaOrreryChassis::CloseAll(UObject* WorldContextObject)
{
	if (UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr)
	{
		for (TActorIterator<AMelodiaOrreryChassis> It(World); It; ++It)
		{
			It->Close();
		}
	}
}

void AMelodiaOrreryChassis::Close()
{
	bOpening = false;
	bWaitingForBeat = false;
}

float AMelodiaOrreryChassis::ReadBeatPhase() const
{
	return Palette ? UKismetMaterialLibrary::GetScalarParameterValue(const_cast<AMelodiaOrreryChassis*>(this), Palette, TEXT("BeatPhase")) : 0.0f;
}

void AMelodiaOrreryChassis::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bWaitingForBeat)
	{
		const float Phase = ReadBeatPhase();
		BeatWait += DeltaSeconds;
		if (Phase < LastBeatPhase || BeatWait >= MaxBeatWaitSeconds)
		{
			bWaitingForBeat = false;
			UE_LOG(LogTemp, Log, TEXT("MELODIA_ORRERY_UNFOLD start wait=%.3fs"), BeatWait);
		}
		LastBeatPhase = Phase;
		ApplyPose(TimelineMs, DeltaSeconds);
		return;
	}

	const float MsPerSecond = 1000.0f * FMath::Max(BPM, 1.0f) / 128.0f;
	if (bOpening)
	{
		TimelineMs = FMath::Min(TimelineMs + DeltaSeconds * MsPerSecond, SettleMs);
	}
	else if (TimelineMs > 0.0f)
	{
		TimelineMs = FMath::Max(TimelineMs - DeltaSeconds * MsPerSecond * CloseSpeed, 0.0f);
		if (TimelineMs <= 0.0f)
		{
			Capture->bCaptureEveryFrame = false;
			SetActorHiddenInGame(true);
		}
	}
	ApplyPose(TimelineMs, DeltaSeconds);
}

void AMelodiaOrreryChassis::ApplyPose(float Ms, float DeltaSeconds)
{
	const float CoreT = Ease(Ms / LatchMs);
	const float CoreScale = 0.3f + 0.7f * CoreT + 0.15f * Bump(Ms, LatchMs, BloomMs);
	Core->SetRelativeScale3D(FVector(CoreScale));

	const float Tilt = Ease((Ms - BloomMs) / (IgniteMs - BloomMs));
	if (Ms >= IgniteMs)
	{
		SpinDegrees = FMath::Fmod(SpinDegrees + DeltaSeconds * 14.0f, 360.0f);
	}
	for (int32 Index = 0; Index < Rings.Num(); ++Index)
	{
		const float Grow = Ease((Ms - LatchMs - Index * 30.0f) / (BloomMs - LatchMs));
		const float TiltDeg = RingTiltDegrees[Index % UE_ARRAY_COUNT(RingTiltDegrees)] * Tilt;
		const float Spin = SpinDegrees * (Index + 1) * ((Index % 2) ? -1.0f : 1.0f);
		const FQuat Rotation = FQuat(FVector::UpVector, FMath::DegreesToRadians(TiltDeg))
			* FQuat(FRotator(90.0f, 0.0f, 0.0f))
			* FQuat(FVector::UpVector, FMath::DegreesToRadians(Spin));
		Rings[Index]->SetRelativeRotation(Rotation);
		Rings[Index]->SetRelativeScale3D(FVector((1.0f + Index * RingRadiusStep) * FMath::Max(Grow, 0.01f)));
	}

	const float PetalOpen = Ease((Ms - LatchMs) / (IgniteMs - LatchMs));
	const float Overshoot = Bump(Ms, IgniteMs, SettleMs);
	const float FoldYaw = -85.0f * (1.0f - PetalOpen) + 9.0f * Overshoot;
	for (UStaticMeshComponent* Petal : Petals)
	{
		Petal->SetRelativeRotation(FQuat(FVector::UpVector, FMath::DegreesToRadians(FoldYaw)) * FQuat(FRotator(-90.0f, 0.0f, 0.0f)));
		Petal->SetRelativeScale3D(FVector(0.6f + 0.6f * PetalOpen));
	}

	const float Ignite = Bump(Ms, BloomMs, SettleMs);
	if (BaseLightIntensity > 0.0f)
	{
		Light->SetIntensity(BaseLightIntensity * (1.0f + 2.0f * Ignite));
	}
}
