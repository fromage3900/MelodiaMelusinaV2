#include "MelodiaRhythmReactivitySubsystem.h"

#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundMix.h"
#include "Sound/SoundClass.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Common/UdpSocketBuilder.h"
#include "IPAddress.h"

// Was /Game/EnvSandbox/Materials/Functions/MPC_Portfolio_Audio, which only exposes
// BeatIntensity/RhythmPulse -- every other Publish() write below was silently dropped
// (SetScalarParameterValue on a nonexistent name is a no-op). MPC_Melodia_Palette already
// carries a matching, well-named param set (17 params incl. GlobalSparkleIntensity/
// PaletteShift/TemporalJitter) that other project materials presumably already sample.
const FName UMelodiaRhythmReactivitySubsystem::AudioCollectionPath(TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"));

// Tension ambience duck: the SoundMix must carry at least one SoundClassAdjuster
// for SCL_Ambience (the override below writes volume at runtime regardless, but
// a mix with no adjusters for the class is ignored by the override path).
const FName UMelodiaRhythmReactivitySubsystem::TensionDuckSoundMixPath(TEXT("/Game/Melodia/Audio/Mix/SM_MelodiaTensionDuck"));
const FName UMelodiaRhythmReactivitySubsystem::AmbienceSoundClassPath(TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Ambience"));

void UMelodiaRhythmReactivitySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	CachedCollection = LoadObject<UMaterialParameterCollection>(nullptr, *AudioCollectionPath.ToString());

	OscSocket = FUdpSocketBuilder(TEXT("MelodiaOSCSender"))
		.AsReusable()
		.Build();

	if (OscSocket)
	{
		ISocketSubsystem* SocketSub = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
		if (SocketSub)
		{
			OscTargetAddr = SocketSub->CreateInternetAddr();
			OscTargetAddr->SetIp(0x7f000001);
			OscTargetAddr->SetPort(9000);
		}
	}
}

void UMelodiaRhythmReactivitySubsystem::Deinitialize()
{
	if (OscSocket)
	{
		OscSocket->Close();
		if (ISocketSubsystem* SocketSub = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM))
		{
			SocketSub->DestroySocket(OscSocket);
		}
		OscSocket = nullptr;
	}
	Super::Deinitialize();
}

void UMelodiaRhythmReactivitySubsystem::SendOSCFloat(const FString& Address, float Value) const
{
	if (!OscSocket || !OscTargetAddr.IsValid()) return;

	TArray<uint8> Packet;

	FTCHARToUTF8 AddrStr(*Address);
	Packet.Append(reinterpret_cast<const uint8*>(AddrStr.Get()), AddrStr.Length());
	while (Packet.Num() % 4 != 0) Packet.Add(0);

	Packet.Add(',');
	Packet.Add('f');
	while (Packet.Num() % 4 != 0) Packet.Add(0);

	uint32 Raw = 0;
	FMemory::Memcpy(&Raw, &Value, sizeof(Raw));
	Raw = BYTESWAP_ORDER32(Raw);
	Packet.Append(reinterpret_cast<const uint8*>(&Raw), sizeof(uint32));

	int32 Sent = 0;
	OscSocket->SendTo(Packet.GetData(), Packet.Num(), Sent, *OscTargetAddr);
}

