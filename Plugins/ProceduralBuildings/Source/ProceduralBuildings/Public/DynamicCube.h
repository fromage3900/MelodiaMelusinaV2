

#pragma once

#include "CoreMinimal.h"
#include "Materials/MaterialInterface.h"
#include "UDynamicMesh.h"
#include "UObject/NoExportTypes.h"
#include "UDynamicMesh.h"
#include "GeometryScript/MeshPrimitiveFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "DynamicCube.generated.h"

/**
 * This is a wrapper around various static methods that the Procedural Mesh plugin provides.
 * Instead of having a bunch of different static methods to call, which becomes confusing, this class takes all the inputs and 
 * customizations to the given shape up-front and then applies it when `GetMesh()` is called.
 * 
 */
UCLASS()
class PROCEDURALBUILDINGS_API UDynamicCube : public UObject
{
	GENERATED_BODY()

public:

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetSize(const FVector& Size);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void AddToSize(const FVector& Delta);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void AddToOrigin(const FVector& Delta);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void AddToSizeInDirection(const float Size, const FVector& Direction);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetTranslation(const FVector& Position);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void AddToTranslation(const FVector& Delta);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetRotation(const FRotator& Rotation);

	virtual void SetRotation(const FVector& Facing);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetOrigin(const FVector& Origin);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetGeometryOptions(const FGeometryScriptPrimitiveOptions Options);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetOriginMode(const EGeometryScriptPrimitiveOriginMode Origin);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual FVector GetSize();

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual FVector GetTranslation();

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual FRotator GetRotation();

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void SetTransform(const FTransform& Transform);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual FTransform GetTransform();

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void GenerateMesh(UDynamicMesh* Mesh, const bool ApplyTransform = true);

	UFUNCTION(Category="ProceduralBuildings", BlueprintCallable)
		virtual void Reset();

	// todo taper
	// todo twist
	// todo rounded rectangle, etc

private:
	FVector mScale = FVector(1.f);
	FVector mSize = FVector(100.f, 100.f, 100.f);
	FVector mOrigin = FVector::Zero();
	FVector mTranslation = FVector::Zero();
	FRotator mRotation = FRotator();
	FGeometryScriptPrimitiveOptions mGeometryOptions;
	EGeometryScriptPrimitiveOriginMode mOriginMode = EGeometryScriptPrimitiveOriginMode::Base;
};