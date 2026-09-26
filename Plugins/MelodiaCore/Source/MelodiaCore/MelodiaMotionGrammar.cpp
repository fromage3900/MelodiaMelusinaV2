#include "MelodiaMotionGrammar.h"

namespace
{
	float Smooth(float X)
	{
		X = FMath::Clamp(X, 0.0f, 1.0f);
		return X * X * (3.0f - 2.0f * X);
	}
}

void UMelodiaMotionGrammarLibrary::GetStageBeats(const EMelodiaMotionStage Stage, float& OutStartBeat, float& OutEndBeat)
{
	switch (Stage)
	{
	case EMelodiaMotionStage::Glint:  OutStartBeat = 0.0f;   OutEndBeat = 0.25f;  break;
	case EMelodiaMotionStage::Unseal: OutStartBeat = 0.25f;  OutEndBeat = 0.75f;  break;
	case EMelodiaMotionStage::Bloom:  OutStartBeat = 0.75f;  OutEndBeat = 1.25f;  break;
	case EMelodiaMotionStage::Orbit:  OutStartBeat = 1.25f;  OutEndBeat = 1.875f; break;
	default:                          OutStartBeat = 1.875f; OutEndBeat = 5.875f; break; // one bar per breath
	}
}

float UMelodiaMotionGrammarLibrary::GetStageProgress(const EMelodiaMotionStage Stage, const float ElapsedSeconds, const float BPM)
{
	const float Beats = ElapsedSeconds * FMath::Max(BPM, 1.0f) / 60.0f;
	float Start = 0.0f, End = 1.0f;
	GetStageBeats(Stage, Start, End);
	if (Stage == EMelodiaMotionStage::Breathe)
	{
		return Beats < Start ? 0.0f : 0.5f - 0.5f * FMath::Cos(2.0f * PI * (Beats - Start) / (End - Start));
	}
	const float T = FMath::Clamp((Beats - Start) / (End - Start), 0.0f, 1.0f);
	if (Stage == EMelodiaMotionStage::Bloom)
	{
		// Restrained overshoot: rises past 1 in the first 70 %, settles back by the end.
		return Smooth(T / 0.7f) + 0.08f * FMath::Sin(PI * FMath::Clamp((T - 0.45f) / 0.55f, 0.0f, 1.0f));
	}
	return Smooth(T);
}

float UMelodiaMotionGrammarLibrary::GetSettleSeconds(const float BPM)
{
	return 1.875f * 60.0f / FMath::Max(BPM, 1.0f);
}
