// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Camera/CameraShakeBase.h"
#include "CoreMinimal.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>
#include <Components/MeshComponent.h>

#include "CCMTypes.generated.h"

class UMaterialInterface;
class UCameraShakeBase;
/**
 *
 */

USTRUCT(BlueprintType)
struct FCameraOccludedActor {
	GENERATED_USTRUCT_BODY()


	FCameraOccludedActor() {
		Actor = nullptr;
		StaticMesh = nullptr;
		IsOccluded = false;
	}


	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	const AActor* Actor;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	UStaticMeshComponent* StaticMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	TArray<UMaterialInterface*> Materials;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	bool IsOccluded;
};

USTRUCT(BlueprintType)
struct FMeshMaterials {
	GENERATED_USTRUCT_BODY()

public:

	FMeshMaterials() {
		Mesh = nullptr;
	}

	FMeshMaterials(UMeshComponent* inMesh)
	{
		Mesh = inMesh;
		Materials = inMesh->GetMaterials();
	}
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	UMeshComponent* Mesh = nullptr;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = CCM)
	TArray<UMaterialInterface*> Materials;

	FORCEINLINE bool operator==(const UMeshComponent* Other) const { return this->Mesh == Other; }
	FORCEINLINE bool operator!=(const UMeshComponent* Other) const { return this->Mesh != Other; }
	FORCEINLINE bool operator!=(const FMeshMaterials& Other) const { return this->Mesh != Other.Mesh; }
	FORCEINLINE bool operator==(const FMeshMaterials& Other) const { return this->Mesh == Other.Mesh; }
};

USTRUCT(BlueprintType)
struct FCCMCameraMovementSettings : public FTableRowBase {
	GENERATED_BODY()

public:
	FCCMCameraMovementSettings()
	{
		CameraOffset = FVector();
		Shake = UCameraShakeBase::StaticClass();
		FOV = 0.f;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Offset")
	FVector CameraOffset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Offset")
	float InterpSpeed = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float FovInterpSpeed = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float FOV;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	TSubclassOf<UCameraShakeBase> Shake;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bIsWorldShaking"), Category = "Camera")
	float ShakeIntensity = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bShakeLooping = false;

	FORCEINLINE FCCMCameraMovementSettings operator+=(const FCCMCameraMovementSettings& Other)
	{

		this->CameraOffset += Other.CameraOffset;
		this->FOV += Other.FOV;
		this->InterpSpeed = Other.InterpSpeed;
		this->FovInterpSpeed = Other.FovInterpSpeed;

		if (Other.Shake) {
			this->Shake = Other.Shake;
			this->ShakeIntensity = Other.ShakeIntensity;
			this->bShakeLooping = Other.bShakeLooping;
		}

		return *this;
	}

	FORCEINLINE FCCMCameraMovementSettings operator-=(const FCCMCameraMovementSettings& Other)
	{

		this->CameraOffset = this->CameraOffset - Other.CameraOffset;
		this->FOV -= Other.FOV;
		this->InterpSpeed = Other.InterpSpeed;
		this->FovInterpSpeed = Other.FovInterpSpeed;
		if (Other.Shake) {
			this->Shake = nullptr;
			this->bShakeLooping = false;
		}

		return *this;
	}
};
/**
 * Enum defining available camera movement presets.
 * All movements are continuous until manually stopped.
 */
UENUM(BlueprintType)
enum class EACFCameraMovementPreset : uint8
{
	/** No automatic movement */
	None UMETA(DisplayName = "None"),

	/** Rotate continuously around the owner actor */
	RotateAroundOwner UMETA(DisplayName = "Rotate Around Owner"),

	/** Move vertically while keeping look-at on owner. Stop manually. */
	Crane UMETA(DisplayName = "Crane"),

	/** Move laterally (strafe) while keeping look-at on owner. Stop manually. */
	PanLateral UMETA(DisplayName = "Pan Lateral"),
	/** Custom movement driven by Blueprint */
	Custom UMETA(DisplayName = "Custom (Blueprint)")
};

/**
 * Configuration struct for camera movement preset parameters.
 */
USTRUCT(BlueprintType)
struct CINEMATICCAMERAMANAGER_API FACFCameraMovementConfig
{
	GENERATED_BODY()

	/** The movement preset to use when this camera is activated */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement")
	EACFCameraMovementPreset MovementPreset = EACFCameraMovementPreset::None;

