#include "MelodiaPersonaSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/TextBlock.h"
#include "Components/Widget.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "UObject/UObjectIterator.h"

namespace
{
	constexpr TCHAR PersonaContentPath[] = TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent.DA_MelodiaPersonaContent");

	/** Persona-lite social stats run 0..5. Persona owns this range; the narrative record just stores the value. */
	constexpr int32 MaxSocialStat = 5;

	constexpr TCHAR MelusinaUnitClassPath[] = TEXT("/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation.BP_MelusinaSwordsman_Presentation_C");

	// LEGACY fallback only. Every entry here is a piece of equipment that cannot be
	// authored without a C++ edit and a rebuild, which is why it never grew past
	// three. Author FMelodiaEquipmentDefinition::StockItemClass instead; this table
	// exists to keep already-authored StockItemAssetId content working and should
	// shrink to empty, not grow.
	const TMap<FName, FString> StockEquipmentPaths = {
		{TEXT("BP_Rod"), TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Items/Equipment/Weapons/BP_Rod.BP_Rod_C")},
		{TEXT("BP_LeatherArmor"), TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Items/Equipment/Armors/BP_LeatherArmor.BP_LeatherArmor_C")},
		{TEXT("BP_LeatherBoots"), TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Items/Equipment/Boots/BP_LeatherBoots.BP_LeatherBoots_C")},
	};

	/**
	 * One resolver for both equip paths. RequestEquip and HandleEquipmentRequested
	 * previously duplicated this lookup, so they could disagree about whether a
	 * definition was resolvable.
	 *
	 * Data-driven StockItemClass wins; the hardcoded table is the fallback.
	 */
	UClass* ResolveStockEquipmentClass(const FMelodiaEquipmentDefinition& Definition)
	{
		if (!Definition.StockItemClass.IsNull())
		{
			if (UClass* Loaded = Definition.StockItemClass.LoadSynchronous())
			{
				return Loaded;
			}
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_EQUIP '%s' StockItemClass '%s' failed to load; falling back to StockItemAssetId."),
				*Definition.EquipmentId.ToString(), *Definition.StockItemClass.ToString());
		}

		if (const FString* Path = StockEquipmentPaths.Find(Definition.StockItemAssetId))
		{
			return LoadClass<UObject>(nullptr, **Path);
		}

		if (!Definition.StockItemAssetId.IsNone())
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_EQUIP '%s' names StockItemAssetId '%s', which is not in the legacy path table. "
					 "Author StockItemClass on the definition instead of extending that table."),
				*Definition.EquipmentId.ToString(), *Definition.StockItemAssetId.ToString());
		}
		return nullptr;
	}

	/**
	 * Unit id -> stock unit class. Only Melusina resolves today; every other party
	 * member silently failed to equip because the null landed in a bStockContractReady
	 * check that did not distinguish "unknown unit" from "stock contract missing".
	 */
	UClass* ResolveUnitClass(const FName UnitId)
	{
		if (UnitId == TEXT("melusina"))
		{
			return LoadClass<UObject>(nullptr, MelusinaUnitClassPath);
		}
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_EQUIP unit '%s' has no stock unit class mapping; only 'melusina' is mapped. "
				 "Party equipment needs this widened before other members can equip."),
			*UnitId.ToString());
		return nullptr;
	}
}

void UMelodiaPersonaSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Content = LoadObject<UMelodiaPersonaContent>(nullptr, PersonaContentPath);
	if (!Content)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia Persona content is missing: %s"), PersonaContentPath);
	}

	Narrative = GetGameInstance()->GetSubsystem<UMelodiaNarrativeSubsystem>();
	if (Narrative)
	{
		Narrative->OnQuestRequested.AddUniqueDynamic(this, &ThisClass::HandleNarrativeQuest);
		Narrative->OnSocialStatRequested.AddUniqueDynamic(this, &ThisClass::HandleSocialStatRequested);
		Narrative->OnRewardRequested.AddUniqueDynamic(this, &ThisClass::HandleRewardRequested);
	}
	JRPGBridge = GetGameInstance()->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();
	if (JRPGBridge)
	{
		JRPGBridge->OnJRPGBattleStarted.AddUniqueDynamic(this, &ThisClass::HandleJRPGBattleStarted);
		JRPGBridge->OnJRPGBattleEnded.AddUniqueDynamic(this, &ThisClass::HandleJRPGBattleEnded);
	}
	OnEquipmentRequested.AddUniqueDynamic(this, &ThisClass::HandleEquipmentRequested);
}