void UMelodiaRhythmReactivitySubsystem::Tick(const float DeltaTime)
{
	const float BeatDecay = FMath::Max(0.01f, DeltaTime * 6.0f);
	Signal.BeatPulse = FMath::Max(0.0f, Signal.BeatPulse - BeatDecay);
	Signal.CommandPulse = FMath::Max(0.0f, Signal.CommandPulse - DeltaTime * 5.0f);
	Signal.BreakPulse = FMath::Max(0.0f, Signal.BreakPulse - DeltaTime * 3.0f);
	Signal.VictoryPulse = FMath::Max(0.0f, Signal.VictoryPulse - DeltaTime * 2.0f);
	Signal.EnemyTension = FMath::FInterpTo(Signal.EnemyTension, 0.0f, DeltaTime, 1.5f);

	// Tension sustain: fast attack toward the latest graded tension, slow release
	// toward zero -- danger spikes, dread lingers (OMORI's held-tension register).
	// Presentation-only; never feeds damage or results (Decision 033).
	if (Signal.EnemyTension >= Signal.TensionSustain)
	{
		Signal.TensionSustain = FMath::FInterpTo(Signal.TensionSustain, Signal.EnemyTension, DeltaTime, 4.0f);
	}
	else
	{
		Signal.TensionSustain = FMath::FInterpTo(Signal.TensionSustain, 0.0f, DeltaTime, 0.35f);
	}

	// Continuous dissonance register: 0 = Clear, 1 = Strain, 2 = Rupture, derived
	// from how much dread is currently felt. Drives the DissonanceAmount MPC/OSC
	// channel so materials and TouchDesigner can shift toward the Rupture look
	// without a one-shot overlap trigger.
	Signal.DissonanceAmount = FMath::Clamp(Signal.TensionSustain * 2.0f, 0.0f, 2.0f);

	// Tension ambience duck: the ambience bed pulls back as dread lingers.
	// Runs every tick (cheap pointer checks + IsNearlyEqual) and BEFORE the
	// at-rest skip so the fade back to full ambience completes even after
	// TensionSustain decays below the at-rest epsilon.
	UpdateTensionAmbienceDuck();

	// Cozy: slow-decaying ambient values. WarmthGlow fades gently, others drift toward zero.
	Signal.WarmthGlow = FMath::FInterpTo(Signal.WarmthGlow, 0.0f, DeltaTime, 0.8f);
	Signal.PetalFallIntensity = FMath::FInterpTo(Signal.PetalFallIntensity, 0.0f, DeltaTime, 1.2f);
	Signal.DreamRipple = FMath::FInterpTo(Signal.DreamRipple, 0.0f, DeltaTime, 0.6f);
	Signal.EmberDance = FMath::FInterpTo(Signal.EmberDance, 0.0f, DeltaTime, 1.0f);
	Signal.CozyBloom = FMath::FInterpTo(Signal.CozyBloom, 0.0f, DeltaTime, 1.5f);

	// Idle exploration (no rhythm activity) previously still ran the full
	// Publish() - 14 MPC writes + 6 OSC sends + a delegate broadcast - every
	// single frame forever. Notify*() calls below still Publish() immediately
	// on their own, so skipping here only removes redundant at-rest spam.
	if (!IsSignalAtRest())
	{
		Publish();
		HeartbeatAccumulator = 0.0f;
		return;
	}

	// Heartbeat. At rest the block above sends nothing at all, which leaves the
	// TouchDesigner end unable to distinguish "Unreal is idle" from "Unreal is not
	// running" -- an oscinCHOP simply holds its last values forever either way.
	// A slow publish keeps the stream provably alive without reintroducing the
	// per-frame at-rest spam that the skip above exists to prevent.
	//
	// Note IsSignalAtRest() ignores ComboNormalized / CrescendoNormalized /
	// CommandEnergy, so those are sticky between encounters; the heartbeat is also
	// what eventually republishes them after the pulses decay to zero.
	HeartbeatAccumulator += DeltaTime;
	if (HeartbeatAccumulator >= HeartbeatInterval)
	{
		HeartbeatAccumulator = 0.0f;
		Publish();
	}
}

bool UMelodiaRhythmReactivitySubsystem::IsSignalAtRest() const
{
	constexpr float Epsilon = 0.0005f;
	return Signal.BeatPulse < Epsilon
		&& Signal.CommandPulse < Epsilon
		&& Signal.BreakPulse < Epsilon
		&& Signal.VictoryPulse < Epsilon
		&& Signal.EnemyTension < Epsilon
		&& Signal.TensionSustain < Epsilon
		&& Signal.DissonanceAmount < Epsilon
		&& Signal.WarmthGlow < Epsilon
		&& Signal.PetalFallIntensity < Epsilon
		&& Signal.DreamRipple < Epsilon
		&& Signal.EmberDance < Epsilon
		&& Signal.CozyBloom < Epsilon;
}

