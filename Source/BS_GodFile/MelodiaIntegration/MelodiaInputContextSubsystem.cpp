#include "MelodiaInputContextSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaAuthorityLocator.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "GenericPlatform/GenericApplication.h"
#include "Input/Events.h"
#include "InputCoreTypes.h"

class FMelodiaCursorInputPreprocessor final : public IInputProcessor
{
public:
	explicit FMelodiaCursorInputPreprocessor(UMelodiaInputContextSubsystem& InOwner) : Owner(&InOwner) {}

	virtual bool HandleMouseButtonDownEvent(FSlateApplication&, const FPointerEvent& Event) override
	{
		if (Owner.IsValid()) Owner->HandlePointerEvent(Event.GetEffectingButton(), Event.GetScreenSpacePosition(), Event.GetPointerIndex(), Event.IsTouchEvent(), true);
		return false;
	}

	virtual bool HandleMouseButtonUpEvent(FSlateApplication&, const FPointerEvent& Event) override
	{
		if (Owner.IsValid()) Owner->HandlePointerEvent(Event.GetEffectingButton(), Event.GetScreenSpacePosition(), Event.GetPointerIndex(), Event.IsTouchEvent(), false);
		return false;
	}

	virtual bool HandleMouseMoveEvent(FSlateApplication&, const FPointerEvent& Event) override
	{
		if (Owner.IsValid() && !Event.IsTouchEvent()) Owner->HandleInputDevice(EMelodiaCursorDevice::MouseAndKeyboard);
		return false;
	}

	virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override
	{
		if (Owner.IsValid()) Owner->HandleInputDevice(Event.GetKey().IsGamepadKey() ? EMelodiaCursorDevice::Gamepad : EMelodiaCursorDevice::MouseAndKeyboard);
		return false;
	}

	virtual bool HandleAnalogInputEvent(FSlateApplication&, const FAnalogInputEvent& Event) override
	{
		if (Owner.IsValid() && Event.GetKey().IsGamepadKey()) Owner->HandleInputDevice(EMelodiaCursorDevice::Gamepad);
		return false;
	}

private:
	TWeakObjectPtr<UMelodiaInputContextSubsystem> Owner;
};

bool FMelodiaCursorVisualState::operator==(const FMelodiaCursorVisualState& Other) const
{
	return ContextTheme == Other.ContextTheme && BaseRole == Other.BaseRole && EffectiveRole == Other.EffectiveRole
		&& ActiveDevice == Other.ActiveDevice && bPressed == Other.bPressed && bVisible == Other.bVisible;
}

void UMelodiaInputContextSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ContextStack.Reset();
	NextHandleId = 1;
	CursorVisualState = ResolveCursorVisualState(GetActiveContext(), RequestedCursorRole, false, ActiveCursorDevice, FPlatformMisc::SupportsTouchInput());
	if (FSlateApplication::IsInitialized())
	{
		CursorInputPreprocessor = MakeShared<FMelodiaCursorInputPreprocessor>(*this);
		FSlateApplication::Get().RegisterInputPreProcessor(CursorInputPreprocessor, 0);
	}
	RefreshTickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateWeakLambda(this, [this](float)
	{
		RefreshControllerAndWorld();
		return true;
	}));

	if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
	{
		Locator->RegisterInputContextProvider(TScriptInterface<IMelodiaInputContextProvider>(this));
		UE_LOG(LogTemp, Log, TEXT("MELODIA_AUTHORITY registered InputContextProvider"));
	}
}

void UMelodiaInputContextSubsystem::Deinitialize()
{
	if (RefreshTickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(RefreshTickerHandle);
		RefreshTickerHandle.Reset();
	}
	if (CursorInputPreprocessor.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().UnregisterInputPreProcessor(CursorInputPreprocessor);
	}
	CursorInputPreprocessor.Reset();
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
			break;

		case EMelodiaInputContext::Dialogue:
			{
				FInputModeGameAndUI Mode;
				Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
				PC->SetInputMode(Mode);
			}
			break;

		case EMelodiaInputContext::Cinematic:
			PC->SetInputMode(FInputModeGameOnly());
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
			break;
		}
	}
	UpdateCursorVisualState();

	UE_LOG(LogTemp, Log, TEXT("MELODIA_INPUT_CONTEXT %s -> %s (movement=%d interact=%d save=%d)"),
		*UEnum::GetValueAsString(PreviousContext), *UEnum::GetValueAsString(Context),
		IsMovementAllowed() ? 1 : 0, IsInteractionAllowed() ? 1 : 0, IsSavingAllowed() ? 1 : 0);

	if (Context != PreviousContext)
	{
		OnInputContextChanged.Broadcast(Context, PreviousContext);
	}
}