void UMelodiaPersonaSubsystem::Deinitialize()
{
	OnEquipmentRequested.RemoveDynamic(this, &ThisClass::HandleEquipmentRequested);
	if (Narrative)
	{
		Narrative->OnQuestRequested.RemoveDynamic(this, &ThisClass::HandleNarrativeQuest);
		Narrative->OnSocialStatRequested.RemoveDynamic(this, &ThisClass::HandleSocialStatRequested);
		Narrative->OnRewardRequested.RemoveDynamic(this, &ThisClass::HandleRewardRequested);
	}
	if (JRPGBridge)
	{
		JRPGBridge->OnJRPGBattleStarted.RemoveDynamic(this, &ThisClass::HandleJRPGBattleStarted);
		JRPGBridge->OnJRPGBattleEnded.RemoveDynamic(this, &ThisClass::HandleJRPGBattleEnded);
	}
	JRPGBridge = nullptr;
	ActiveBridgeEncounterId = NAME_None;
	Narrative = nullptr;
	Content = nullptr;
	Super::Deinitialize();
}

UMelodiaPersonaSubsystem* UMelodiaPersonaSubsystem::Get(const UObject* WorldContextObject)
{
	if (!IsValid(WorldContextObject) || !WorldContextObject->GetWorld())
	{
		return nullptr;
	}
	UGameInstance* GI = WorldContextObject->GetWorld()->GetGameInstance();
	return GI ? GI->GetSubsystem<UMelodiaPersonaSubsystem>() : nullptr;
}

TArray<FMelodiaAbilityDefinition> UMelodiaPersonaSubsystem::GetAbilitiesForLevel(const int32 Level) const
{
	TArray<FMelodiaAbilityDefinition> Result;
	if (Content)
	{
		for (const FMelodiaAbilityDefinition& Ability : Content->Abilities)
		{
			if (Ability.UnlockLevel <= Level)
			{
				Result.Add(Ability);
			}
		}
	}
	return Result;
}

TArray<FMelodiaEquipmentDefinition> UMelodiaPersonaSubsystem::GetEquipmentDefinitions() const
{
	return Content ? Content->Equipment : TArray<FMelodiaEquipmentDefinition>();
}

bool UMelodiaPersonaSubsystem::RequestEquip(const FName UnitId, const FName EquipmentId)
{
	const FMelodiaEquipmentDefinition* Definition = Content ? Content->Equipment.FindByPredicate(
		[EquipmentId](const FMelodiaEquipmentDefinition& Entry) { return Entry.EquipmentId == EquipmentId; }) : nullptr;
	UClass* EquipmentClass = Definition ? ResolveStockEquipmentClass(*Definition) : nullptr;
	UClass* UnitClass = ResolveUnitClass(UnitId);
	APlayerController* Controller = GetWorld() ? UGameplayStatics::GetPlayerController(GetWorld(), 0) : nullptr;
	const bool bStockContractReady = Controller
		&& EquipmentClass
		&& UnitClass
		&& Controller->FindFunction(TEXT("AddEquipmentToInventory"))
		&& Controller->FindFunction(TEXT("WearEquipmentOnUnit"));

	if (!Definition || !bStockContractReady)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("Persona equip request rejected before dispatch: unit=%s equipment=%s definition=%d controller=%d item_class=%d unit_class=%d"),
			*UnitId.ToString(), *EquipmentId.ToString(), Definition ? 1 : 0, Controller ? 1 : 0,
			EquipmentClass ? 1 : 0, UnitClass ? 1 : 0);
		return false;
	}

	OnEquipmentRequested.Broadcast(UnitId, EquipmentId);
	return true;
}

const FMelodiaQuestDefinition* UMelodiaPersonaSubsystem::FindQuest(const FName QuestId) const
{
	return Content ? Content->Quests.FindByPredicate(
		[QuestId](const FMelodiaQuestDefinition& Quest) { return Quest.QuestId == QuestId; }) : nullptr;
}

bool UMelodiaPersonaSubsystem::IsQuestComplete(const FName QuestId) const
{
	if (QuestId.IsNone())
	{
		return true;
	}
	const FMelodiaQuestDefinition* Quest = FindQuest(QuestId);
	return Narrative && Quest && Narrative->GetNarrativeRecord().Flags.FindRef(Quest->CompletionFlagId);
}

