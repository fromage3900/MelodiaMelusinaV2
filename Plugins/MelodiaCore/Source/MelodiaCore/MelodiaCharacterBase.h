// Shared base for every playable Melodia character (ground, flight, future
// roster members). Owns what is genuinely identical across all of them today:
// camera rig, look-sensitivity, party-swap action/handler, and the mapping-
// context cleanup pattern. Movement/traversal specifics (jump/glide vs
// fly/boost) stay in the subclass - do not move gameplay-specific input here.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "MelodiaCharacterBase.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UInputAction;
class UInputMappingContext;
class UMelodiaOutfitComponent;

UCLASS(Abstract, Blueprintable)
class MELODIACORE_API AMelodiaCharacterBase : public ACharacter
{
	GENERATED_BODY()

public:
	AMelodiaCharacterBase();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Character")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Character")
	TObjectPtr<UCameraComponent> FollowCamera;

	/** Modular-outfit slot owner. Present on every playable character even
	 * before individual garment slots are populated, so outfit work never
	 * needs another character-base migration. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Character|Outfit")
	TObjectPtr<UMelodiaOutfitComponent> Outfit;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Character|Input", meta=(ClampMin="0.05", ClampMax="2.0"))
	float MouseLookSensitivity = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Character|Input")
	bool bInvertMouseY = true;

	/** Shared across the whole roster so UMelodiaPartySubsystem only has to
	 * bind one action regardless of which concrete character is possessed. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Character|Input")
	TObjectPtr<UInputAction> PartySwitchAction;

	virtual void UnPossessed() override;

protected:
	/** Hands control to the party subsystem. Subclasses bind this to their
	 * own mapping context's party-switch key; the handler itself never
	 * needs to differ per character. */
	UFUNCTION()
	virtual void OnPartySwitch();

	/** Common UnPossessed cleanup: remove one mapping context so swapping
	 * pawns never stacks input bindings. Call from the subclass's own
	 * UnPossessed override before Super::UnPossessed(). */
	void RemoveMappingContextOnUnpossess(UInputMappingContext* Context) const;
};