void UMelodiaRhythmReactivitySubsystem::UpdateTensionAmbienceDuck()
{
	// Presentation-only ambience duck (Decision 033): as DreadPresence rises the
	// ambience bed pulls back -- a quiet-register shift, never a mechanic. The
	// dark-bed crossfade itself (Riverbed_Open toward Canopy_Small) is a content
	// task on the ambience player; this only ducks the SCL_Ambience class volume.
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	if (!CachedTensionDuckMix)
	{
		CachedTensionDuckMix = LoadObject<USoundMix>(nullptr, *TensionDuckSoundMixPath.ToString());
		if (!CachedTensionDuckMix)
		{
			// Content does not exist yet -- silent no-op (same policy as the MPC
			// param writes: SetScalarParameterValue on a missing param is a no-op).
			return;
		}
	}
	if (!CachedAmbienceSoundClass)
	{
		CachedAmbienceSoundClass = LoadObject<USoundClass>(nullptr, *AmbienceSoundClassPath.ToString());
		if (!CachedAmbienceSoundClass)
		{
			return;
		}
	}

	// Full ambience at rest, -6 dB (~0.5x) at max dread. The 1.5s fade keeps the
	// shift from snapping; the override re-fades toward the new target on each
	// change and ClearSoundMixClassOverride is never needed (target 1.0 restores
	// full ambience through the same override).
	const float TargetVolume = 1.0f - Signal.TensionSustain * 0.5f;

	if (!FMath::IsNearlyEqual(TargetVolume, LastAmbienceDuckVolume, 0.01f))
	{
		LastAmbienceDuckVolume = TargetVolume;
		UGameplayStatics::SetSoundMixClassOverride(World, CachedTensionDuckMix, CachedAmbienceSoundClass, TargetVolume, 1.0f, 1.5f, true);
	}
}

TStatId UMelodiaRhythmReactivitySubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UMelodiaRhythmReactivitySubsystem, STATGROUP_Tickables);
}

void UMelodiaRhythmReactivitySubsystem::NotifyBeat(const float InBPM, const float InBeatPhase)
{
	Signal.BPM = FMath::Clamp(InBPM, 20.0f, 400.0f);
	Signal.BeatPhase = FMath::Clamp(InBeatPhase, 0.0f, 1.0f);
	Signal.BeatPulse = 1.0f;

	// Cozy: gentle warmth pulse on each beat, dream ripple follows the beat.
	Signal.WarmthGlow = FMath::Min(1.0f, Signal.WarmthGlow + 0.3f);
	Signal.DreamRipple = FMath::Min(1.0f, Signal.DreamRipple + 0.2f);

	Publish();
}

void UMelodiaRhythmReactivitySubsystem::NotifyCommandResolved(const EMelodiaRhythmGrade Grade, const float InCommandEnergy, const float InComboNormalized, const float InCrescendoNormalized, const uint8 InRhythmElement)
{
	Signal.LastRhythmGrade = Grade;
	Signal.CommandEnergy = FMath::Clamp(InCommandEnergy, 0.0f, 2.0f);
	Signal.ComboNormalized = FMath::Clamp(InComboNormalized, 0.0f, 1.0f);
	Signal.CrescendoNormalized = FMath::Clamp(InCrescendoNormalized, 0.0f, 1.0f);
	Signal.RhythmElement = InRhythmElement;
	Signal.CommandPulse = 1.0f;

	// Cozy: petal fall and ember dance respond to combo and crescendo.
	Signal.PetalFallIntensity = FMath::Min(1.0f, Signal.PetalFallIntensity + Signal.ComboNormalized * 0.5f);
	Signal.EmberDance = FMath::Min(1.0f, Signal.EmberDance + Signal.CrescendoNormalized * 0.4f);

	Publish();
}

