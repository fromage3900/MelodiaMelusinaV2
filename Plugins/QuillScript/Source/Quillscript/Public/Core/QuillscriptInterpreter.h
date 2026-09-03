// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Base/InterpreterState.h"
#include "Base/Statement.h"
#include "GameFramework/Actor.h"
#include "QuillscriptInterpreter.generated.h"

enum class EInputMode : uint8;
struct FOuterParameter;
struct FScriptSettings;
class UBackgroundBox;
class USpriteBox;
class UDialogBox;
class UQuillscriptAsset;
class USelectionBox;
class UWidget;

#pragma region Delegates

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams( FStatementPlayedDelegate, AQuillscriptInterpreter*, Interpreter, const int32&, PlayedStatementIndex, const FStatement&, PlayedStatement );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FScriptStartedDelegate, AQuillscriptInterpreter*, Interpreter );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FScriptResumedDelegate, AQuillscriptInterpreter*, Interpreter );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam( FScriptEndedDelegate, AQuillscriptInterpreter*, Interpreter );

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams( FPlayDialogueBoxDelegate, AQuillscriptInterpreter*, Interpreter, const FStatement&, Dialogue );
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams( FPlaySelectionBoxDelegate, AQuillscriptInterpreter*, Interpreter, const TArray<FStatement>&, Options);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams( FPlayBackgroundBoxDelegate, AQuillscriptInterpreter*, Interpreter, UTexture*, Image, const FString&, Transition, const float&, Duration );

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams( FAudioFinishedDelegate, AQuillscriptInterpreter*, Interpreter, const FName&, Channel, UAudioComponent*, AudioComponent );

#pragma endregion Delegates


/**
 * An Interpreter is responsible for getting a Quillscript and play its story.
 * Managing story flow, player interaction, and everything story related.
 */
UCLASS(BlueprintType)
class QUILLSCRIPT_API AQuillscriptInterpreter : public AActor
{
	GENERATED_BODY()

public:
	AQuillscriptInterpreter();
	virtual void Tick(float DeltaSeconds) override;


	/// Flow
	#pragma region Flow

