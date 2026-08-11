#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include "PCGPoint.h"
#include "PCGPianoKeyboard.generated.h"

class UPCGComponent;
class UPCGGraph;
class UPCGMetadata;
class UBoxComponent;
class UPrimitiveComponent;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;
class USoundBase;
class UMaterialInterface;

USTRUCT(BlueprintType)
struct BS_GODFILE_API FPCGPianoKeyboardDimensions
{
	GENERATED_BODY()

	/** Unreal units. The defaults are centimeter-based dimensions for a full-size piano key. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float WhiteKeyWidth = 23.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float WhiteKeyDepth = 150.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float WhiteKeyHeight = 20.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float BlackKeyWidth = 13.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float BlackKeyDepth = 95.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float BlackKeyHeight = 32.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Dimensions")
	float InterKeyGap = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Animation", meta = (ClampMin = "0.0"))
	float PressDepth = 8.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Animation", meta = (ClampMin = "0.0"))
	float SpringStiffness = 950.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Animation", meta = (ClampMin = "0.0"))
	float SpringDamping = 92.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Piano|Animation", meta = (ClampMin = "0.0"))
	float PressTriggerHeight = 8.0f;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UPCGPianoKeyboardProfile : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Layout")
	int32 FirstMidiNote = 21;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Layout")
	int32 LastMidiNote = 108;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Layout")
	FPCGPianoKeyboardDimensions Dimensions;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UStaticMesh> WhiteKeyMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UStaticMesh> BlackKeyMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UStaticMesh> KeybedMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UMaterialInterface> WhiteKeyMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UMaterialInterface> BlackKeyMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Visuals")
	TSoftObjectPtr<UMaterialInterface> KeybedMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Audio")
	TSoftObjectPtr<USoundBase> PressSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Audio")
	bool bPlayPressSound = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FPCGPianoKeyEvent, int32, KeyIndex, int32, MidiNote, AActor*, SteppingActor);

UCLASS(Blueprintable)
class BS_GODFILE_API APCGPianoKey : public AActor
{
	GENERATED_BODY()

public:
	APCGPianoKey();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Called by PCGSpawnActor after the point has produced this key actor. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Piano|PCG")
	void InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata);

	UFUNCTION(BlueprintPure, Category = "Piano")
	int32 GetKeyIndex() const { return KeyIndex; }

	UFUNCTION(BlueprintPure, Category = "Piano")
	int32 GetMidiNote() const { return MidiNote; }

	UFUNCTION(BlueprintPure, Category = "Piano")
	bool IsBlackKey() const { return bIsBlackKey; }

	UFUNCTION(BlueprintPure, Category = "Piano")
	bool IsPressed() const { return bIsPressed; }

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Piano|Components")
	TObjectPtr<UStaticMeshComponent> KeyMesh;

	/** Moving blocker: it follows the key down during the spring animation. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Piano|Components")
	TObjectPtr<UBoxComponent> KeyBlocker;

	/** Static overlap volume used for player-foot contact. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Piano|Components")
	TObjectPtr<UBoxComponent> StepTrigger;

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyPressed;

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyReleased;

	/** Bounds used by the keyboard to decide which overlapping key is physically on top. */
	FBox GetWorldFootprint() const;

	float GetKeyTopZ() const;

	void SetLogicalPressed(AActor* SteppingActor, bool bPressedForActor);

	void SetKeyboard(class APCGPianoKeyboard* InKeyboard);

protected:
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Piano|PCG")
	int32 KeyIndex = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Piano|PCG")
	int32 MidiNote = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Piano|PCG")
	bool bIsBlackKey = false;

	void ApplyProfileGeometry();
	void ResolveKeyboard();
	UFUNCTION()
	void HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
	UFUNCTION()
	void HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
	void BeginVisualPress(AActor* SteppingActor);
	void EndVisualPress(AActor* SteppingActor);

	bool IsPlayerControlledPawn(AActor* OtherActor) const;

	TWeakObjectPtr<class APCGPianoKeyboard> KeyboardOwner;
	TSet<TWeakObjectPtr<AActor>> PressingActors;
	float CurrentPressOffset = 0.0f;
	float PressVelocity = 0.0f;
	bool bIsPressed = false;
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGPianoWhiteKey : public APCGPianoKey
{
	GENERATED_BODY()

public:
	APCGPianoWhiteKey();
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGPianoBlackKey : public APCGPianoKey
{
	GENERATED_BODY()

public:
	APCGPianoBlackKey();
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGPianoKeyboard : public AActor
{
	GENERATED_BODY()

public:
	APCGPianoKeyboard();

	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Piano|Components")
	TObjectPtr<UPCGComponent> PCGComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Configuration")
	TObjectPtr<UPCGPianoKeyboardProfile> Profile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Configuration")
	TObjectPtr<UPCGGraph> PianoGraph;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Piano|Configuration")
	FName KeyboardId = TEXT("PianoKeyboard");

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyPressed;

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyReleased;

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyboardPressed;

	UPROPERTY(BlueprintAssignable, Category = "Piano|Events")
	FPCGPianoKeyEvent OnKeyboardReleased;

	UPROPERTY(BlueprintReadOnly, Category = "Piano|State")
	int32 ActiveKeyCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Piano|State")
	int32 RegisteredKeyCount = 0;

	UFUNCTION(BlueprintPure, Category = "Piano")
	UPCGPianoKeyboardProfile* GetProfile() const { return Profile; }

	void RegisterKey(APCGPianoKey* Key);
	void UnregisterKey(APCGPianoKey* Key);
	void NotifyContactBegin(APCGPianoKey* Key, AActor* SteppingActor);
	void NotifyContactEnd(APCGPianoKey* Key, AActor* SteppingActor);
	void NotifyKeyPressed(APCGPianoKey* Key, AActor* SteppingActor);
	void NotifyKeyReleased(APCGPianoKey* Key, AActor* SteppingActor);

private:
	void RecomputePressedKeysForActor(AActor* SteppingActor);
	void RemoveActorContact(AActor* SteppingActor);
	void UpdateActiveKeyCount();

	UPROPERTY()
	TSet<TObjectPtr<APCGPianoKey>> RegisteredKeys;

	TMap<TObjectPtr<AActor>, TSet<TObjectPtr<APCGPianoKey>>> ContactsByActor;
};