void UMelodiaRhythmReactivitySubsystem::NotifyBreak() { Signal.BreakPulse = 1.0f; Publish(); }

void UMelodiaRhythmReactivitySubsystem::NotifyVictory()
{
	Signal.VictoryPulse = 1.0f;

	// Cozy: warm bloom flares on victory, embers dance.
	Signal.CozyBloom = 1.0f;
	Signal.EmberDance = FMath::Min(1.0f, Signal.EmberDance + 0.6f);

	Publish();
}

void UMelodiaRhythmReactivitySubsystem::NotifyEnemyIntent(const float Tension)
{
	Signal.EnemyTension = FMath::Clamp(Tension, 0.0f, 1.0f);

	// Cozy: dream ripple responds to tension for subtle atmospheric shift.
	Signal.DreamRipple = FMath::Min(1.0f, Signal.DreamRipple + Tension * 0.3f);

	Publish();
}

void UMelodiaRhythmReactivitySubsystem::ResetEncounter()
{
	Signal.ComboNormalized = 0.0f;
	Signal.CrescendoNormalized = 0.0f;
	Signal.CommandEnergy = 0.0f;
	Signal.CommandPulse = 0.0f;
	Signal.BreakPulse = 0.0f;
	Signal.VictoryPulse = 0.0f;
	Signal.EnemyTension = 0.0f;
	Signal.TensionSustain = 0.0f;
	Signal.DissonanceAmount = 0.0f;

	// Cozy: gentle values linger — WarmthGlow and DreamRipple fade slowly rather than snap.
	Signal.PetalFallIntensity = 0.0f;
	Signal.EmberDance = 0.0f;
	Signal.CozyBloom = 0.0f;
	Publish();
}

UMelodiaRhythmReactivitySubsystem* UMelodiaRhythmReactivitySubsystem::Get(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr)
	{
		return World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>();
	}
	return nullptr;
}

void UMelodiaRhythmReactivitySubsystem::RegisterReactiveMeshComponent(UPrimitiveComponent* MeshComponent)
{
	if (!MeshComponent)
	{
		return;
	}
	const int32 NumSlots = MeshComponent->GetNumMaterials();
	for (int32 SlotIndex = 0; SlotIndex < NumSlots; ++SlotIndex)
	{
		if (UMaterialInstanceDynamic* MID = MeshComponent->CreateAndSetMaterialInstanceDynamic(SlotIndex))
		{
			ReactiveDynamicMaterials.Add(MID);
		}
	}
}

void UMelodiaRhythmReactivitySubsystem::SetReactiveStencil(UPrimitiveComponent* MeshComponent, const int32 StencilValue)
{
	if (!MeshComponent)
	{
		return;
	}

	const int32 SafeStencilValue = FMath::Clamp(StencilValue, 0, 255);
	MeshComponent->SetRenderCustomDepth(SafeStencilValue > 0);
	MeshComponent->SetCustomDepthStencilValue(SafeStencilValue);
}

void UMelodiaRhythmReactivitySubsystem::PublishToReactiveMaterials() const
{
	// M_Master_Toon_Universal's own exposed knobs -- "dream rim"/temporal stylization/parallax/
	// iridescence per the user's brief. Params that don't exist on a given instance's parent chain
	// are a safe no-op (UMaterialInstanceDynamic::SetScalarParameterValue), so this is safe to call
	// unconditionally across whatever slots got registered, even non-toon ones.
	for (const TObjectPtr<UMaterialInstanceDynamic>& MID : ReactiveDynamicMaterials)
	{
		if (!MID)
		{
			continue;
		}
		MID->SetScalarParameterValue(TEXT("DreamPulseAmp"), Signal.BeatPulse);
		MID->SetScalarParameterValue(TEXT("Iridescence"), Signal.BeatPulse);
		MID->SetScalarParameterValue(TEXT("TemporalStrength"), Signal.CommandEnergy);
		MID->SetScalarParameterValue(TEXT("ParallaxStrength"), Signal.BeatPulse);
	}
}