EMelodiaQuestState UMelodiaPersonaSubsystem::GetQuestState(const FName QuestId) const
{
	const FMelodiaQuestDefinition* Quest = FindQuest(QuestId);
	if (!Quest)
	{
		return EMelodiaQuestState::Locked;
	}
	if (IsQuestComplete(QuestId))
	{
		return EMelodiaQuestState::Completed;
	}
	if (Narrative && Narrative->GetNarrativeRecord().ActiveQuestIds.Contains(QuestId))
	{
		return EMelodiaQuestState::Active;
	}

	const bool bQuestPrerequisiteMet = IsQuestComplete(Quest->PrerequisiteQuestId);
	const bool bSocialStatMet = Quest->RequiredSocialStatId.IsNone()
		|| GetSocialStat(Quest->RequiredSocialStatId) >= Quest->RequiredSocialStatValue;
	return bQuestPrerequisiteMet && bSocialStatMet
		? EMelodiaQuestState::Available
		: EMelodiaQuestState::Locked;
}

TArray<FMelodiaQuestDefinition> UMelodiaPersonaSubsystem::GetAvailableQuests() const
{
	TArray<FMelodiaQuestDefinition> Result;
	if (Content)
	{
		for (const FMelodiaQuestDefinition& Quest : Content->Quests)
		{
			const EMelodiaQuestState State = GetQuestState(Quest.QuestId);
			if (State == EMelodiaQuestState::Available || State == EMelodiaQuestState::Active)
			{
				Result.Add(Quest);
			}
		}
	}
	return Result;
}

bool UMelodiaPersonaSubsystem::AcceptQuest(const FName QuestId)
{
	if (GetQuestState(QuestId) != EMelodiaQuestState::Available)
	{
		return false;
	}
	if (!Narrative || !Narrative->SetQuestActive(QuestId, true))
	{
		return false;
	}
	OnQuestStateChanged.Broadcast(QuestId, EMelodiaQuestState::Active);
	RefreshMinimapWidgets();
	return true;
}

bool UMelodiaPersonaSubsystem::CompleteQuest(const FName QuestId)
{
	const FMelodiaQuestDefinition* Quest = FindQuest(QuestId);
	if (!Quest || !Narrative || GetQuestState(QuestId) != EMelodiaQuestState::Active ||
		!Narrative->SetNarrativeFlag(Quest->CompletionFlagId, true))
	{
		return false;
	}
	Narrative->SetQuestActive(QuestId, false);
	OnQuestStateChanged.Broadcast(QuestId, EMelodiaQuestState::Completed);
	RefreshMinimapWidgets();
	if (!Quest->RewardId.IsNone())
	{
		Narrative->GrantDialogueReward(Quest->RewardId);
	}
	return true;
}

int32 UMelodiaPersonaSubsystem::GetSocialStat(const FName StatId) const
{
	return Narrative ? Narrative->GetSocialStat(StatId) : 0;
}

int32 UMelodiaPersonaSubsystem::AddSocialStat(const FName StatId, const int32 Delta)
{
	if (StatId.IsNone() || Delta == 0)
	{
		return GetSocialStat(StatId);
	}

	if (!Narrative)
	{
		// Without the narrative record there is nowhere durable to put this.
		// Refuse rather than bank it somewhere that will not survive a reload.
		UE_LOG(LogTemp, Warning, TEXT("Melodia Persona social stat '%s' dropped: narrative subsystem unavailable."), *StatId.ToString());
		return 0;
	}

	// Persona owns the 0..MaxSocialStat range; the record is dumb storage.
	// Compute the clamped target first so the record never holds an out-of-range
	// value even briefly.
	const int32 Current = Narrative->GetSocialStat(StatId);
	const int32 Target = FMath::Clamp(Current + Delta, 0, MaxSocialStat);
	const int32 Value = Narrative->AddSocialStat(StatId, Target - Current);

	OnSocialStatChanged.Broadcast(StatId, Value);
	RefreshMinimapWidgets();
	return Value;
}

void UMelodiaPersonaSubsystem::HandleSocialStatRequested(const FName StatId, const int32 Delta)
{
	// Narrative already checked the allowlist and consumed the intent once.
	AddSocialStat(StatId, Delta);
}

bool UMelodiaPersonaSubsystem::IsGatedContentAvailable(const FName RequiredQuestId) const
{
	return RequiredQuestId.IsNone() || GetQuestState(RequiredQuestId) == EMelodiaQuestState::Active;
}

