// Copyright Melodia. Phrase bus transport — OSC subset decoder over UDP.
//
// Decodes exactly what Tools/phrase_bridge/bridge.py emits via osc_min.py:
//   /melodia/phrase/state    ",isifsfi"  [idx, SECTION, bar, energy, TREND, conf, pulse]
//   /melodia/phrase/boundary ",ii"      [phrase_index, bar]
// Anything else is ignored. Big-endian per OSC 1.0; 4-byte padded strings.
// No gameplay: no MPC writes, no Niagara, no sheep motion, no WC compile.

#include "MelodiaPhraseBusSubsystem.h"

#include "IPAddress.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogMelodiaPhraseBus, Log, All);

namespace
{
	// OSC 1.0 integers are big-endian; do the swap explicitly rather than
	// relying on platform ntohl availability inside the module.
	int32 ReadBigEndianInt32(const uint8* Bytes)
	{
		return (static_cast<int32>(Bytes[0]) << 24)
			 | (static_cast<int32>(Bytes[1]) << 16)
			 | (static_cast<int32>(Bytes[2]) << 8)
			 |  static_cast<int32>(Bytes[3]);
	}

	bool ReadPaddedString(const uint8*& Cursor, const uint8* End, FString& Out)
	{
		if (Cursor >= End) { return false; }
		const uint8* NullPos = static_cast<const uint8*>(memchr(Cursor, 0, End - Cursor));
		if (!NullPos) { return false; }
		Out = UTF8_TO_TCHAR(reinterpret_cast<const char*>(Cursor));
		const int32 PaddedLen = ((NullPos - Cursor) + 4) & ~3;
		Cursor += PaddedLen;
		return Cursor <= End;
	}

	EMelodiaPhraseSection ParseSection(const FString& S)
	{
		if (S == TEXT("VOICE"))   return EMelodiaPhraseSection::VOICE;
		if (S == TEXT("BUILD"))   return EMelodiaPhraseSection::BUILD;
		if (S == TEXT("CLIMAX"))  return EMelodiaPhraseSection::CLIMAX;
		if (S == TEXT("RELEASE")) return EMelodiaPhraseSection::RELEASE;
		return EMelodiaPhraseSection::SPARSE;
	}

	EMelodiaEnergyTrend ParseTrend(const FString& S)
	{
		if (S == TEXT("RISING"))  return EMelodiaEnergyTrend::RISING;
		if (S == TEXT("FALLING")) return EMelodiaEnergyTrend::FALLING;
		return EMelodiaEnergyTrend::FLAT;
	}
}

void UMelodiaPhraseBusSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	StartListening(9002);
}

void UMelodiaPhraseBusSubsystem::Deinitialize()
{
	StopListening();
	Super::Deinitialize();
}

void UMelodiaPhraseBusSubsystem::StartListening(int32 Port)
{
	StopListening();
	ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!Sockets)
	{
		UE_LOG(LogMelodiaPhraseBus, Warning, TEXT("No socket subsystem; phrase bus disabled"));
		return;
	}
	Socket = Sockets->CreateSocket(NAME_DGram, TEXT("MelodiaPhraseBus"), false);
	if (!Socket)
	{
		UE_LOG(LogMelodiaPhraseBus, Warning, TEXT("CreateSocket failed; phrase bus disabled"));
		return;
	}
	Socket->SetNonBlocking(true);
	Socket->SetReuseAddr(true);
	bool bIpValid = false;
	TSharedRef<FInternetAddr> BindAddr = Sockets->CreateInternetAddr();
	BindAddr->SetIp(TEXT("127.0.0.1"), bIpValid);
	BindAddr->SetPort(Port);
	if (!bIpValid || !Socket->Bind(*BindAddr))
	{
		UE_LOG(LogMelodiaPhraseBus, Warning, TEXT("Bind 127.0.0.1:%d failed; phrase bus disabled"), Port);
		StopListening();
		return;
	}
	LastPacketTime = FPlatformTime::Seconds();
	bTimeoutFired = false;
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaPhraseBusSubsystem::PollSocket), 0.1f);
	UE_LOG(LogMelodiaPhraseBus, Log, TEXT("Phrase bus listening on 127.0.0.1:%d (transport only)"), Port);
}

void UMelodiaPhraseBusSubsystem::StopListening()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	if (Socket)
	{
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(Socket);
		Socket = nullptr;
	}
}

