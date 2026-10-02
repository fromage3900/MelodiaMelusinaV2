#include "MelodiaWaveArrow.h"
#include "MelodiaWaveHarpCombatComponent.h"
#include "MelodiaHybridEncounterComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"

AMelodiaWaveArrow::AMelodiaWaveArrow()
{
 Collision = CreateDefaultSubobject<USphereComponent>(TEXT("ArrowCollision"));
 SetRootComponent(Collision);
 Collision->InitSphereRadius(8);
 Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
 Collision->SetCollisionObjectType(ECC_WorldDynamic);
 Collision->SetCollisionResponseToAllChannels(ECR_Block);
 Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
 Collision->SetGenerateOverlapEvents(true);
 Collision->OnComponentHit.AddDynamic(this, &ThisClass::HandleHit);
 Collision->OnComponentBeginOverlap.AddDynamic(this, &ThisClass::HandleOverlap);
 Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WaveHarpArrow"));
 Visual->SetupAttachment(Collision);
 Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 // The authored R07 arrow points along +Y; movement and actor forward use +X.
 Visual->SetRelativeRotation(FRotator(0, -90, 0));
 Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ArrowMovement"));
 Movement->SetUpdatedComponent(Collision);
 Movement->InitialSpeed = 4000;
 Movement->MaxSpeed = 4000;
 Movement->ProjectileGravityScale = 0;
 Movement->bRotationFollowsVelocity = true;
 Trail = CreateDefaultSubobject<UNiagaraComponent>(TEXT("ArrowMotionTrail"));
 Trail->SetupAttachment(Collision);
 Trail->SetAutoActivate(false);
 Trail->SetRelativeScale3D(FVector(.18));
 Trail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 InitialLifeSpan = 4;
}

void AMelodiaWaveArrow::Launch(UMelodiaWaveHarpCombatComponent* Source, const FVector& Direction)
{
 Shooter = Source;
 Collision->IgnoreActorWhenMoving(GetOwner(), true);
 Visual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,
  TEXT("/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Arrow_R07.SM_ME_WaveHarp_Arrow_R07")));
 Movement->Velocity = Direction.GetSafeNormal() * Movement->InitialSpeed;
 // Existing world-space ribbon + sparks. Per-arrow parameters leave the shared asset intact.
 if (UNiagaraSystem* System = Source ? Source->ArrowTrailSystem.LoadSynchronous() : nullptr)
 {
  Trail->SetAsset(System);
  const float Intensity = FMath::Clamp(Source->bShotIsCharged ? Source->ChargedTrailIntensity : Source->ArrowTrailIntensity, .1f, .8f);
  Trail->SetVariableFloat(TEXT("User.Intensity"), Intensity);
  Trail->SetVariableFloat(TEXT("User.GlobalReactivity"), Intensity);
  Trail->SetVariableFloat(TEXT("User.DreamVisibility"), 1.f);
  Trail->Activate(true);
 }
 UE_LOG(LogTemp, Log, TEXT("MELODIA_ARROW_SPAWN actor=%s location=%s forward=%s velocity=%s owner=%s instigator=%s"),
  *GetName(), *GetActorLocation().ToString(), *GetActorForwardVector().ToString(),
  *Movement->Velocity.ToString(), *GetNameSafe(GetOwner()), *GetNameSafe(GetInstigator()));
}
void AMelodiaWaveArrow::HandleHit(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, FVector, const FHitResult&)
{ Consume(Other); }
void AMelodiaWaveArrow::HandleOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
 if (Other && Other->FindComponentByClass<UMelodiaHybridEncounterComponent>()) Consume(Other);
}
void AMelodiaWaveArrow::Consume(AActor* Other)
{
 if (bConsumed || !Other || Other == GetOwner() || Other == GetInstigator()) return;
 bConsumed = true; // Before the synchronous stock/HP/outcome callbacks.
 UE_LOG(LogTemp, Log, TEXT("MELODIA_ARROW_COLLISION arrow=%s target=%s"), *GetName(), *GetNameSafe(Other));
 if (Shooter.IsValid()) Shooter->ResolveProjectileHit(Other);
 Destroy();
}
