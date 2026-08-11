#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Actor.h"
#include "MelodiaTokenWalletSubsystem.h"
#include "MelodiaTokenPresentation.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class URotatingMovementComponent;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaTokenCollected, AActor*, Collector);

/**
 * Placeable presentation consumer for the canonical Melody Token wallet.
 * It owns no balance or persistence state and only disappears after the wallet
 * accepts its stable GrantId.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaTokenPickup final : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaTokenPickup();

	UFUNCTION(BlueprintCallable, Category="Melodia|Token")
	bool TryInteract(AActor* InteractingActor);

	UFUNCTION(BlueprintCallable, Category="Melodia|Token")
	bool TryCollect(AActor* CollectingActor);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	TObjectPtr<USphereComponent> CollectionVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	TObjectPtr<UStaticMeshComponent> TokenMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	TObjectPtr<URotatingMovementComponent> Rotation;

	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="Melodia|Token",
		meta=(ToolTip="Stable unique ID persisted by the wallet. Collection is refused when unset."))
	FName GrantId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	FName Element = TEXT("Forte");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token", meta=(ClampMin="1"))
	int32 Amount = 1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Token")
	bool bCollectOnOverlap = true;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Token")
	FMelodiaTokenCollected OnCollected;

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

	void EnterCollectedPresentation();
	bool bCollectionAccepted = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWalletSnapshotPresented, const FMelodiaWalletSnapshot&, Snapshot);

/**
 * Read-only wallet HUD base. Authored Widget Blueprints may optionally provide
 * the named text fields; otherwise the current snapshot remains available to
 * Blueprint through Snapshot and OnSnapshotPresented.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API UMelodiaWalletHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|Wallet")
	void RefreshFromWallet();

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Wallet")
	FMelodiaWalletSnapshot Snapshot;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Wallet")
	FMelodiaWalletSnapshotPresented OnSnapshotPresented;

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Forte;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Tide;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Gale;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Stone;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Radiant;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Umbral;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Arcane;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_Mana;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_GoldenTokens;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> TXT_TotalCollected;

private:
	UFUNCTION()
	void HandleWalletChanged(const FMelodiaWalletSnapshot& NewSnapshot);

	void PresentSnapshot(const FMelodiaWalletSnapshot& NewSnapshot);
};