TArray<FMelodiaMinimapMarkerDefinition> UMelodiaPersonaSubsystem::GetVisibleMinimapMarkers() const
{
	TArray<FMelodiaMinimapMarkerDefinition> Result;
	if (Content)
	{
		for (const FMelodiaMinimapMarkerDefinition& Marker : Content->MinimapMarkers)
		{
			if (IsGatedContentAvailable(Marker.RequiredQuestId))
			{
				Result.Add(Marker);
			}
		}
	}
	return Result;
}

void UMelodiaPersonaSubsystem::HandleRewardRequested(const FName RewardId)
{
	const FName* EquipmentId = Content ? Content->RewardEquipment.Find(RewardId) : nullptr;
	if (!EquipmentId || EquipmentId->IsNone())
	{
		// Narrative-only reward, or an unmapped one. Either way the id is already
		// consumed upstream, so say so rather than letting it vanish silently.
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_REWARD '%s' granted with no equipment mapping (content=%d). "
				 "Add an entry to UMelodiaPersonaContent::RewardEquipment if it should equip something."),
			*RewardId.ToString(), Content ? 1 : 0);
		return;
	}

	// Melusina is the only unit the persona layer equips today; RequestEquip
	// already rejects and logs when the stock controller contract is unavailable.
	const bool bEquipped = RequestEquip(TEXT("melusina"), *EquipmentId);
	UE_LOG(LogTemp, Log, TEXT("MELODIA_REWARD '%s' -> equipment '%s' equipped=%s"),
		*RewardId.ToString(), *EquipmentId->ToString(), bEquipped ? TEXT("true") : TEXT("false"));
}

void UMelodiaPersonaSubsystem::HandleNarrativeQuest(const FName QuestId)
{
	const EMelodiaQuestState State = GetQuestState(QuestId);
	if (State == EMelodiaQuestState::Available)
	{
		AcceptQuest(QuestId);
	}
	else if (State == EMelodiaQuestState::Active)
	{
		CompleteQuest(QuestId);
	}
}

void UMelodiaPersonaSubsystem::HandleJRPGBattleStarted(const FName EncounterId)
{
	ActiveBridgeEncounterId = EncounterId;
}

void UMelodiaPersonaSubsystem::HandleJRPGBattleEnded(const uint8 BattleResult)
{
	// Battle completion belongs to UMelodiaNarrativeSubsystem, which maps the
	// typed result back to Quill exactly once. Quest progression is authored by
	// the resumed Quill scene (the Smoke victory branch emits the quest intent);
	// this presentation observer must not create an encounter-specific second
	// quest authority.
	UE_LOG(LogTemp, Verbose,
		TEXT("Melodia Persona observed stock battle end encounter=%s result=%u; quest progression remains authored in Quill."),
		*ActiveBridgeEncounterId.ToString(), static_cast<uint32>(BattleResult));
	ActiveBridgeEncounterId = NAME_None;
}

