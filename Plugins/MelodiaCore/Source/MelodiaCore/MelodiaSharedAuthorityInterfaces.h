#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MelodiaSharedAuthorityInterfaces.generated.h"

/**
 * Cross-module authority interfaces.
 *
 * MelodiaCore (this plugin) cannot call the game module's single-authority
 * subsystems (UMelodiaTravelSubsystem, UMelodiaInputContextSubsystem, ...)
 * directly: they live in BS_GodFile, and BS_GodFile.Build.cs already depends
 * on MelodiaCore, so the reverse dependency would be circular.
 *
 * These interfaces plus UMelodiaAuthorityLocator (same directory) are the
 * fix. The concrete BS_GodFile subsystems implement them and register with
 * the locator in their own Initialize(); MelodiaCore's native C++ resolves
 * through the locator instead of GetSubsystem<T>() directly. Nothing that
 * already works moves or changes class path -- this is additive.
 *
 * Keep this file to capabilities MelodiaCore's C++ actually calls. Do not
 * grow it speculatively; a stale, uncalled interface method is worse than no
 * interface at all because nothing will ever tell you it drifted from the
 * concrete subsystem's real behaviour.
 */

UINTERFACE(MinimalAPI, BlueprintType, NotBlueprintable)
class UMelodiaTravelProvider : public UInterface
{
	GENERATED_BODY()
};

/** Mirrors UMelodiaTravelSubsystem's public API. See that class for the full contract. */
class MELODIACORE_API IMelodiaTravelProvider
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Melodia|Travel")
	virtual bool TravelTo(FName LevelId, FName SpawnTag) = 0;

	// BlueprintCallable, not BlueprintPure: UHT rejects BlueprintPure on an interface
	// function declaration outright. The concrete override in
	// UMelodiaTravelSubsystem keeps its own BlueprintPure -- that is a separate
	// UFUNCTION declaration and is unaffected by this constraint.
	UFUNCTION(BlueprintCallable, Category = "Melodia|Travel")
	virtual FName GetPendingSpawnTag(FName MapId) const = 0;
};

UINTERFACE(MinimalAPI, BlueprintType, NotBlueprintable)
class UMelodiaInputContextProvider : public UInterface
{
	GENERATED_BODY()
};

/** Mirrors UMelodiaInputContextSubsystem's query surface. Push/Pop are deliberately
 * not exposed here -- no MelodiaCore call site owns a context today. Add them only
 * when a real consumer needs them, not speculatively. */
class MELODIACORE_API IMelodiaInputContextProvider
{
	GENERATED_BODY()

public:
	// BlueprintCallable, not BlueprintPure -- see IMelodiaTravelProvider::GetPendingSpawnTag
	// for why. The concrete overrides in UMelodiaInputContextSubsystem keep BlueprintPure.
	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	virtual bool IsMovementAllowed() const = 0;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	virtual bool IsInteractionAllowed() const = 0;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	virtual bool IsSavingAllowed() const = 0;
};

UINTERFACE(MinimalAPI, BlueprintType, NotBlueprintable)
class UMelodiaTraversalStateProvider : public UInterface
{
	GENERATED_BODY()
};

/** Query surface for the pawn's live traversal state, implemented by the game
 * module's UMelodiaTraversalComponent. MelodiaCore anim instances use this to
 * drive locomotion graph states (Glide, Sprint) without a circular dependency
 * on BS_GodFile. Never call the old AMelodiaSmokeCharacter cast for this --
 * no spawned pawn is a Smoke character anymore. */
class MELODIACORE_API IMelodiaTraversalStateProvider
{
	GENERATED_BODY()

public:
	// BlueprintCallable, not BlueprintPure -- see IMelodiaTravelProvider::GetPendingSpawnTag
	// for why. The concrete overrides in UMelodiaTraversalComponent keep BlueprintPure.
	UFUNCTION(BlueprintCallable, Category = "Melodia|Traversal")
	virtual bool IsGliding() const = 0;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Traversal")
	virtual bool IsSprinting() const = 0;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Traversal")
	virtual bool IsJumpWindingUp() const = 0;
};
