#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaSharedAuthorityInterfaces.h"
#include "MelodiaInputContextSubsystem.generated.h"

class APlayerController;

/**
 * What currently owns player input. Exactly one is active at a time.
 *
 * Ordering is deliberate: higher values are more restrictive, so a simple
 * comparison answers "is anything more demanding than exploration active?".
 */
UENUM(BlueprintType)
enum class EMelodiaInputContext : uint8
{
	/** Nothing pushed. Treated as Exploration for permission queries. */
	None		UMETA(DisplayName = "None"),

	/** Free movement, jump, glide, interact. The default overworld state. */
	Exploration	UMETA(DisplayName = "Exploration"),

	/** Quill dialogue is presenting. Movement suppressed, advance/choice accepted. */
	Dialogue	UMETA(DisplayName = "Dialogue"),

	/** Stock JRPG command UI owns input. Movement suppressed, saving refused. */
	Battle		UMETA(DisplayName = "Battle"),

	/** Main menu, settings, save/load. Movement suppressed. */
	Menu		UMETA(DisplayName = "Menu"),

	/** Authored sequence. All player input suppressed. */
	Cinematic	UMETA(DisplayName = "Cinematic"),

	/**
	 * A rhythm session owns input. Lane keys (Q/W/O/P) are live, movement is
	 * suppressed, and saving is refused for the same reason as Battle.
	 *
	 * The keys are authored in BP_BattleUI's OnKeyDown AND OnKeyUp graphs, which
	 * must agree -- OnKeyUp is what clears the pressed state, so a key present in
	 * one and not the other latches that lane lit for the rest of the session.
	 *
	 * Appended rather than inserted after Battle deliberately: Blueprint pin
	 * defaults store this enum by byte value, so inserting mid-list would
	 * silently repoint every authored Menu/Cinematic default. The "higher value
	 * is more restrictive" ordering above therefore does not hold for Rhythm --
	 * every permission query below tests it explicitly, none compare by value.
	 */
	Rhythm		UMETA(DisplayName = "Rhythm")
};

/**
 * Opaque token identifying one push. Hold it and pass it to PopContext.
 *
 * Handles exist so contexts can be released out of order -- a dialogue that ends
 * while a menu is open must remove its own entry, not whatever happens to be on top.
 */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaInputContextHandle
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Input")
	int32 Id = 0;

	bool IsValid() const { return Id > 0; }
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaInputContextChanged,
	EMelodiaInputContext, NewContext, EMelodiaInputContext, PreviousContext);

/**
 * The project's single input and focus authority.
 *
 * Before this existed there were ZERO SetInputMode call sites in C++ -- every widget
 * and Blueprint managed input mode ad hoc, and nothing restored it. That is the direct
 * cause of stuck cursors, dead movement after dialogue, and battle HUD that will not
 * release focus, which are items 1 and 2 of the Flow/QOL priorities in
 * _VERTICAL_SLICE_SCOPE.md.
 *
 * Contexts form a stack. The top entry owns input. Popping restores whatever was
 * beneath it, so a caller cannot leak a mode by forgetting to reset -- it only has to
 * release its own handle. Travel force-clears the stack, so a transition can never
 * strand the player in dialogue input.
 *
 * AUTHORITY: input mode, cursor visibility, and the permission queries below. It does
 * not own movement code, battle flow, or save execution -- it answers whether those
 * are currently permitted, and the systems themselves honour the answer.
 */
UCLASS()
class BS_GODFILE_API UMelodiaInputContextSubsystem final : public UGameInstanceSubsystem, public IMelodiaInputContextProvider
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Input", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaInputContextSubsystem* Get(const UObject* WorldContextObject);

	// --- Stack ---------------------------------------------------------------

	/**
	 * Take ownership of input. Keep the returned handle and pop it when done.
	 *
	 * @param Context  What is taking over.
	 * @param Owner    For diagnostics only; logged so an unreleased context can be
	 *                 traced to whatever pushed it. Not held as a strong reference.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	FMelodiaInputContextHandle PushContext(EMelodiaInputContext Context, UObject* Owner);

	/** Release a push. Safe to call twice; the second call is a no-op returning false. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	bool PopContext(FMelodiaInputContextHandle Handle);

	/**
	 * Drop every context and return to Exploration.
	 *
	 * Called automatically on travel arrival. Reason is logged -- if this ever fires
	 * with entries still on the stack, something failed to release and the log names it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Input")
	void ClearAllContexts(const FString& Reason);

	// --- Queries the in-scope mechanics need ---------------------------------

	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	EMelodiaInputContext GetActiveContext() const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	bool IsContextActive(EMelodiaInputContext Context) const { return GetActiveContext() == Context; }

	/** Traversal: jump, glide, walk. False in dialogue, battle, menu, cinematic and rhythm. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	virtual bool IsMovementAllowed() const override;

	/** Interaction prompts and the interact key. Exploration only. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	virtual bool IsInteractionAllowed() const override;

	/**
	 * Whether a save may be written right now.
	 *
	 * Enforces the no-mid-battle-save gate from _VERTICAL_SLICE_SCOPE.md structurally
	 * rather than as a rule somebody has to remember. False during Battle and
	 * Cinematic; Dialogue is permitted because autosave fires at dialogue boundaries.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	virtual bool IsSavingAllowed() const override;

	/** How many contexts are stacked. Non-zero outside Exploration means nesting. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Input")
	int32 GetContextDepth() const { return ContextStack.Num(); }

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Input")
	FMelodiaInputContextChanged OnInputContextChanged;

private:
	struct FContextEntry
	{
		int32 Id = 0;
		EMelodiaInputContext Context = EMelodiaInputContext::None;
		FString OwnerName;
	};

	/** Pushes the engine input mode and cursor state matching the active context. */
	void ApplyActiveContext(EMelodiaInputContext PreviousContext);

	APlayerController* GetPlayerController() const;

	TArray<FContextEntry> ContextStack;
	int32 NextHandleId = 1;
};
