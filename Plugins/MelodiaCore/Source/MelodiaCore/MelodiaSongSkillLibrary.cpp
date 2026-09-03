#include "MelodiaSongSkillLibrary.h"
#include "MelodiaSongDataAsset.h"

namespace
{
FMelodiaSongSkillRecipe MakeSkill(
	const FName SkillId,
	const TCHAR* Name,
	const TCHAR* Desc,
	const EMelodiaSpellElement Element,
	const EMelodiaInstrument Instrument,
	const int32 Level,
	const TArray<int32>& Pitches,
	const TArray<float>& Durations,
	const float PowerScalar = 1.0f)
{
	FMelodiaSongSkillRecipe Skill;
	Skill.SkillId = SkillId;
	Skill.DisplayName = FText::FromString(Name);
	Skill.Description = FText::FromString(Desc);
	Skill.Element = Element;
	Skill.Instrument = Instrument;
	Skill.MechanicLevelRequired = Level;
	Skill.NotePitches = Pitches;
	Skill.NoteDurations = Durations;
	Skill.PowerScalar = PowerScalar;

	FMelodiaSongMaterialInput Material;
	Material.MaterialId = TEXT("DemoShard");
	Material.RarityTier = FMath::Clamp(1 + Level / 8, 1, 4);
	Material.PowerModifier = 1.0f + static_cast<float>(Level) * 0.02f;
	Skill.Materials.Add(Material);
	return Skill;
}

EMelodiaSpellElement ElementForLevel(const int32 Level)
{
	const int32 Index = (Level - 1) % 7;
	return static_cast<EMelodiaSpellElement>(Index);
}

EMelodiaInstrument InstrumentForLevel(const int32 Level)
{
	const int32 Index = (Level - 1) % 5;
	return static_cast<EMelodiaInstrument>(Index);
}

static UMelodiaSongDataAsset* G_SongDataAsset = nullptr;
}

void UMelodiaSongSkillLibrary::SetSongDataAsset(UMelodiaSongDataAsset* InAsset)
{
	G_SongDataAsset = InAsset;
	GetCachedSkills().Empty();
	GetCachedSkillMap().Empty();
}

UMelodiaSongDataAsset* UMelodiaSongSkillLibrary::GetSongDataAsset()
{
	return G_SongDataAsset;
}

TArray<FMelodiaSongSkillRecipe>& UMelodiaSongSkillLibrary::GetCachedSkills()
{
	static TArray<FMelodiaSongSkillRecipe> CachedSkills;
	return CachedSkills;
}

TMap<FName, FMelodiaSongSkillRecipe>& UMelodiaSongSkillLibrary::GetCachedSkillMap()
{
	static TMap<FName, FMelodiaSongSkillRecipe> CachedMap;
	return CachedMap;
}

