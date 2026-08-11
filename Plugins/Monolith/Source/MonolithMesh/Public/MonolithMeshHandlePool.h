#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"

class UDynamicMesh;
class FJsonObject;

#if WITH_GEOMETRYSCRIPT
#include "UDynamicMesh.h"
#include "Containers/Ticker.h"
#endif

#include "MonolithMeshHandlePool.generated.h"

/**
 * Pool of named UDynamicMesh handles for GeometryScript mesh operations.
 * All access is game-thread only. AddToRoot on creation, RemoveFromRoot on shutdown.
 * Eviction timer removes idle handles after a configurable timeout.
 *
 * The UCLASS always exists (UHT requirement), but methods are no-ops when
 * WITH_GEOMETRYSCRIPT=0.
 */
UCLASS()
class UMonolithMeshHandlePool : public UObject
{
	GENERATED_BODY()

public:
	static constexpr int32 MaxHandles = 64;
	static constexpr float EvictionTimeoutSeconds = 300.0f;
	static constexpr float EvictionCheckIntervalSeconds = 60.0f;

	void Initialize();
	void Teardown();

	bool CreateHandle(const FString& HandleName, const FString& Source, FString& OutError);
	UDynamicMesh* GetHandle(const FString& HandleName, FString& OutError);
	bool ReleaseHandle(const FString& HandleName);
	bool SaveHandle(const FString& HandleName, const FString& TargetPath, bool bOverwrite, FString& OutError,
		const FString& CollisionMode = TEXT("auto"), int32 MaxHulls = 4);
	TSharedPtr<FJsonObject> ListHandles() const;

private:
	// UPROPERTY must be outside preprocessor guards (UHT limitation).
	// Store as UObject* — cast to UDynamicMesh* at runtime in WITH_GEOMETRYSCRIPT code.
	UPROPERTY()
	TMap<FString, TObjectPtr<UObject>> Handles;

	TMap<FString, FString> HandleSources;
	TMap<FString, double> LastAccessTime;

#if WITH_GEOMETRYSCRIPT
	FTSTicker::FDelegateHandle EvictionTimerHandle;

	void TouchHandle(const FString& HandleName);
	bool OnEvictionCheck(float DeltaTime);
	UDynamicMesh* CreateFromPrimitive(const FString& PrimitiveType, FString& OutError);
	UDynamicMesh* CreateFromAsset(const FString& AssetPath, FString& OutError);
#endif
};
