#include "MelodiaIntegrationConfig.h"

#include "GameFramework/Pawn.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraEffectType.h"

UMelodiaIntegrationConfig::UMelodiaIntegrationConfig()
	: P0PlayerClass(FSoftClassPath(TEXT("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C")))
	, ChoralSheepDefinition(FSoftObjectPath(TEXT("/Game/Melodia/Companions/ChoralSheep/DA_ChoralSheepDefinition.DA_ChoralSheepDefinition")))
	, CharacterEffectType(FSoftObjectPath(TEXT("/Game/Melodia/VFX/EffectTypes/ET_Melodia_CharacterFX.ET_Melodia_CharacterFX")))
	, AmbientEffectType(FSoftObjectPath(TEXT("/Game/EnvSandbox/VFX/EffectTypes/ENV_StorybookAmbientVFX.ENV_StorybookAmbientVFX")))
{
	auto AddPostProcess = [this](const TCHAR* Path, const float Weight)
	{
		FMelodiaPostProcessIdentity& Entry = FrozenPostProcessStack.AddDefaulted_GetRef();
		Entry.Material = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(Path));
		Entry.Weight = Weight;
	};
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_StorybookOutline_Frozen.MI_StorybookOutline_Frozen"), 1.0f);
	// B1 (owner, 2026-09-14, Docs/VFX/CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md):
	// StarryNight lives on sky-dome geometry blended with UDS; the post-process
	// overlay path is REJECTED. This slot stays only until the next editor pass
	// lifts it from the PPV — do not tune it as a blendable.
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_StarryNight_Frozen.MI_StarryNight_Frozen"), 1.0f);
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_MeluColorGrade_Frozen.MI_MeluColorGrade_Frozen"), 1.0f);
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_MelodiaInk_Frozen.MI_MelodiaInk_Frozen"), 0.31f);
}
