#include "MelodiaDressingSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

bool UMelodiaDressingSubsystem::DressHeroClutter(AActor* CameraFocus, const FName& FamilyTag, const int32 Count)
{
	if (!CameraFocus || Count <= 0)
	{
		return false;
	}
	// Scaffold: this validates the contract and logs intent. Live placement
	// loads the dressing catalog (DA_MelodiaDressingCatalog) and spawns tagged
	// hero props from the existing SM_/MI_ library around CameraFocus within a
	// camera-critical radius. Full wiring requires a live editor + Monolith
	// :9316 (single editor) and `unattended:true` batch saves.
	ActiveFamily = FamilyTag;
	UE_LOG(LogTemp, Log, TEXT("[Dressing] DressHeroClutter family=%s count=%d around %s"),
		*FamilyTag.ToString(), Count, *CameraFocus->GetName());
	return true;
}

bool UMelodiaDressingSubsystem::PhysicallyDrop(const TArray<AActor*>& Actors, const FVector DropOffset, const float Restitution)
{
	if (Actors.Num() == 0)
	{
		return false;
	}
	// Scaffold: validates the call. Live: spawns the actors at DropOffset above
	// the focus and enables simulation (gravity) with the given restitution to
	// settle debris (logs/rocks/field gear) — the "physically dropped" Dash case.
	UE_LOG(LogTemp, Log, TEXT("[Dressing] PhysicallyDrop %d actors offset=%s restitution=%.2f"),
		Actors.Num(), *DropOffset.ToString(), Restitution);
	return true;
}

TArray<AActor*> UMelodiaDressingSubsystem::FindCompositionOccluders(AActor* CameraFocus, const float Radius, const int32 MaxReports)
{
	TArray<AActor*> Out;
	if (!CameraFocus || MaxReports <= 0)
	{
		return Out;
	}
	// Scaffold: live implementation raycasts/overlaps from CameraFocus and
	// returns props occluding the framing cone within Radius. It REPORTS only —
	// never deletes foreign assets. Offline this returns empty (contract check).
	UE_LOG(LogTemp, Log, TEXT("[Dressing] FindCompositionOccluders radius=%.1f max=%d (scaffold)"),
		Radius, MaxReports);
	return Out;
}

FSoftObjectPath UMelodiaDressingSubsystem::GetDressingCatalogPath() const
{
	// Reserved destination for the hero-prop dressing catalog (DataAsset keyed
	// by FGameplayTag family). Not invented on disk yet — returned here so the
	// contract is stable. Guardrail: no Content/_PROJECT/ writes.
	return FSoftObjectPath(TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaDressingCatalog"));
}