TArray<FMelodiaSongSkillRecipe> UMelodiaSongSkillLibrary::BuildDemoSongSkills()
{
	TArray<FMelodiaSongSkillRecipe>& Cache = GetCachedSkills();
	if (!Cache.IsEmpty())
	{
		return Cache;
	}

	// If a data asset is set, use it
	if (G_SongDataAsset)
	{
		for (const FMelodiaSongChart& Chart : G_SongDataAsset->Songs)
		{
			for (const FMelodiaSongSkillRecipe& Variant : Chart.SkillVariants)
			{
				Cache.Add(Variant);
			}
		}
		for (const auto& Pair : G_SongDataAsset->SkillOverrides)
		{
			// Override or add specific skills
			bool bFound = false;
			for (FMelodiaSongSkillRecipe& Skill : Cache)
			{
				if (Skill.SkillId == Pair.Key)
				{
					Skill = Pair.Value;
					bFound = true;
					break;
				}
			}
			if (!bFound)
			{
				Cache.Add(Pair.Value);
			}
		}

		if (!Cache.IsEmpty())
		{
			// Build lookup map
			GetCachedSkillMap().Empty();
			for (const FMelodiaSongSkillRecipe& Skill : Cache)
			{
				GetCachedSkillMap().Add(Skill.SkillId, Skill);
			}
			return Cache;
		}
	}

	// Fallback: hardcoded demo skills
	Cache.Reserve(30);

	struct FSkillRow
	{
		FName Id;
		const TCHAR* Name;
		const TCHAR* Desc;
		int32 PitchPattern[4];
		float DurationPattern[4];
		int32 NoteCount;
	};

	const FSkillRow Rows[30] = {
		{ TEXT("Skill_Lv01_StarlitPing"), TEXT("Starlit Ping"), TEXT("Two-note opener on the music box."), { 60, 64, -1, -1 }, { 1.0f, 1.0f, 0.0f, 0.0f }, 2 },
		{ TEXT("Skill_Lv02_MoonStep"), TEXT("Moon Step"), TEXT("Gentle waltz triplet."), { 57, 60, 64, -1 }, { 0.75f, 0.75f, 1.0f, 0.0f }, 3 },
		{ TEXT("Skill_Lv03_CherryArpeggio"), TEXT("Cherry Arpeggio"), TEXT("Ascending cherry-blossom run."), { 60, 64, 67, 72 }, { 0.5f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv04_WhisperPulse"), TEXT("Whisper Pulse"), TEXT("Syncopated pool echo."), { 55, 58, 62, 65 }, { 0.5f, 0.5f, 0.75f, 0.75f }, 4 },
		{ TEXT("Skill_Lv05_GoldStuccoStrike"), TEXT("Gold Stucco Strike"), TEXT("Colonnade power chord."), { 48, 55, 62, 67 }, { 1.0f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv06_EscherClimb"), TEXT("Escher Climb"), TEXT("Staircase violin motif."), { 62, 65, 69, 74 }, { 0.5f, 0.5f, 0.5f, 1.25f }, 4 },
		{ TEXT("Skill_Lv07_GravityDrop"), TEXT("Gravity Drop"), TEXT("Heavy drum downbeat."), { 36, 43, 48, 55 }, { 1.0f, 0.25f, 0.25f, 1.0f }, 4 },
		{ TEXT("Skill_Lv08_TessellationWave"), TEXT("Tessellation Wave"), TEXT("Companion-unlock mosaic pattern."), { 60, 63, 67, 70 }, { 0.5f, 0.5f, 0.5f, 0.5f }, 4 },
		{ TEXT("Skill_Lv09_RecursiveLoop"), TEXT("Recursive Loop"), TEXT("Self-echoing harp figure."), { 64, 67, 71, 76 }, { 0.75f, 0.25f, 0.75f, 1.0f }, 4 },
		{ TEXT("Skill_Lv10_SpiralFanfare"), TEXT("Spiral Fanfare"), TEXT("Tower trumpet call."), { 67, 71, 74, 79 }, { 0.5f, 0.5f, 0.5f, 1.5f }, 4 },
		{ TEXT("Skill_Lv11_BaroqueCourante"), TEXT("Baroque Courante"), TEXT("Tier III dance in 3."), { 58, 62, 65, 70 }, { 0.66f, 0.66f, 0.66f, 1.0f }, 4 },
		{ TEXT("Skill_Lv12_CathedralChant"), TEXT("Cathedral Chant"), TEXT("Nave resonance lines."), { 55, 59, 62, 67 }, { 1.0f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv13_VineRefrain"), TEXT("Vine Refrain"), TEXT("Overgrown ruin motif."), { 60, 64, 68, 72 }, { 0.5f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv14_BridgeGallop"), TEXT("Bridge Gallop"), TEXT("Floating bridge rush."), { 65, 69, 72, 77 }, { 0.25f, 0.25f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv15_ConservatoryBloom"), TEXT("Conservatory Bloom"), TEXT("Greenhouse crescendo."), { 62, 66, 69, 74 }, { 0.5f, 0.5f, 0.75f, 1.25f }, 4 },
		{ TEXT("Skill_Lv16_AuroraGleam"), TEXT("Aurora Gleam"), TEXT("Tier IV light arpeggio."), { 67, 71, 74, 79 }, { 0.5f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv17_CometRondo"), TEXT("Comet Rondo"), TEXT("Chapel rondo figure."), { 59, 63, 66, 71 }, { 0.75f, 0.25f, 0.75f, 1.0f }, 4 },
		{ TEXT("Skill_Lv18_NebulaDrift"), TEXT("Nebula Drift"), TEXT("Maze ambient swell."), { 54, 58, 61, 66 }, { 1.0f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv19_ConstellationGrid"), TEXT("Constellation Grid"), TEXT("Lattice star pattern."), { 60, 64, 67, 72 }, { 0.33f, 0.33f, 0.33f, 1.0f }, 4 },
		{ TEXT("Skill_Lv20_HarmonicDome"), TEXT("Harmonic Dome"), TEXT("Radial dome resonance."), { 63, 67, 70, 75 }, { 0.5f, 0.5f, 0.5f, 1.5f }, 4 },
		{ TEXT("Skill_Lv21_DragonscaleRiff"), TEXT("Dragonscale Riff"), TEXT("Tier V percussive riff."), { 50, 55, 62, 67 }, { 0.25f, 0.25f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv22_PianoCascade"), TEXT("Piano Cascade"), TEXT("Waterfall descending run."), { 72, 69, 65, 60 }, { 0.25f, 0.25f, 0.25f, 1.0f }, 4 },
		{ TEXT("Skill_Lv23_MusicBoxEtude"), TEXT("Music Box Etude"), TEXT("Atelier precision study."), { 60, 62, 64, 67 }, { 0.5f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv24_ImaginaryStairs"), TEXT("Imaginary Stairs"), TEXT("Escher paradox climb."), { 58, 61, 65, 70 }, { 0.5f, 0.5f, 0.75f, 1.25f }, 4 },
		{ TEXT("Skill_Lv25_GalaxyRefrain"), TEXT("Galaxy Refrain"), TEXT("Cloister galaxy chorus."), { 64, 68, 71, 76 }, { 0.5f, 0.5f, 0.5f, 1.0f }, 4 },
		{ TEXT("Skill_Lv26_ObservatoryHymn"), TEXT("Observatory Hymn"), TEXT("Tier VI celestial hymn."), { 55, 59, 62, 67 }, { 1.0f, 0.5f, 0.5f, 1.5f }, 4 },
		{ TEXT("Skill_Lv27_FinalStarGate"), TEXT("Final Star Gate"), TEXT("Penrose gate fanfare."), { 67, 71, 74, 79 }, { 0.5f, 0.5f, 0.5f, 2.0f }, 4 },
		{ TEXT("Skill_Lv28_DreamCathedral"), TEXT("Dream Cathedral"), TEXT("Boss-room cathedral blast."), { 48, 55, 62, 67 }, { 0.5f, 0.5f, 0.5f, 1.5f }, 4 },
		{ TEXT("Skill_Lv29_HallOfHarmonics"), TEXT("Hall of Harmonics"), TEXT("Multi-voice harmonic wall."), { 60, 64, 67, 72 }, { 0.25f, 0.25f, 0.25f, 1.0f }, 4 },
		{ TEXT("Skill_Lv30_MaestroFinale"), TEXT("Maestro Finale"), TEXT("Demo cap -- full highway mastery."), { 62, 66, 69, 74 }, { 0.5f, 0.5f, 0.5f, 2.0f }, 4 },
	};

	for (int32 Level = 1; Level <= 30; ++Level)
	{
		const FSkillRow& Row = Rows[Level - 1];
		TArray<int32> Pitches;
		TArray<float> Durations;
		for (int32 Index = 0; Index < Row.NoteCount; ++Index)
		{
			Pitches.Add(Row.PitchPattern[Index]);
			Durations.Add(Row.DurationPattern[Index]);
		}

		const float PowerScalar = 0.85f + static_cast<float>(Level) * 0.05f;
		Cache.Add(MakeSkill(
			Row.Id,
			Row.Name,
			Row.Desc,
			ElementForLevel(Level),
			InstrumentForLevel(Level),
			Level,
			Pitches,
			Durations,
			PowerScalar));
	}

	// Build lookup map
	TMap<FName, FMelodiaSongSkillRecipe>& Map = GetCachedSkillMap();
	Map.Empty();
	for (FMelodiaSongSkillRecipe& Skill : Cache)
	{
		// Overnight: StarlitPing opener uses authored 2-lane chart (not Index%4)
		if (Skill.SkillId == TEXT("Skill_Lv01_StarlitPing"))
		{
			Skill.ChartNotes.Reset();
			FMelodiaChartNote A; A.TargetBeat = 0.0f; A.LaneIndex = 0; A.Pitch = 60; A.DurationBeats = 1.0f;
			FMelodiaChartNote B; B.TargetBeat = 1.0f; B.LaneIndex = 1; B.Pitch = 64; B.DurationBeats = 1.0f;
			Skill.ChartNotes.Add(A);
			Skill.ChartNotes.Add(B);
		}
		Map.Add(Skill.SkillId, Skill);
	}

	return Cache;
}

bool UMelodiaSongSkillLibrary::FindSongSkill(const FName SkillId, FMelodiaSongSkillRecipe& OutSkill)
{
	if (SkillId.IsNone())
	{
		return false;
	}

	// Check cached map first
	const TMap<FName, FMelodiaSongSkillRecipe>& Map = GetCachedSkillMap();
	if (const FMelodiaSongSkillRecipe* Found = Map.Find(SkillId))
	{
		OutSkill = *Found;
		return true;
	}

	// Build cache and try again
	BuildDemoSongSkills();
	const TMap<FName, FMelodiaSongSkillRecipe>& Map2 = GetCachedSkillMap();
	if (const FMelodiaSongSkillRecipe* Found = Map2.Find(SkillId))
	{
		OutSkill = *Found;
		return true;
	}

	return false;
}

FName UMelodiaSongSkillLibrary::GetSkillIdForMechanicLevel(const int32 MechanicLevel)
{
	const int32 Clamped = FMath::Clamp(MechanicLevel, 1, 30);
	for (const FMelodiaSongSkillRecipe& Skill : BuildDemoSongSkills())
	{
		if (Skill.MechanicLevelRequired == Clamped)
		{
			return Skill.SkillId;
		}
	}
	return NAME_None;
}

TArray<FName> UMelodiaSongSkillLibrary::GetSkillIdsUnlockedAtOrBelowLevel(const int32 MechanicLevel)
{
	TArray<FName> Ids;
	for (const FMelodiaSongSkillRecipe& Skill : BuildDemoSongSkills())
	{
		if (Skill.MechanicLevelRequired <= MechanicLevel)
		{
			Ids.Add(Skill.SkillId);
		}
	}
	return Ids;
}