void UMelodiaPersonaSubsystem::RefreshMinimapWidgets() const
{
	const EMelodiaQuestState EchoOneState = GetQuestState(TEXT("melodia_q_echo_01"));
	const EMelodiaQuestState EchoTwoState = GetQuestState(TEXT("melodia_q_echo_02"));
	const EMelodiaQuestState EchoThreeState = GetQuestState(TEXT("melodia_q_echo_03"));
	const bool bPriestessVisible = EchoOneState == EMelodiaQuestState::Available || EchoOneState == EMelodiaQuestState::Active;
	const bool bStarWeaverVisible = EchoTwoState == EMelodiaQuestState::Available || EchoTwoState == EMelodiaQuestState::Active;
	const bool bEchoVisible = EchoTwoState == EMelodiaQuestState::Active;
	const bool bExitVisible = EchoThreeState == EMelodiaQuestState::Active;
	const FMelodiaQuestDefinition* JournalQuest = nullptr;
	if (Content)
	{
		for (const FMelodiaQuestDefinition& Quest : Content->Quests)
		{
			if (GetQuestState(Quest.QuestId) == EMelodiaQuestState::Active)
			{
				JournalQuest = &Quest;
				break;
			}
		}
	}
	for (TObjectIterator<UUserWidget> It; It; ++It)
	{
		UUserWidget* Widget = *It;
		if (!IsValid(Widget) || Widget->GetWorld() != GetWorld() || !Widget->WidgetTree)
		{
			continue;
		}
		if (UWidget* Echo = Widget->WidgetTree->FindWidget(TEXT("Marker_RhythmEcho")))
		{
			Echo->SetVisibility(bEchoVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
		if (UWidget* Exit = Widget->WidgetTree->FindWidget(TEXT("Marker_ForestExit")))
		{
			Exit->SetVisibility(bExitVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
		if (UWidget* Priestess = Widget->WidgetTree->FindWidget(TEXT("Marker_PetalPriestess")))
		{
			Priestess->SetVisibility(bPriestessVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
		if (UWidget* StarWeaver = Widget->WidgetTree->FindWidget(TEXT("Marker_StarWeaver")))
		{
			StarWeaver->SetVisibility(bStarWeaverVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		}
		if (UTextBlock* JournalResonance = Cast<UTextBlock>(Widget->WidgetTree->FindWidget(TEXT("JournalResonance"))))
		{
			const FText QuestText = JournalQuest
				? JournalQuest->DisplayName
				: FText::FromString(TEXT("Resonance Journal"));
			JournalResonance->SetText(FText::Format(
				FText::FromString(TEXT("Harmony {0}/5  ·  {1}")),
				FText::AsNumber(GetSocialStat(TEXT("melodia_harmony"))),
				QuestText));
		}
		if (UTextBlock* JournalObjective = Cast<UTextBlock>(Widget->WidgetTree->FindWidget(TEXT("JournalObjective"))))
		{
			JournalObjective->SetText(JournalQuest ? JournalQuest->Objective : FText::FromString(TEXT("Listen for the next story thread.")));
		}
	}
}

void UMelodiaPersonaSubsystem::HandleEquipmentRequested(const FName UnitId, const FName EquipmentId)
{
	const FMelodiaEquipmentDefinition* Definition = Content ? Content->Equipment.FindByPredicate(
		[EquipmentId](const FMelodiaEquipmentDefinition& Entry) { return Entry.EquipmentId == EquipmentId; }) : nullptr;
	if (!Definition)
	{
		return;
	}

	UClass* EquipmentClass = ResolveStockEquipmentClass(*Definition);
	UClass* UnitClass = ResolveUnitClass(UnitId);
	APlayerController* Controller = GetWorld() ? UGameplayStatics::GetPlayerController(GetWorld(), 0) : nullptr;
	if (!Controller || !EquipmentClass || !UnitClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Persona equip request could not resolve stock authority: unit=%s equipment=%s stock=%s"),
			*UnitId.ToString(), *EquipmentId.ToString(), *Definition->StockItemAssetId.ToString());
		return;
	}

	// This is the REWARD-GRANT path. Both stock calls below used to be bare
	// `if (FindFunction(...))` with no else, so renaming either Blueprint function
	// consumed the reward and silently dropped the equip -- the reward is gone and
	// the item never arrives. RequestEquip already validated both up front; this
	// path did not. Report the miss rather than returning as if it worked.
	UFunction* AddToInventory = Controller->FindFunction(TEXT("AddEquipmentToInventory"));
	UFunction* WearEquipment = Controller->FindFunction(TEXT("WearEquipmentOnUnit"));
	if (!AddToInventory || !WearEquipment)
	{
		UE_LOG(LogTemp, Error,
			TEXT("MELODIA_EQUIP stock contract missing on the reward path: unit=%s equipment=%s "
				 "AddEquipmentToInventory=%d WearEquipmentOnUnit=%d. The reward was consumed but nothing was equipped. "
				 "These are Blueprint functions on the PlayerController, resolved by name -- check for a rename."),
			*UnitId.ToString(), *EquipmentId.ToString(),
			AddToInventory != nullptr, WearEquipment != nullptr);
		return;
	}

	{
		struct FAddEquipmentParams
		{
			UClass* Equipment = nullptr;
			int32 Amount = 1;
		} Params;
		Params.Equipment = EquipmentClass;
		Controller->ProcessEvent(AddToInventory, &Params);
	}

	{
		struct FWearEquipmentParams
		{
			UClass* PlayerUnit = nullptr;
			UClass* Equipment = nullptr;
		} Params;
		Params.PlayerUnit = UnitClass;
		Params.Equipment = EquipmentClass;
		Controller->ProcessEvent(WearEquipment, &Params);
	}
}