FMelodiaCursorVisualState UMelodiaInputContextSubsystem::ResolveCursorVisualState(const EMelodiaInputContext Context,
	const EMelodiaCursorRole BaseRole, const bool bPressed, const EMelodiaCursorDevice Device, const bool bTouchOnlyPlatform)
{
	FMelodiaCursorVisualState State;
	State.ContextTheme = Context == EMelodiaInputContext::None ? EMelodiaInputContext::Exploration : Context;
	State.BaseRole = BaseRole;
	State.ActiveDevice = Device;
	State.bPressed = bPressed;
	State.bVisible = Context != EMelodiaInputContext::Cinematic && !bTouchOnlyPlatform && Device == EMelodiaCursorDevice::MouseAndKeyboard;
	State.EffectiveRole = BaseRole == EMelodiaCursorRole::SlashedCircle
		? EMelodiaCursorRole::SlashedCircle
		: (bPressed ? EMelodiaCursorRole::Crosshairs : BaseRole);
	return State;
}

void UMelodiaInputContextSubsystem::RefreshControllerAndWorld()
{
	APlayerController* CurrentController = GetPlayerController();
	UWorld* CurrentWorld = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (AppliedPlayerController.Get() != CurrentController || AppliedWorld.Get() != CurrentWorld)
	{
		AppliedPlayerController = CurrentController;
		AppliedWorld = CurrentWorld;
		ApplyActiveContext(GetActiveContext());
	}
}

void UMelodiaInputContextSubsystem::HandlePointerEvent(const FKey& Button, const FVector2D& ScreenPosition,
	const int32 PointerIndex, const bool bIsTouch, const bool bPressed)
{
	HandleInputDevice(bIsTouch ? EMelodiaCursorDevice::Touch : EMelodiaCursorDevice::MouseAndKeyboard);
	bPointerPressed = bPressed;
	UpdateCursorVisualState();

	FMelodiaCursorPointerData Data;
	Data.Button = Button;
	Data.ScreenPosition = ScreenPosition;
	Data.PointerIndex = PointerIndex;
	Data.bIsTouch = bIsTouch;
	Data.ActiveContext = GetActiveContext();
	if (bPressed) OnCursorPointerDown.Broadcast(Data);
	else OnCursorPointerUp.Broadcast(Data);
}

void UMelodiaInputContextSubsystem::HandleInputDevice(const EMelodiaCursorDevice Device)
{
	if (ActiveCursorDevice != Device)
	{
		ActiveCursorDevice = Device;
		UpdateCursorVisualState();
	}
}

void UMelodiaInputContextSubsystem::SetCursorRole(const EMelodiaCursorRole Role)
{
	if (RequestedCursorRole != Role)
	{
		RequestedCursorRole = Role;
		UpdateCursorVisualState();
	}
}

void UMelodiaInputContextSubsystem::UpdateCursorVisualState()
{
	const FMelodiaCursorVisualState NewState = ResolveCursorVisualState(GetActiveContext(), RequestedCursorRole,
		bPointerPressed, ActiveCursorDevice, FPlatformMisc::SupportsTouchInput());
	if (APlayerController* PC = GetPlayerController())
	{
		PC->bShowMouseCursor = NewState.bVisible;
		PC->CurrentMouseCursor = static_cast<EMouseCursor::Type>(NewState.EffectiveRole);
	}
	if (NewState != CursorVisualState)
	{
		CursorVisualState = NewState;
		OnCursorVisualStateChanged.Broadcast(CursorVisualState);
	}
}
