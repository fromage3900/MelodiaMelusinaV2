#include "MelodiaRhythmReactivitySubsystem.h"

#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
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
		&& Signal.WarmthGlow < Epsilon
		&& Signal.PetalFallIntensity < Epsilon
		&& Signal.DreamRipple < Epsilon
		&& Signal.EmberDance < Epsilon
		&& Signal.CozyBloom < Epsilon;
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
	// BeatPulse/BeatPhase match by name directly. The rest are a deliberate creative mapping,
	// not 1:1 renames -- combo shifts the palette, victory blooms sparkle, tension jitters time.
	SetMPCScalar(TEXT("BeatPulse"), Signal.BeatPulse);
	SetMPCScalar(TEXT("BeatPhase"), Signal.BeatPhase);
	SetMPCScalar(TEXT("BeatIntensity"), Signal.BeatPulse);
	SetMPCScalar(TEXT("RhythmPulse"), Signal.CommandEnergy);
	SetMPCScalar(TEXT("GlobalSparkleIntensity"), FMath::Max(Signal.VictoryPulse, Signal.CommandPulse));
	SetMPCScalar(TEXT("PaletteShift"), Signal.ComboNormalized);
	SetMPCScalar(TEXT("GlobalEmissiveBoost"), 1.0f + Signal.CrescendoNormalized);
	SetMPCScalar(TEXT("ProximityGlow"), Signal.BreakPulse);
	SetMPCScalar(TEXT("TemporalJitter"), Signal.EnemyTension);

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
