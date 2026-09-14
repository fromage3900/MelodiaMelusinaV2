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
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_StarryNight_Frozen.MI_StarryNight_Frozen"), 1.0f);
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_MeluColorGrade_Frozen.MI_MeluColorGrade_Frozen"), 1.0f);
	AddPostProcess(TEXT("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/MI_MelodiaInk_Frozen.MI_MelodiaInk_Frozen"), 0.31f);
}
