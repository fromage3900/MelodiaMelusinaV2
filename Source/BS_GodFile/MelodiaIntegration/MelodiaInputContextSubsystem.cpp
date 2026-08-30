#include "MelodiaInputContextSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaAuthorityLocator.h"

void UMelodiaInputContextSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ContextStack.Reset();
	NextHandleId = 1;

	if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
	{
		Locator->RegisterInputContextProvider(TScriptInterface<IMelodiaInputContextProvider>(this));
		UE_LOG(LogTemp, Log, TEXT("MELODIA_AUTHORITY registered InputContextProvider"));
	}
}

void UMelodiaInputContextSubsystem::Deinitialize()
{
	ContextStack.Reset();
	Super::Deinitialize();
}

UMelodiaInputContextSubsystem* UMelodiaInputContextSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaInputContextSubsystem>() : nullptr;
}

APlayerController* UMelodiaInputContextSubsystem::GetPlayerController() const
{
	const UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	return World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
}

EMelodiaInputContext UMelodiaInputContextSubsystem::GetActiveContext() const
{
	return ContextStack.Num() > 0 ? ContextStack.Last().Context : EMelodiaInputContext::None;
}

FMelodiaInputContextHandle UMelodiaInputContextSubsystem::PushContext(const EMelodiaInputContext Context, UObject* Owner)
{
	FMelodiaInputContextHandle Handle;

	if (Context == EMelodiaInputContext::None)
	{
		// Pushing None would make the stack lie about who owns input.
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_INPUT push rejected: None is not a pushable context (owner=%s)"),
			*GetNameSafe(Owner));
		return Handle;
	}

	const EMelodiaInputContext Previous = GetActiveContext();

	FContextEntry Entry;
	Entry.Id = NextHandleId++;
	Entry.Context = Context;
	Entry.OwnerName = GetNameSafe(Owner);
	ContextStack.Add(Entry);

	Handle.Id = Entry.Id;

	UE_LOG(LogTemp, Log, TEXT("MELODIA_INPUT_PUSH context=%s owner=%s depth=%d handle=%d"),
		*UEnum::GetValueAsString(Context), *Entry.OwnerName, ContextStack.Num(), Entry.Id);

	ApplyActiveContext(Previous);
	return Handle;
}

bool UMelodiaInputContextSubsystem::PopContext(const FMelodiaInputContextHandle Handle)
{
	if (!Handle.IsValid())
	{
		return false;
	}

	const int32 Index = ContextStack.IndexOfByPredicate(
		[&Handle](const FContextEntry& Entry) { return Entry.Id == Handle.Id; });

	if (Index == INDEX_NONE)
	{
		// Already popped, or popped by ClearAllContexts. Not an error -- teardown
		// order is not guaranteed and a double release must stay harmless.
		return false;
	}

	const EMelodiaInputContext Previous = GetActiveContext();
	const FContextEntry Removed = ContextStack[Index];

	// Remove by index, not by popping the top: a dialogue ending while a menu is
	// open must release its own entry and leave the menu owning input.
	ContextStack.RemoveAt(Index);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_INPUT_POP context=%s owner=%s depth=%d handle=%d"),
		*UEnum::GetValueAsString(Removed.Context), *Removed.OwnerName, ContextStack.Num(), Removed.Id);

	ApplyActiveContext(Previous);
	return true;
}

void UMelodiaInputContextSubsystem::ClearAllContexts(const FString& Reason)
{
	if (ContextStack.Num() == 0)
	{
		return;
	}

	// Anything still stacked here failed to release. Name it -- this is the log line
	// that turns "the cursor is stuck again" into a specific culprit.
	for (const FContextEntry& Entry : ContextStack)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_INPUT_LEAK context=%s owner=%s was still held at clear (%s)"),
			*UEnum::GetValueAsString(Entry.Context), *Entry.OwnerName, *Reason);
	}

	const EMelodiaInputContext Previous = GetActiveContext();
	ContextStack.Reset();

	UE_LOG(LogTemp, Log, TEXT("MELODIA_INPUT_CLEAR reason=%s"), *Reason);
	ApplyActiveContext(Previous);
}

bool UMelodiaInputContextSubsystem::IsMovementAllowed() const
{
	const EMelodiaInputContext Context = GetActiveContext();
	return Context == EMelodiaInputContext::None || Context == EMelodiaInputContext::Exploration;
}

bool UMelodiaInputContextSubsystem::IsInteractionAllowed() const
{
	// Same permission set as movement today, but kept separate: interaction prompts
	// are the thing most likely to want suppressing independently later.
	return IsMovementAllowed();
}

bool UMelodiaInputContextSubsystem::IsSavingAllowed() const
{
	const EMelodiaInputContext Context = GetActiveContext();

	// Battle: _VERTICAL_SLICE_SCOPE.md requires manual saving be unavailable during an
	// active narrative battle, and a mid-battle save cannot represent turn state.
	// Cinematic: an authored sequence has no stable resume point.
	// Rhythm: a session in flight holds an unsubmitted result; saving mid-session
	// would persist a state the rhythm subsystem cannot reconstruct on load.
	// Dialogue is allowed -- autosave fires at dialogue boundaries by design.
	return Context != EMelodiaInputContext::Battle
		&& Context != EMelodiaInputContext::Cinematic
		&& Context != EMelodiaInputContext::Rhythm;
}

void UMelodiaInputContextSubsystem::ApplyActiveContext(const EMelodiaInputContext PreviousContext)
{
	const EMelodiaInputContext Context = GetActiveContext();
	if (Context == PreviousContext)
	{
		return;
	}

	if (APlayerController* PC = GetPlayerController())
	{
		switch (Context)
		{
		case EMelodiaInputContext::Battle:
		case EMelodiaInputContext::Menu:
		case EMelodiaInputContext::Rhythm:
			// GameAndUI, not UIOnly: the stock JRPG command UI must accept keyboard
			// and controller navigation as well as the mouse, and UIOnly drops the
			// game-side bindings that parity testing depends on.
			{
				FInputModeGameAndUI Mode;
				Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				Mode.SetHideCursorDuringCapture(false);
				PC->SetInputMode(Mode);
			}
			PC->bShowMouseCursor = true;
			break;

		case EMelodiaInputContext::Dialogue:
			{
				FInputModeGameAndUI Mode;
				Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				PC->SetInputMode(Mode);
			}
			PC->bShowMouseCursor = true;
			break;

		case EMelodiaInputContext::Cinematic:
			PC->SetInputMode(FInputModeGameOnly());
			PC->bShowMouseCursor = false;
			break;

		case EMelodiaInputContext::None:
		case EMelodiaInputContext::Exploration:
		default:
			{
				FInputModeGameAndUI Mode;
				Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				Mode.SetHideCursorDuringCapture(false);
				PC->SetInputMode(Mode);
			}
			PC->bShowMouseCursor = true;
			break;
		}
	}

	UE_LOG(LogTemp, Log, TEXT("MELODIA_INPUT_CONTEXT %s -> %s (movement=%d interact=%d save=%d)"),
		*UEnum::GetValueAsString(PreviousContext), *UEnum::GetValueAsString(Context),
		IsMovementAllowed() ? 1 : 0, IsInteractionAllowed() ? 1 : 0, IsSavingAllowed() ? 1 : 0);

	OnInputContextChanged.Broadcast(Context, PreviousContext);
}