	/**
	 * Setup and play the scene from the start.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Start(UQuillscriptAsset* ScriptAsset, FName StartingLabel = NAME_None, const bool bResume = false);
	virtual void Start_Implementation(UQuillscriptAsset* ScriptAsset, FName StartingLabel = NAME_None, const bool bResume = false);

	/**
	 * Play Statement by name.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Flow")
	void Play(const int32 StatementIndex);
	virtual void Play_Implementation(const int32 StatementIndex);

	/**
	 * Play Statement by name.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	void PlayByLabel(const FName Label);

	/**
	 * Go back to the beginning of the script.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Restart();
	virtual void Restart_Implementation();

	/**
	 * Go to the next Statement.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Next();
	virtual void Next_Implementation();

	/**
	 * Go to previous executed Statement.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Rollback();
	virtual void Rollback_Implementation();

	/**
	 * Restart current label statement.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Repeat();

	/**
	 * Advance to next label statement.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Done();

	/**
	 * Go back to the last executed Router statement.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Return();

	/**
	 * End this script.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void End();
	virtual void End_Implementation();

	/**
	 * Same as 'End', but does not apply script settings after.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Kill();
	virtual void Kill_Implementation();

	/**
	 * Allows this scene to proceed.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Restore();
	virtual void Restore_Implementation();

	/**
	 * Prevents this scene from proceeding.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Stop();
	virtual void Stop_Implementation();

	/**
	 * The same as End, but does not destroy any object.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Sleep();
	virtual void Sleep_Implementation();

	/**
	 * Return from the sleep state.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void Wakeup();
	virtual void Wakeup_Implementation();

	/**
	 * Stop the script for a few seconds.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	void Wait(const float Duration = 0.2f);

	/**
	 * Execute the given command after the given time.
	 *
	 * @param	Duration	Seconds to wait.
	 * @param	Command		A command statement to execute when the timer is over.
	 * @param	bAsync		If false, the story flow pauses until the timer is over.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	void Timer(const float Duration, FString Command, const bool bAsync = false);

	/**
	 * Play a new script from start or from label, and end current script.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	void Travel(const FString TargetScript, const FName StartingLabel = NAME_None);

	/**
	 * Play a new script from start or from label keeping current script settings and script target, and end current script.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	void TravelPass(const FString TargetScript, const FName StartingLabel = NAME_None);

	#pragma endregion Flow


	/// Statements
	#pragma region Statements

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayLabel(const FStatement Label);
	virtual void PlayLabel_Implementation(const FStatement Label);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayDialogue(const FStatement Dialogue);
	virtual void PlayDialogue_Implementation(const FStatement Dialogue);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayOption(TArray<FStatement>& Options);
	virtual void PlayOption_Implementation(TArray<FStatement>& Options);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayCommand(const FStatement Command);
	virtual void PlayCommand_Implementation(const FStatement Command);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayRouter(const FStatement Router);
	virtual void PlayRouter_Implementation(const FStatement Router);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayCondition(const FStatement Condition);
	virtual void PlayCondition_Implementation(const FStatement Condition);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|Statements")
	void PlayDirective(const FStatement Directive);
	virtual void PlayDirective_Implementation(const FStatement Directive);

	UFUNCTION(BlueprintGetter)
	FStatement GetCurrentStatement() const;

	/**
	 * Replace Quillscript variables in statement.
	 * Conditions, Commands, Target and Target Arguments are replaced in their own methods.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|Statements")
	FStatement ReplaceVariablesInStatement(const FStatement Statement) const;

	/**
	 * return -1 if there is no statement of type, ahead.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	int32 GetPreviousStatementIndexOfType(const EStatementType Type) const;

	/**
	 * return -1 if there is no statement of type, ahead.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	int32 GetNextStatementIndexOfType(const EStatementType Type) const;

	/**
	 * return -1 if there is no end if, ahead.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	int32 GetNextElseElseIfEndIfIndex() const;

	/**
	 * return -1 if there is no end if, ahead.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Flow")
	int32 GetNextStatementIndexAfterEndIf() const;

	#pragma endregion Statements


	/// State
	#pragma region State

	/**
	 * Print the given Quillscript variable's value.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void Print(const FName VariableName) const;

	/**
	 * Delete the given Quillscript variable.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void Delete(const FName VariableName) const;

	/**
	 * Notify all registered observers in 'UQuillscriptSubsystem::OnNotified(FString)'.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void Notify(const FString Message) const;

	/**
	 * Get the complete set of sequential options from the given option statement.
	 *
	 * @param	Index	Index of the option to get its set. if -1, use current index.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|State", meta = ( AdvancedDisplay = "Index" ))
	TArray<FStatement> GetOptionsSet(int32 Index = -1) const;

	/**
	 * Callback function for when SelectionBox OnSelected event is called.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Quillscript|State")
	void OptionSelected(const FStatement Option);
	virtual void OptionSelected_Implementation(const FStatement Option);

	/**
	 * Make a copy of this Interpreter object with no Script reference.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	virtual AQuillscriptInterpreter* MakeCopy(const bool bCopyDelegates = false) const;

	/**
	 * Reboot this Interpreter back to defaults, remove references, reset state, delete temporary data, clear delegates, etc.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, CallInEditor, Category = "Quillscript|Flow")
	void HardReset();
	virtual void HardReset_Implementation();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void ResetState();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void ResetScript() const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void ResetWidgets();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void ResetAudioChannels();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|State")
	void ResetDelegates();

	#pragma endregion State


	/// Input
	#pragma region Input

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Input")
	void SetInputMode(const EInputMode InputMode, const EMouseLockMode MouseLockMode = EMouseLockMode::LockOnCapture, const bool bHideCursorDuringCapture = false, UWidget* WidgetToFocus = nullptr) const;

	/**
	 * Enable input, move input and look input.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Input")
	void InputEnable() const;

	/**
	 * Disable input, move input and look input.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Input")
	void InputDisable() const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Input")
	void ShowMouseCursor() const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Input")
	void HideMouseCursor() const;

	#pragma endregion Input


	/// User Interface
	#pragma region UI

	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	void CreateDialogBox();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	void CreateSelectionBox();

	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	void CreateBackgroundBox();

	/**
	 * Use the specified class or keyword for Dialog Box, Selection Box and Background Box.
	 *
	 * Keywords:
	 *		Default			Reset to default all boxes classes.
	 *		DialogBox		Reset to default Dialog Box class.
	 *		SelectionBox	Reset to default Selection Box class.
	 *		BackgroundBox	Reset to default Background Box class.
	 *		SpriteBox		Reset to default Sprite Box class.
	 *
	 * Class Path:
	 *		/Script/Quillscript.DialogBox
	 *		/Game/MyFolder/MyDialogBox.MyDialogBox
	 *
	 * @param WidgetClassPath	Widget class path, or keyword.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void Use(const FString WidgetClassPath) const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void ShowDialogBox() const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void ShowSelectionBox() const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void ShowBackgroundBox() const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void RemoveDialogBox() const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void RemoveSelectionBox() const;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void RemoveBackgroundBox() const;

	/**
	 * Set Dialog Box and Selection Box widgets visibility to 'Visible'.
	 * This function will be delayed to the next 2 ticks to allow the next statement to be processed first.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void Show() const;

	/**
	 * Set Dialog Box and Selection Box widgets visibility to 'Collapsed'.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void Hide() const;

	/**
	 * Show background box with background image.
	 *
	 * @param	Image		Background image asset.
	 * @param	Transition	Transition animation name.
	 * @param	Duration	Transition duration.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void Background(UTexture* Image, const FString Transition = "", const float Duration = 0.5);

	/**
	 * Show background box with background image.
	 * Alias, shot text form, for 'AQuillscriptInterpreter::Background()'.
	 *
	 * @param	Image		Background image asset.
	 * @param	Transition	Transition animation name.
	 * @param	Duration	Transition duration.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void Bg(UTexture* Image, const FString Transition = "", const float Duration = 0.5);

	/**
	 * Create a Sprite Box with the specified name and class.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|User Interface")
	void Sprite(const FName Name, TSubclassOf<USpriteBox> Class = nullptr);

	#pragma endregion UI


	/// Media
	#pragma region Media

	/**
	 * Play a sound wave asset.
	 *
	 * @param	Sound			Sound asset.
	 * @param	Channel			Sound channel name.
	 * @param	Volume			Sound volume multiplier.
	 * @param	FadeDuration	Fade duration in seconds.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void PlaySound(USoundBase* Sound, FName Channel = "default", float Volume = 1, const float FadeDuration = 0);

	/**
	 * Play a sound wave asset in the 'voice' channel.
	 * Same as 'PlaySound(Sound, "voice", Volume)'.
	 *
	 * @param	Sound			Sound asset.
	 * @param	Volume			Sound volume multiplier.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void Voice(USoundBase* Sound, float Volume = 1);

	/**
	 * Play a sound wave asset in the 'music' channel.
	 * Same as 'PlaySound(Sound, "music", Volume, FadeDuration)'.
	 *
	 * @param	Sound			Sound asset.
	 * @param	Volume			Sound volume multiplier.
	 * @param	FadeDuration	Fade duration in seconds.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void Music(USoundBase* Sound, float Volume = 0.5, float FadeDuration = 3);

	/**
	 * Play a sound wave asset in the 'sfx' channel.
	 * Same as 'PlaySound(Sound, "sfx", Volume)'.
	 *
	 * @param	Sound			Sound asset.
	 * @param	Volume			Sound volume multiplier.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void SFX(USoundBase* Sound, float Volume = 1);

	/**
	 * Stop background sound.
	 *
	 * @param	Channel			Sound channel name.
	 * @param	FadeDuration	Fade duration in seconds.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void StopSound(const FName Channel = "default", const float FadeDuration = 0);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	void StopAllSounds(const float FadeDuration = 0);

	/**
	 * Play an Static Mesh component animation.
	 *
	 * @param	SkeletalMeshComponent	Static Mesh component.
	 * @param	Animation				Animation asset.
	 * @param	bLoop					Loop animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quillscript|Media")
	static void PlayAnimation(USkeletalMeshComponent* SkeletalMeshComponent, UAnimationAsset* Animation, const bool bLoop = false);

	/**
	 * Calculate the typewriter speed based on the given text and the audio duration playing in the 'voice' channel.
	 */
	UFUNCTION(BlueprintPure, Category = "Quillscript|Media", meta = ( AdvancedDisplay = "DefaultDuration" ))
	float VoiceTypingSpeed(const float DefaultDuration = 0.02) const;