	/** Speed of the movement (degrees/sec for orbit, units/sec for crane) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement", meta = (ClampMin = "0.0", EditCondition = "MovementPreset != EACFCameraMovementPreset::None && MovementPreset != EACFCameraMovementPreset::Custom"))
	float MovementSpeed = 3.0f;

	/** Vertical offset from owner's location to look at */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Look At", meta = (EditCondition = "MovementPreset != EACFCameraMovementPreset::None && MovementPreset != EACFCameraMovementPreset::Custom"))
	float LookAtHeightOffset = 100.0f;

	/** Direction multiplier: 1 = counter-clockwise/up, -1 = clockwise/down */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement", meta = (ClampMin = "-1.0", ClampMax = "1.0", EditCondition = "MovementPreset != EACFCameraMovementPreset::None && MovementPreset != EACFCameraMovementPreset::Custom"))
	float MovementDirection = 1.0f;
};

USTRUCT(BlueprintType)
struct FCurrentSequence {
	GENERATED_BODY()

	FCurrentSequence()
	{
		cameraSequenceComp = nullptr;
	}

public:
	UPROPERTY(BlueprintReadOnly, Category = "Camera")
	class UCCMCameraSplineComponent* cameraSequenceComp;

	UPROPERTY(BlueprintReadOnly, Category = "Camera")
	float currentTime = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Camera")
	float currentSplinePos = 0.f;

	void Reset(UCCMCameraSplineComponent* inSequence)
	{
		cameraSequenceComp = inSequence;
		currentTime = 0.f;
		currentSplinePos = 0.f;
	}
};

USTRUCT(BlueprintType)
struct FCCMSequenceEvent {
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bEditCameraSpeed = false;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bEditCameraSpeed), Category = "Camera")
	float CameraSpeed = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bEditFov = false;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bEditFov), Category = "Camera")
	float CameraFovOffset = 0.f;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bEditFov), BlueprintReadWrite, Category = "Camera")
	float FovOffsetInterpSpeed = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bSwitchLookAt = false;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bSwitchLookAt), BlueprintReadWrite, Category = "Camera")
	FName LookAtPoint;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bSwitchLookAt), BlueprintReadWrite, Category = "Camera")
	float LookAtRotationSpeed = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bChangeTimeDilation = false;

	UPROPERTY(EditAnywhere, meta = (EditCondition = bChangeTimeDilation), BlueprintReadWrite, Category = "Camera")
	float TimeDilatation = 1.0f;
};

USTRUCT(BlueprintType)
struct FCCMCameraSequenceSettings : public FTableRowBase {
	GENERATED_BODY()

public:
	FCCMCameraSequenceSettings()
	{
		lookAtActor = nullptr;
	}

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float CameraSpeed = 0.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float CameraRotationsSpeed = 1.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float CameraFov = 90.f;

	UPROPERTY(BlueprintReadOnly, Category = "Camera")
	float FovInterpSpeed = 1.f;

	UPROPERTY(BlueprintReadOnly, Category = "Camera")
	AActor* lookAtActor;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	FName LookAtPoint;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float TimeDilatation = 1.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float BlendSettingsTime = .3f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "Camera")
	float OutBlendSettings = 1.f;
};

UENUM(BlueprintType)
enum class ELockType : uint8 {
	EYawOnly = 0 UMETA(DisplayName = "Only Lock Yaw"),
	EAllAxis UMETA(DisplayName = "Lock Yaw And Pitch"),
};

UENUM(BlueprintType)
enum class ETargetLockType : uint8 {
	ENone = 0,
	EActor,
	EComponent,
};

/**
 * Struct containing binding information for level sequence actors.
 * Used to bind actors to sequence tags.
 */
USTRUCT(BlueprintType)
struct CINEMATICCAMERAMANAGER_API FCCMSequenceBinding
{
	GENERATED_BODY()

	FCCMSequenceBinding()
		: TagName(NAME_None)
		, BoundActor(nullptr)
	{
	}

	FCCMSequenceBinding(const FName& InTagName, AActor* InBoundActor = nullptr)
		: TagName(InTagName)
		, BoundActor(InBoundActor)
	{
	}

	/** Tag name used to identify the binding point in the sequence */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sequence Binding")
	FName TagName;

	/** Actor to bind to this tag (optional - if null, binding will be skipped) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sequence Binding")
	TObjectPtr<AActor> BoundActor;
};