bool UMelodiaPhraseBusSubsystem::PollSocket(float DeltaSeconds)
{
	(void)DeltaSeconds;
	if (!Socket) { return false; }

	ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!Sockets)
	{
		return false;
	}
	uint8 Buffer[2048];
	int32 BytesRead = 0;
	TSharedRef<FInternetAddr> Source = Sockets->CreateInternetAddr();
	// Unconnected datagram sockets must RecvFrom. Recv() returns false on
	// WSAEWOULDBLOCK *and* on unconnected UDP in this UE socket wrapper, so
	// packets never reached Parse. Drain with RecvFrom.
	while (Socket->RecvFrom(Buffer, sizeof(Buffer), BytesRead, *Source) && BytesRead > 0)
	{
		ParseOscPacket(Buffer, BytesRead);
		LastPacketTime = FPlatformTime::Seconds();
		bTimeoutFired = false;
	}

	if (!bTimeoutFired &&
		(FPlatformTime::Seconds() - LastPacketTime) > TimeoutSeconds)
	{
		bTimeoutFired = true;
		UE_LOG(LogMelodiaPhraseBus, Log, TEXT("Phrase bus timeout after %.1fs — conductor owns settle"), TimeoutSeconds);
		OnPhraseTimeout.Broadcast();
	}
	return true;
}

bool UMelodiaPhraseBusSubsystem::ParseOscPacket(const uint8* Data, int32 Size)
{
	if (!Data || Size <= 0) { return false; }
	const uint8* Cursor = Data;
	const uint8* End = Data + Size;
	FString Address;
	if (!ReadPaddedString(Cursor, End, Address)) { return false; }

	if (Address == TEXT("/melodia/phrase/state"))
	{
		return ParseStateMessage(Cursor, static_cast<int32>(End - Cursor));
	}
	if (Address == TEXT("/melodia/phrase/boundary"))
	{
		FString Tags;
		if (!ReadPaddedString(Cursor, End, Tags) || Tags != TEXT(",ii"))
		{
			return false;
		}
		if (Cursor + 8 > End) { return false; }
		const int32 PhraseIndex = ReadBigEndianInt32(Cursor); Cursor += 4;
		const int32 Bar = ReadBigEndianInt32(Cursor); Cursor += 4;
		OnPhraseBoundary.Broadcast(PhraseIndex, Bar);
		return true;
	}
	return false; // unknown address: not ours
}

bool UMelodiaPhraseBusSubsystem::ParseStateMessage(const uint8* Payload, int32 Size)
{
	const uint8* Cursor = Payload;
	const uint8* End = Payload + Size;
	FString Tags;
	if (!ReadPaddedString(Cursor, End, Tags)) { return false; }
	// Wire tags from bridge.py _send_state: int, str, int, float, str, float, int.
	if (Tags != TEXT(",isifsfi")) { return false; }

	auto ReadInt = [&](int32& Out) {
		if (Cursor + 4 > End) return false;
		Out = ReadBigEndianInt32(Cursor);
		Cursor += 4;
		return true;
	};
	auto ReadFloat = [&](float& Out) {
		if (Cursor + 4 > End) return false;
		const int32 Bits = ReadBigEndianInt32(Cursor);
		FMemory::Memcpy(&Out, &Bits, 4);
		Cursor += 4;
		return true;
	};
	auto ReadStr = [&](FString& Out) { return ReadPaddedString(Cursor, End, Out); };

	FMelodiaPhraseState S;
	FString SectionStr, TrendStr;
	int32 Pulse = 0;
	if (!ReadInt(S.PhraseIndex)) { return false; }
	if (!ReadStr(SectionStr))    { return false; }
	if (!ReadInt(S.Bar))         { return false; }
	if (!ReadFloat(S.Energy))    { return false; }
	if (!ReadStr(TrendStr))      { return false; }
	if (!ReadFloat(S.Confidence)){ return false; }
	if (!ReadInt(Pulse))         { return false; }

	S.Section = ParseSection(SectionStr);
	S.EnergyTrend = ParseTrend(TrendStr);
	S.BeatInBar = 0.0f; // OSC state feed omits beat phase (JSON schema has it;
	                    // conductor / Jev derive phrasing from Bar + BoundaryPulse).
	S.bBoundaryPulse = Pulse != 0;

	CurrentState = S;
	OnPhraseState.Broadcast(CurrentState);
	return true;
}
