#include "MonolithStatActions.h"
#include "MonolithParamSchema.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "HAL/PlatformTime.h"

#if STATS
#include "Stats/StatsData.h"
#include "Stats/StatsCommand.h"
#include "Stats/StatsSystemTypes.h"
#endif

DEFINE_LOG_CATEGORY_STATIC(LogMonolithStat, Log, All);

#if STATS
namespace
{
	// Normalise a user-supplied group name into the two forms the stats system uses:
	//   - the STATGROUP_-prefixed FName key used in FStatsThreadState::Groups
	//     (e.g. "STATGROUP_Anim"), and
	//   - the bare short name the `stat <group>` console/DirectStatsCommand syntax expects
	//     (e.g. "Anim").
	// Accepts either form on input.
	void NormaliseGroupName(const FString& Input, FName& OutGroupKey, FString& OutShortName)
	{
		FString Trimmed = Input.TrimStartAndEnd();
		FString Short = Trimmed;
		Short.RemoveFromStart(TEXT("STATGROUP_"));
		OutShortName = Short;
		OutGroupKey = FName(*(FString(TEXT("STATGROUP_")) + Short));
	}

	// IItemFilter that keeps only the stat messages belonging to a known set of raw FNames
	// (the group's stats, both short and long names). Mirrors the engine's FGroupFilter Keep()
	// minus the hierarchy root-filter bookkeeping (we read flat inclusive aggregates, no roots).
	struct FGroupItemFilter : public IItemFilter
	{
		const TSet<FName>& EnabledItems;
		explicit FGroupItemFilter(const TSet<FName>& InEnabledItems) : EnabledItems(InEnabledItems) {}
		virtual bool Keep(FStatMessage const& Item) override
		{
			return EnabledItems.Contains(Item.NameAndInfo.GetRawName());
		}
	};

	// Build the set of raw FNames that belong to a group, mirroring the engine's
	// GetStatsForGroup/GetStatsForNames: for each short name in Groups[GroupKey], add the short
	// name and its long (raw) name from ShortNameToLongName.
	void BuildGroupItemSet(const FStatsThreadState& Stats, const FName GroupKey, TSet<FName>& OutItems)
	{
		OutItems.Reset();
		TArray<FName> ShortNames;
		Stats.Groups.MultiFind(GroupKey, ShortNames);
		for (const FName& ShortName : ShortNames)
		{
			OutItems.Add(ShortName);
			if (const FStatMessage* LongName = Stats.ShortNameToLongName.Find(ShortName))
			{
				OutItems.Add(LongName->NameAndInfo.GetRawName());
			}
		}
	}

	// Running per-stat accumulator across the sampled frame window. Counters and cycle timings
	// are tracked separately because they read different payloads.
	struct FStatAccumulator
	{
		FString ShortName;
		bool bIsCycle = false;     // cycle timing (ms) vs a plain counter
		bool bIsDouble = false;    // ST_double counter (only when !bIsCycle)

		int32 SampleCount = 0;
		double Min = 0.0;
		double Max = 0.0;
		double Sum = 0.0;

		void Add(double Value)
		{
			if (SampleCount == 0) { Min = Max = Value; }
			else { Min = FMath::Min(Min, Value); Max = FMath::Max(Max, Value); }
			Sum += Value;
			++SampleCount;
		}
	};

	// Convert one aggregated FStatMessage into a sample value, classifying it as a cycle timing
	// (returned in milliseconds) or a counter (int64/double). Returns false for message types we
	// do not surface (FName/Ptr/None).
	bool ReadStatSample(const FStatMessage& Message, double& OutValue, bool& bOutIsCycle, bool& bOutIsDouble)
	{
		const EStatDataType::Type DataType = Message.NameAndInfo.GetField<EStatDataType>();
		const bool bIsCycle = Message.NameAndInfo.GetFlag(EStatMetaFlags::IsCycle);

		if (bIsCycle && DataType == EStatDataType::ST_int64)
		{
			const int64 Cycles = Message.GetValue_Duration();
			OutValue = FPlatformTime::ToMilliseconds64(static_cast<uint64>(Cycles));
			bOutIsCycle = true;
			bOutIsDouble = false;
			return true;
		}
		if (DataType == EStatDataType::ST_int64)
		{
			OutValue = static_cast<double>(Message.GetValue_int64());
			bOutIsCycle = false;
			bOutIsDouble = false;
			return true;
		}
		if (DataType == EStatDataType::ST_double)
		{
			OutValue = Message.GetValue_double();
			bOutIsCycle = false;
			bOutIsDouble = true;
			return true;
		}
		return false; // ST_FName / ST_Ptr / ST_None — not surfaced
	}
}
#endif // STATS

void FMonolithStatActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("editor"), TEXT("get_stat_group_values"),
		TEXT("Read the values of a stats group programmatically into a structured response. Enables high-performance collection for the named stat group, "
		     "reads the most recent settled stat frame(s) from the stats thread, and returns each stat's counter value (int64/double) and cycle-stat timing "
		     "in milliseconds. group_name accepts either the full STATGROUP_ name (e.g. 'STATGROUP_Anim') or the short form (e.g. 'Anim'); project-defined "
		     "groups work the same way. sample_frames (default 1; >1 aggregates min/avg/max per stat over the last N already-settled frames in the stats "
		     "history ring). Cycle stats are reported as milliseconds; counters as their raw numeric value. A group this action enables is disabled again on "
		     "completion (a group already collecting is left as-is). REQUIRES the engine STATS system, compiled into Development editor builds but NOT "
		     "Shipping/Test — off-gate this returns a clean 'stats system not compiled in' error. IMPORTANT: this reads the LIVE stats stream, which only "
		     "produces frame data while overall stats collection is primary-enabled. Enabling a group alone does not start the stats thread producing frames; "
		     "for reliable data have stats already active (PIE running with an on-screen stat, or call run_console_command('stat <group>') first). If no "
		     "settled frame exists yet this returns settled=false with zero stats — retry once the editor/PIE has advanced a frame with collection active."),
		FMonolithActionHandler::CreateStatic(&HandleGetStatGroupValues),
		FParamSchemaBuilder()
			.Required(TEXT("group_name"), TEXT("string"), TEXT("Stat group name, full ('STATGROUP_Anim') or short ('Anim')."))
			.Optional(TEXT("sample_frames"), TEXT("number"), TEXT("Number of recent settled frames to aggregate (default 1). >1 returns per-stat min/avg/max over the window. Clamped to the stats history depth."), TEXT("1"))
			.Build());

	UE_LOG(LogMonolithStat, Log, TEXT("MonolithEditor: registered 1 stat-group readout action"));
}

#if STATS