	#pragma endregion Media


	/// Helper
	#pragma region Helper

	UFUNCTION(BlueprintCallable, Category = "Helper", meta = ( AdvancedDisplay = "Quantity" ))
	static int32 Roll(const int32 DieSides, int32 Quantity = 1);

	#pragma endregion Helper


	/// Getters and Setters
	#pragma region GetSet

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UQuillscriptAsset* GetScript() const { return this->Script; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE int32 GetCurrentStatementIndex() const { return this->State.CurrentIndex; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE bool GetCanProceed() const { return this->State.bCanProceed; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UDialogBox* GetDialogBox() const { return this->DialogBox; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE USelectionBox* GetSelectionBox() const { return this->SelectionBox; }

	UFUNCTION(BlueprintGetter)
	FORCEINLINE UBackgroundBox* GetBackgroundBox() const { return this->BackgroundBox; }

	UFUNCTION(BlueprintPure, Category = "Quillscript|References")
	FORCEINLINE TMap<FName, USpriteBox*> GetSpriteBoxes() const { return this->SpriteBoxes; }

	UFUNCTION(BlueprintPure, Category = "Quillscript|Components")
	FORCEINLINE TMap<FName, UAudioComponent*> GetAudioComponents() const { return this->AudioComponents; }

	#pragma endregion GetSet


	/// Events
	#pragma region Events

	/** Statement has played event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FStatementPlayedDelegate OnStatementPlayed;

	/** Script started event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FScriptStartedDelegate OnStarted;

	/** Script started event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FScriptResumedDelegate OnResumed;

	/** Script ended event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FScriptEndedDelegate OnEnded;

	/** Dialogue Box played event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FPlayDialogueBoxDelegate OnPlayDialogueBox;

	/** Selection Box played event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FPlaySelectionBoxDelegate OnPlaySelectionBox;

	/** Background Box played event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FPlayBackgroundBoxDelegate OnPlayBackgroundBox;

	/** Audio finished event. */
	UPROPERTY(BlueprintAssignable, BlueprintCallable, Category = "Quillscript|Events")
	FAudioFinishedDelegate OnAudioFinished;

	#pragma endregion Events


protected:
	/// Components
	#pragma region Components

	/** Root component. */
	UPROPERTY(EditAnywhere, Category = "Quillscript|Components")
	TObjectPtr<USceneComponent> SceneComponent;

	/** Audio components used to play script sounds. (Channel -> Component) */
	UPROPERTY(BlueprintReadWrite, Category = "Quillscript|Components")
	TMap<FName, UAudioComponent*> AudioComponents;

	#pragma endregion Components


	/// References
	#pragma region References

	/** Quillscript asset used by this 'Scene'. */
	UPROPERTY(EditAnywhere, BlueprintGetter = GetScript, Category = "Quillscript|Scene")
	TObjectPtr<UQuillscriptAsset> Script;

	#if WITH_EDITORONLY_DATA

	/**
	 * Exact authored asset supplied to Start(). Runtime update must refresh
	 * from this object, not an ID lookup, because script IDs are not globally
	 * unique across Engine and project content.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UQuillscriptAsset> RuntimeSourceScript;

	#endif

	/** 'Dialog Box' Widget used by this 'Scene'. */
	UPROPERTY(BlueprintGetter = GetDialogBox, Category = "Quillscript|References")
	TObjectPtr<UDialogBox> DialogBox;

	/** 'Player Options' Widget used by this 'Scene'. */
	UPROPERTY(BlueprintGetter = GetSelectionBox, Category = "Quillscript|References")
	TObjectPtr<USelectionBox> SelectionBox;

	/** 'Background' Widget used by this 'Scene'. */
	UPROPERTY(BlueprintGetter = GetBackgroundBox, Category = "Quillscript|References")
	TObjectPtr<UBackgroundBox> BackgroundBox;

	/** 'Background' Widget used by this 'Scene'. */
	UPROPERTY(BlueprintReadWrite, Category = "Quillscript|References")
	TMap<FName, USpriteBox*> SpriteBoxes;

	#pragma endregion References


	/// State
	#pragma region State

	/** Group state data that should be snapshot. */
	FInterpreterState State;

	/** Mark if a label play is made by a router statement, and not by regular script flow. */
	bool bRouterCall{ false };

	/** Mark that a condition is open. */
	bool bConditionOpen{ false };

	#pragma endregion State


	/// Instructions
	#pragma region Instructions

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void PlayDialogueBox(const FStatement Dialogue);

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Quillscript|User Interface")
	void PlaySelectionBox(const TArray<FStatement> Options);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Instructions")
	virtual void ExecuteCommand(const FExpression CommandInstruction);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Instructions")
	virtual void ExecuteCommands(TArray<FExpression> CommandInstructions);

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Instructions")
	virtual void GoToTarget(const FName TargetLabel, TArray<FText> Arguments, const bool bChannel);

	#pragma endregion Instructions


	/// Customizers
	#pragma region Customizers

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Flow")
	void BeforeStart();
	virtual void BeforeStart_Implementation() {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Flow")
	void BeforeResume();
	virtual void BeforeResume_Implementation() {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Flow")
	void BeforePlay();
	virtual void BeforePlay_Implementation() {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Flow")
	void BeforeEnd();
	virtual void BeforeEnd_Implementation() {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayLabel(FStatement Label, const bool bDirectCall = false, const bool bCallback = true);
	virtual void BeforePlayLabel_Implementation(FStatement Label, const bool bDirectCall = false, const bool bCallback = true) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayDialogue(FStatement Dialogue);
	virtual void BeforePlayDialogue_Implementation(FStatement Dialogue) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayOption(TArray<FStatement>& Options);
	virtual void BeforePlayOption_Implementation(TArray<FStatement>& Options) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayCommand(FStatement Command);
	virtual void BeforePlayCommand_Implementation(FStatement Command) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayRouter(FStatement Router);
	virtual void BeforePlayRouter_Implementation(FStatement Router) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayCondition(FStatement Condition);
	virtual void BeforePlayCondition_Implementation(FStatement Condition) {}

	UFUNCTION(BlueprintNativeEvent, Category = "Quillscript|Statements")
	void BeforePlayDirective(FStatement Directive);
	virtual void BeforePlayDirective_Implementation(FStatement Directive) {}

	#pragma endregion Customizers


	/// Evaluation
	#pragma region Evaluation

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Evaluation")
	virtual bool EvaluateCondition(FExpression Condition) const;

	UFUNCTION(BlueprintCallable, Category = "Quillscript|Evaluation")
	virtual bool EvaluateConditions(const TArray<FExpression> Conditions) const;

	#pragma endregion Evaluation


	/// Tasks
	#pragma region Tasks

	/**
	 * Return if this scene is already started or resumed
	 */
	bool IsFresh() const;

	/**
	 * Stores the current state of the save variables.
	 */
	void Snapshot() const;

	/**
	 * Receive a function address from Quillscript and call the function on target.
	 */
	void CallFunction(const FString& FunctionAddress, TArray<FString> Parameters);

	#pragma endregion Tasks


	/// Internal Use
	#pragma region Internal

	/**
	 * Create a list with the options and dynamic options from the given raw options set.
	 */
	TArray<FStatement> CreateDynamicOptionsSet(const TArray<FStatement>& Options);

	/**
	 * Increment the times played counter in this script history.
	 */
	void IncrementTimesPlayed() const;

	/**
	 * Delete all temporary data, like temporary variables, references, etc.
	 */
	void DeleteTemporaryData() const;

	/**
	 * Create a Quillscript variable for each statement argument. (Starts with @)
	 */
	void CreateTemplateVariables(const FName Target, const TArray<FText> Arguments) const;

	/**
	 * Delete all argument Quillscript variables. (Starts with @)
	 */
	void DeleteTemplateVariables() const;

	void ApplyScriptSettingsDuring() const;
	void ApplyScriptSettingsAfter() const;

	/**
	 * Executed when a checkpoint directive is being evaluated timely.
	 */
	inline void EvaluateCheckpointDirective();

	FStatement CheckpointDirective;
	bool bEvaluateCheckpointDirectiveEveryFrame{ false };
	FTimerHandle TimerHandleRef;

	#pragma endregion Internal


private:
	/// Call Function
	#pragma region CallFunction

	/**
	 * Get a reference to the object in the last position of a properties' list like:
	 * RootObject.PropertyObject1.PropertyObject2
	 */
	UObject* GetObjectLastProperty(UObject* RootObject, TArray<FString> PropertiesList) const;

	TArray<UObject*> GetRootObjectsByName(const FString& RootObjectsName);
	TArray<UObject*> GetRootObjectsByClass(const FString& RootObjectsClassName);
	TArray<UObject*> GetRootObjectsByTag(const FString& RootObjectsTag) const;

	void CallMemberOnTarget(UObject* Target, const FString& MemberName, const TArray<FString>& Parameters);
	void CallFunctionOnTarget(UObject* Target, UFunction* Function, TArray<FString> Parameters);
	void CallPropertyOnTarget(UObject* Target, const FProperty* Property) const;

	/**
	 * Create a temporary Quillscript variable holding the value of an outer parameter.
	 * {$OuterParameterName}
	 */
	void CreateOuterQuillscriptVariable(const FString& Name, const FString& Value) const;

	#pragma endregion CallFunction


	/// Directives
	#pragma region Directives

	void ExecuteCheckpointDirective(const FStatement& Directive);

	#pragma endregion Directives


	/// Editor
	#if WITH_EDITOR

	void ReloadScript();

	#endif
};