void UMelodiaRhythmReactivitySubsystem::Publish()
{
	// Remapped onto MPC_Melodia_Palette's real param set (see AudioCollectionPath comment).
	// The beat namespace (BeatPulse/BeatPhase/BeatIntensity) is owned by the game
	// module's MelodiaAudioReactivePresentationSubsystem, which publishes the
	// continuous clock-driven cos^2 pulse every frame. This subsystem keeps its own
	// internal Signal beat values for the OSC + reactive-material pulses below but
	// must not also write the MPC beat params -- two writers on one surface is a
	// documented defect class in this project. RhythmPulse (CommandEnergy) stays here.
	SetMPCScalar(TEXT("RhythmPulse"), Signal.CommandEnergy);
	SetMPCScalar(TEXT("GlobalSparkleIntensity"), FMath::Max(Signal.VictoryPulse, Signal.CommandPulse));
	SetMPCScalar(TEXT("PaletteShift"), Signal.ComboNormalized);
	SetMPCScalar(TEXT("GlobalEmissiveBoost"), 1.0f + Signal.CrescendoNormalized);
	SetMPCScalar(TEXT("ProximityGlow"), Signal.BreakPulse);
	SetMPCScalar(TEXT("TemporalJitter"), Signal.EnemyTension);

	// Tension/dread channels: the cold counterpart to the cozy set. DreadPresence
	// cools the palette as dread lingers; DissonanceAmount drives the continuous
	// Clear->Strain->Rupture register. SetScalarParameterValue on a param that
	// does not yet exist in MPC_Melodia_Palette is a safe no-op, so this is
	// content-ready before the editor session that adds the params.
	SetMPCScalar(TEXT("DreadPresence"), Signal.TensionSustain);
	SetMPCScalar(TEXT("DissonanceAmount"), Signal.DissonanceAmount);

	// Cozy MPC expansion: gentle world-reactivity values.
	SetMPCScalar(TEXT("WarmthGlow"), Signal.WarmthGlow);
	SetMPCScalar(TEXT("PetalFallIntensity"), Signal.PetalFallIntensity);
	SetMPCScalar(TEXT("DreamRipple"), Signal.DreamRipple);
	SetMPCScalar(TEXT("EmberDance"), Signal.EmberDance);
	SetMPCScalar(TEXT("CozyBloom"), Signal.CozyBloom);

	PublishToReactiveMaterials();

	// OSC: existing beat routes.
	SendOSCFloat(TEXT("/rhythm/beat_pulse"), Signal.BeatPulse);
	SendOSCFloat(TEXT("/rhythm/beat_phase"), Signal.BeatPhase);

	// OSC: cozy expansion for TouchDesigner ambient reactivity.
	SendOSCFloat(TEXT("/rhythm/combo_normalized"), Signal.ComboNormalized);
	SendOSCFloat(TEXT("/rhythm/crescendo_normalized"), Signal.CrescendoNormalized);
	SendOSCFloat(TEXT("/rhythm/command_energy"), Signal.CommandEnergy);
	SendOSCFloat(TEXT("/rhythm/victory_pulse"), Signal.VictoryPulse);
	SendOSCFloat(TEXT("/rhythm/tension"), Signal.EnemyTension);
	SendOSCFloat(TEXT("/rhythm/dread_presence"), Signal.TensionSustain);
	SendOSCFloat(TEXT("/rhythm/dissonance"), Signal.DissonanceAmount);

	OnSignalChanged.Broadcast(Signal);
}

void UMelodiaRhythmReactivitySubsystem::SetMPCScalar(const FName Parameter, const float Value) const
{
	if (!GetWorld() || !CachedCollection) return;
	if (UMaterialParameterCollectionInstance* Instance = GetWorld()->GetParameterCollectionInstance(CachedCollection))
	{
		Instance->SetScalarParameterValue(Parameter, FMath::Clamp(Value, 0.0f, 2.0f));
	}
}