FMonolithActionResult FMonolithStatActions::HandleGetStatGroupValues(const TSharedPtr<FJsonObject>& Params)
{
	FString GroupNameRaw;
	if (!Params->TryGetStringField(TEXT("group_name"), GroupNameRaw) || GroupNameRaw.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("get_stat_group_values requires 'group_name' (e.g. 'STATGROUP_Anim' or 'Anim')"));
	}

	int32 SampleFrames = 1;
	{
		double Frames = 1.0;
		if (Params->TryGetNumberField(TEXT("sample_frames"), Frames)) { SampleFrames = static_cast<int32>(Frames); }
	}
	// Guard against a pathological window. The stats history ring is small; clamp to a sane cap
	// and reject absurd requests rather than spinning over a huge range.
	if (SampleFrames < 1) { SampleFrames = 1; }
	if (SampleFrames > 240)
	{
		return FMonolithActionResult::Error(TEXT("sample_frames too large (max 240) — the stats history ring only retains a small number of frames"));
	}

	FName GroupKey;
	FString GroupShort;
	NormaliseGroupName(GroupNameRaw, GroupKey, GroupShort);

	FStatsThreadState& Stats = FStatsThreadState::GetLocalState();

	// Determine whether the group already had stats registered (so we only disable a group we
	// ourselves enabled). A group with no registered stats yet will populate after enable.
	const bool bGroupKnownBefore = Stats.Groups.Contains(GroupKey);

	// Enable collection for the group. DirectStatsCommand expects the leading "stat" token; the
	// group-enable subcommand takes the SHORT name (the console form strips STATGROUP_).
	const FString EnableCmd = FString::Printf(TEXT("stat group enable %s"), *GroupShort);
	UE::Stats::DirectStatsCommand(*EnableCmd, /*bBlockForCompletion=*/true);

	// Re-fetch the local state (it is a singleton; enabling may have registered the group).
	const int64 LatestFrame = Stats.GetLatestValidFrame();
	const int64 OldestFrame = Stats.GetOldestValidFrame();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("group_name"), GroupKey.ToString());
	Root->SetStringField(TEXT("group_short"), GroupShort);

	auto DisableIfWeEnabled = [&]()
	{
		// Only disable when WE turned the group on (it was unknown before). A group that was
		// already collecting is left as the user had it.
		if (!bGroupKnownBefore)
		{
			const FString DisableCmd = FString::Printf(TEXT("stat group disable %s"), *GroupShort);
			UE::Stats::DirectStatsCommand(*DisableCmd, /*bBlockForCompletion=*/true);
		}
	};

	if (LatestFrame <= 0 || OldestFrame <= 0)
	{
		// No settled frame yet — typical immediately after enabling a fresh group.
		Root->SetBoolField(TEXT("settled"), false);
		Root->SetNumberField(TEXT("frames_sampled"), 0);
		Root->SetArrayField(TEXT("stats"), TArray<TSharedPtr<FJsonValue>>());
		Root->SetStringField(TEXT("note"),
			TEXT("No settled stat frame available yet — the group was likely just enabled. Retry after the editor/PIE has advanced at least one frame."));
		DisableIfWeEnabled();
		return FMonolithActionResult::Success(Root);
	}

	// Build the group's item-name set once (the group registration is stable across frames).
	TSet<FName> GroupItems;
	BuildGroupItemSet(Stats, GroupKey, GroupItems);
	if (GroupItems.Num() == 0)
	{
		Root->SetBoolField(TEXT("settled"), true);
		Root->SetNumberField(TEXT("frames_sampled"), 0);
		Root->SetArrayField(TEXT("stats"), TArray<TSharedPtr<FJsonValue>>());
		Root->SetStringField(TEXT("note"),
			FString::Printf(TEXT("Group '%s' has no registered stats (unknown group name, or no stat in that group has executed yet)."), *GroupKey.ToString()));
		DisableIfWeEnabled();
		return FMonolithActionResult::Success(Root);
	}

	// Aggregate across the last N already-settled frames in the history ring. We do NOT advance
	// frames ourselves (a synchronous handler cannot tick the editor); instead we read what the
	// stats thread has already accumulated. The window is clamped to the available history.
	const int64 AvailableFrames = LatestFrame - OldestFrame + 1;
	const int64 WindowFrames = FMath::Clamp<int64>(SampleFrames, 1, AvailableFrames);
	const int64 FirstFrame = LatestFrame - WindowFrames + 1;

	TMap<FName, FStatAccumulator> Accumulators;
	int32 FramesActuallySampled = 0;

	for (int64 Frame = FirstFrame; Frame <= LatestFrame; ++Frame)
	{
		if (!Stats.IsFrameValid(Frame))
		{
			continue;
		}

		FGroupItemFilter Filter(GroupItems);
		TArray<FStatMessage> Aggregated;
		Stats.GetInclusiveAggregateStackStats(Frame, Aggregated, &Filter, /*bAddNonStackStats=*/true);
		++FramesActuallySampled;

		for (const FStatMessage& Message : Aggregated)
		{
			double Value = 0.0;
			bool bIsCycle = false;
			bool bIsDouble = false;
			if (!ReadStatSample(Message, Value, bIsCycle, bIsDouble))
			{
				continue;
			}

			const FName RawName = Message.NameAndInfo.GetRawName();
			FStatAccumulator& Acc = Accumulators.FindOrAdd(RawName);
			if (Acc.SampleCount == 0)
			{
				Acc.ShortName = Message.NameAndInfo.GetShortName().GetPlainNameString();
				Acc.bIsCycle = bIsCycle;
				Acc.bIsDouble = bIsDouble;
			}
			Acc.Add(Value);
		}
	}

	// Emit. For a single-frame window we report a flat "value"; for a multi-frame window we
	// report min/avg/max. Cycle stats carry a "unit":"ms"; counters carry "unit":"count".
	TArray<TSharedPtr<FJsonValue>> StatsArr;
	StatsArr.Reserve(Accumulators.Num());
	for (const TPair<FName, FStatAccumulator>& Pair : Accumulators)
	{
		const FStatAccumulator& Acc = Pair.Value;
		TSharedPtr<FJsonObject> StatObj = MakeShared<FJsonObject>();
		StatObj->SetStringField(TEXT("name"), Acc.ShortName);
		StatObj->SetStringField(TEXT("kind"), Acc.bIsCycle ? TEXT("cycle") : TEXT("counter"));
		StatObj->SetStringField(TEXT("unit"), Acc.bIsCycle ? TEXT("ms") : TEXT("count"));
		StatObj->SetNumberField(TEXT("samples"), Acc.SampleCount);

		if (WindowFrames <= 1)
		{
			StatObj->SetNumberField(TEXT("value"), Acc.Sum); // single sample => Sum == the value
		}
		else
		{
			const double Avg = Acc.SampleCount > 0 ? (Acc.Sum / Acc.SampleCount) : 0.0;
			StatObj->SetNumberField(TEXT("min"), Acc.Min);
			StatObj->SetNumberField(TEXT("avg"), Avg);
			StatObj->SetNumberField(TEXT("max"), Acc.Max);
		}
		StatsArr.Add(MakeShared<FJsonValueObject>(StatObj));
	}

	Root->SetBoolField(TEXT("settled"), true);
	Root->SetNumberField(TEXT("frames_sampled"), FramesActuallySampled);
	Root->SetNumberField(TEXT("requested_frames"), SampleFrames);
	Root->SetNumberField(TEXT("latest_frame"), static_cast<double>(LatestFrame));
	Root->SetArrayField(TEXT("stats"), StatsArr);

	DisableIfWeEnabled();
	return FMonolithActionResult::Success(Root);
}

#else // !STATS

FMonolithActionResult FMonolithStatActions::HandleGetStatGroupValues(const TSharedPtr<FJsonObject>& /*Params*/)
{
	return FMonolithActionResult::Error(
		TEXT("get_stat_group_values is unavailable: the engine STATS system is not compiled in this build configuration "
		     "(STATS is defined in Development editor builds, not Shipping/Test). Run from a Development editor build."));
}

#endif // STATS
