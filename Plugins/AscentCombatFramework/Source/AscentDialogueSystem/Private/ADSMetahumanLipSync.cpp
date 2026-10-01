// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "ADSMetahumanLipSync.h"
#include "Engine/Engine.h"
#include <TimerManager.h>

DEFINE_LOG_CATEGORY(ADSMetahumanLipSyncLog);

// Essential viseme names for mouth animations
const TArray<FString> UADSMetahumanLipSync::VisemeNames = { "sil", "PP", "FF", "TH", "DD", "kk", "CH", "SS", "nn", "RR", "aa", "E", "ih", "oh", "ou" };

// Initialize static variable for audio analysis smoothing
float UADSMetahumanLipSync::LastFrameIntensity = 0.0f;

UADSMetahumanLipSync::UADSMetahumanLipSync()
{
    PrimaryComponentTick.bCanEverTick = false;
    

    CurrentActiveVisemeName = "sil";
    CurrentActiveVisemeIntensity = 0.0f;
    
    // Initialize timing variables
    StartTime = 0.0;
    CurrentSequenceTimePassed = 0.0f;
    bIsPlaying = false;
    
}

void UADSMetahumanLipSync::BeginPlay()
{
    Super::BeginPlay();
        // Initialize current viseme values for Animation Blueprint access
    CurrentVisemeValues.SetNum(15);
    for (int32 i = 0; i < 15; ++i)
    {
        CurrentVisemeValues[i] = 0.0f;
    }
}

void UADSMetahumanLipSync::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // Clear any active timers
    if (VisemePlaybackTimer.IsValid())
    {
        GetWorld()->GetTimerManager().ClearTimer(VisemePlaybackTimer);
    }
    
    Super::EndPlay(EndPlayReason);
}

TArray<FString> UADSMetahumanLipSync::GetAvailableVisemes() const
{
    return VisemeNames;
}

// === MAIN WORKFLOW IMPLEMENTATION ===

bool UADSMetahumanLipSync::GenerateAndBroadcastVisemesFromAudio(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels, float FrameDuration)
{
    if (AudioData.Num() == 0)
    {
        UE_LOG(ADSMetahumanLipSyncLog, Warning, TEXT("Audio data is empty"));
        return false;
    }
    
    // Generate visemes from audio
    TArray<FVisemeFrame> GeneratedVisemes = GenerateVisemesFromAudio(AudioData, SampleRate, NumChannels, FrameDuration);
    
    if (GeneratedVisemes.Num() == 0)
    {
        UE_LOG(ADSMetahumanLipSyncLog, Warning, TEXT("No visemes generated"));
        return false;
    }
    
    // Calculate audio duration for timing synchronization
    float AudioDuration = CalculateAudioDuration(AudioData, SampleRate, NumChannels);
    
    // Convert to Animation Sequence format for timing precision
    FADSAnimationSequence VisemeAnimSequence;
    VisemeAnimSequence.FrameRate = 1.0f / FrameDuration; // Frames per second
    VisemeAnimSequence.Duration = AudioDuration;
    
    // Convert FVisemeFrame to FADSAnimationFrame
    for (const FVisemeFrame& Frame : GeneratedVisemes)
    {
        FADSAnimationFrame AnimFrame;
        
        // Find viseme index and set weight
        for (int32 i = 0; i < VisemeNames.Num(); ++i)
        {
            FName VisemeName(*VisemeNames[i]);
            if (VisemeNames[i] == Frame.VisemeName)
            {
                AnimFrame.BlendShapes.Add(VisemeName, Frame.Intensity);
            }
            else
            {
                AnimFrame.BlendShapes.Add(VisemeName, 0.0f);
            }
        }
        
        VisemeAnimSequence.AnimationFrames.Add(AnimFrame);
    }
    
    // Store the sequence with precise timing
    {
        FScopeLock Lock(&SequenceCriticalSection);
        MainSequenceBuffer = VisemeAnimSequence;
        bIsPlaying = true;
        CalculateStartingTime();
    }
    
    // Start tick-based playback for precise timing
    GetWorld()->GetTimerManager().SetTimer(VisemePlaybackTimer, this, &UADSMetahumanLipSync::TickVisemePlayback, 0.016f, true); // ~60 FPS
    
    UE_LOG(ADSMetahumanLipSyncLog, Log, TEXT("Generated %d viseme frames for Animation Blueprint (Duration: %.3fs)"), 
        GeneratedVisemes.Num(), AudioDuration);
    return true;
}

void UADSMetahumanLipSync::StopVisemeBroadcast()
{
    // Clear the timer
    if (VisemePlaybackTimer.IsValid())
    {
        GetWorld()->GetTimerManager().ClearTimer(VisemePlaybackTimer);
    }
    
    // Clear sequence data
    {
        FScopeLock Lock(&SequenceCriticalSection);
        MainSequenceBuffer.AnimationFrames.Empty();
        MainSequenceBuffer.Duration = 0.0f;
        bIsPlaying = false;
        CurrentSequenceTimePassed = 0.0f;
    }
    
    // Send silent frame to Animation Blueprint
    SendSilentFrame();
}

// === ANIMATION BLUEPRINT INTERFACE ===

TArray<float> UADSMetahumanLipSync::GetCurrentVisemeValues() const
{
    return CurrentVisemeValues;
}

void UADSMetahumanLipSync::GetCurrentActiveViseme(FString& OutVisemeName, float& OutIntensity) const
{
    OutVisemeName = CurrentActiveVisemeName;
    OutIntensity = CurrentActiveVisemeIntensity;
}

// === TIMING AND SYNCHRONIZATION ===

void UADSMetahumanLipSync::CalculateStartingTime()
{
    // Record the current time for precise timing synchronization
    StartTime = FPlatformTime::Seconds();
    CurrentSequenceTimePassed = 0.0f;
}

void UADSMetahumanLipSync::ForceRecalculateStartTime()
{
    if (bIsPlaying)
    {
        CalculateStartingTime();
    }
}

void UADSMetahumanLipSync::TickVisemePlayback()
{
    FScopeLock Lock(&SequenceCriticalSection);
    
    if (!bIsPlaying || MainSequenceBuffer.AnimationFrames.Num() == 0)
    {
        return;
    }
    
    // Calculate elapsed time since start
    double CurrentTime = FPlatformTime::Seconds();
    CurrentSequenceTimePassed = CurrentTime - StartTime;
    
    // Check if sequence has completed
    if (CurrentSequenceTimePassed >= MainSequenceBuffer.Duration)
    {
        // Sequence completed
        bIsPlaying = false;
        SendSilentFrame();
        GetWorld()->GetTimerManager().ClearTimer(VisemePlaybackTimer);
        return;
    }
    
    // Calculate current frame based on time and frame rate
    float FrameTime = CurrentSequenceTimePassed * MainSequenceBuffer.FrameRate;
    int32 CurrentFrameIndex = FMath::FloorToInt(FrameTime);
    int32 NextFrameIndex = CurrentFrameIndex + 1;
    
    // Ensure we don't go out of bounds
    CurrentFrameIndex = FMath::Clamp(CurrentFrameIndex, 0, MainSequenceBuffer.AnimationFrames.Num() - 1);
    NextFrameIndex = FMath::Clamp(NextFrameIndex, 0, MainSequenceBuffer.AnimationFrames.Num() - 1);
    
    // Calculate interpolation alpha for smooth animation
    float Alpha = FrameTime - CurrentFrameIndex;
    Alpha = FMath::Clamp(Alpha, 0.0f, 1.0f);
    
    // Get frames for interpolation
    const FADSAnimationFrame& StartFrame = MainSequenceBuffer.AnimationFrames[CurrentFrameIndex];
    const FADSAnimationFrame& EndFrame = MainSequenceBuffer.AnimationFrames[NextFrameIndex];
    
    // Interpolate between frames
    TMap<FName, float> InterpolatedFrame = InterpolateFrames(StartFrame.BlendShapes, EndFrame.BlendShapes, Alpha);
    
    // Convert to our format and broadcast
    ApplyInterpolatedFrame(InterpolatedFrame);
}

TMap<FName, float> UADSMetahumanLipSync::InterpolateFrames(const TMap<FName, float>& StartFrame, const TMap<FName, float>& EndFrame, float Alpha)
{
    TMap<FName, float> Result;
    
    // Interpolate all viseme values
    for (int32 i = 0; i < VisemeNames.Num(); ++i)
    {
        FName VisemeName(*VisemeNames[i]);
        
        float StartValue = StartFrame.Contains(VisemeName) ? StartFrame[VisemeName] : 0.0f;
        float EndValue = EndFrame.Contains(VisemeName) ? EndFrame[VisemeName] : 0.0f;
        float InterpolatedValue = FMath::Lerp(StartValue, EndValue, Alpha);
        
        Result.Add(VisemeName, InterpolatedValue);
    }
    
    return Result;
}

void UADSMetahumanLipSync::ApplyInterpolatedFrame(const TMap<FName, float>& FrameData)
{
    // Convert interpolated frame to array format
    TArray<float> VisemeArrayValues;
    VisemeArrayValues.SetNum(15);
    
    float MaxIntensity = 0.0f;
    FString DominantViseme = "sil";
    
    // Fill array and find dominant viseme
    for (int32 i = 0; i < VisemeNames.Num(); ++i)
    {
        FName VisemeName(*VisemeNames[i]);
        float Value = FrameData.Contains(VisemeName) ? FrameData[VisemeName] : 0.0f;
        
        VisemeArrayValues[i] = FMath::Clamp(Value, 0.0f, 1.0f);
        
        if (Value > MaxIntensity)
        {
            MaxIntensity = Value;
            DominantViseme = VisemeNames[i];
        }
    }
    
    // Update current values
    CurrentVisemeValues = VisemeArrayValues;
    CurrentActiveVisemeName = DominantViseme;
    CurrentActiveVisemeIntensity = MaxIntensity;
    
    // Broadcast to Animation Blueprint
    OnVisemeValuesChanged.Broadcast(CurrentVisemeValues, CurrentActiveVisemeName, CurrentActiveVisemeIntensity);
}

// === PRIVATE IMPLEMENTATION ===

void UADSMetahumanLipSync::SendSilentFrame()
{
    // Create silent frame
    TArray<float> SilentFrame;
    SilentFrame.SetNum(15);
    for (int32 i = 0; i < 15; ++i)
    {
        SilentFrame[i] = 0.0f;
    }
    
    CurrentVisemeValues = SilentFrame;
    CurrentActiveVisemeName = "sil";
    CurrentActiveVisemeIntensity = 0.0f;
    
    OnVisemeValuesChanged.Broadcast(CurrentVisemeValues, CurrentActiveVisemeName, CurrentActiveVisemeIntensity);
}

float UADSMetahumanLipSync::CalculateAudioDuration(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels)
{
    int32 PCMDataOffset = 0;
    int32 ParsedSampleRate = SampleRate;
    int32 ParsedNumChannels = NumChannels;
    
    // Parse WAV header if present
    if (AudioData.Num() > 44 && 
        AudioData[0] == 'R' && AudioData[1] == 'I' && 
        AudioData[2] == 'F' && AudioData[3] == 'F')
    {
        PCMDataOffset = ParseWAVHeader(AudioData, ParsedSampleRate, ParsedNumChannels);
        SampleRate = ParsedSampleRate;
        NumChannels = ParsedNumChannels;
    }
    
    // Get PCM data size
    int32 PCMSize = AudioData.Num() - PCMDataOffset;
    if (PCMSize <= 0) return 0.0f;
    
    // Calculate duration: PCMSize / (SampleRate * NumChannels * BytesPerSample)
    float Duration = (float)PCMSize / ((float)SampleRate * (float)NumChannels * 2.0f); // 2 bytes per sample (16-bit)
    
    return Duration;
}

TArray<FVisemeFrame> UADSMetahumanLipSync::GenerateVisemesFromAudio(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels, float FrameDuration)
{
    TArray<FVisemeFrame> VisemeSequence;
    
    if (AudioData.Num() == 0)
    {
        VisemeSequence.Add(FVisemeFrame("sil", 0.0f, FrameDuration));
        return VisemeSequence;
    }
    
    // Parse WAV header if present
    int32 PCMDataOffset = 0;
    int32 ParsedSampleRate = SampleRate;
    int32 ParsedNumChannels = NumChannels;
    
    if (AudioData.Num() > 44 && 
        AudioData[0] == 'R' && AudioData[1] == 'I' && 
        AudioData[2] == 'F' && AudioData[3] == 'F')
    {
        PCMDataOffset = ParseWAVHeader(AudioData, ParsedSampleRate, ParsedNumChannels);
        SampleRate = ParsedSampleRate;
        NumChannels = ParsedNumChannels;
    }
    
    // Get PCM data
    const uint8* PCMData = AudioData.GetData() + PCMDataOffset;
    int32 PCMSize = AudioData.Num() - PCMDataOffset;
    
    if (PCMSize <= 0)
    {
        VisemeSequence.Add(FVisemeFrame("sil", 0.0f, FrameDuration));
        return VisemeSequence;
    }
    
    // Convert to 16-bit samples
    const int16* Samples = reinterpret_cast<const int16*>(PCMData);
    int32 NumSamples = PCMSize / sizeof(int16);
    
    // Calculate audio duration
    float AudioDuration = (float)NumSamples / (float)(SampleRate * NumChannels);
    
    // Optimized frame duration for better lip-sync (60fps timing)
    float OptimizedFrameDuration = FMath::Clamp(FrameDuration, 0.016f, 0.05f);
    int32 NumFrames = FMath::CeilToInt(AudioDuration / OptimizedFrameDuration);
    
    // Adaptive frame size calculation
    int32 SamplesPerFrame = FMath::RoundToInt(SampleRate * NumChannels * OptimizedFrameDuration);
    
    // Reset smoothing state for new analysis
    LastFrameIntensity = 0.0f;
    
    // Frame-by-frame analysis
    for (int32 FrameIndex = 0; FrameIndex < NumFrames; ++FrameIndex)
    {
        int32 StartSample = FrameIndex * SamplesPerFrame;
        int32 EndSample = FMath::Min(StartSample + SamplesPerFrame, NumSamples);
        
        if (StartSample >= NumSamples)
        {
            float RemainingTime = AudioDuration - (FrameIndex * OptimizedFrameDuration);
            VisemeSequence.Add(FVisemeFrame("sil", 0.0f, FMath::Max(RemainingTime, OptimizedFrameDuration)));
            break;
        }
        
        FString VisemeName = "sil";
        float Intensity = 0.0f;
        
        AnalyzeAudioFrame(Samples, StartSample, EndSample, NumChannels, SampleRate, VisemeName, Intensity);
        
        // Use consistent frame duration for timing precision
        VisemeSequence.Add(FVisemeFrame(VisemeName, Intensity, OptimizedFrameDuration));
    }
    
    return VisemeSequence;
}

void UADSMetahumanLipSync::AnalyzeAudioFrame(const int16* Samples, int32 StartSample, int32 EndSample, int32 NumChannels, int32 SampleRate, FString& OutVisemeName, float& OutIntensity)
{
    int32 NumFrameSamples = EndSample - StartSample;
    
    if (NumFrameSamples <= 0)
    {
        OutVisemeName = "sil";
        OutIntensity = 0.0f;
        return;
    }
    
    // Calculate RMS energy with better normalization
    float TotalEnergy = 0.0f;
    float MaxAmplitude = 0.0f;
    for (int32 i = StartSample; i < EndSample; i += NumChannels)
    {
        float Sample = (float)Samples[i] / 32767.0f; // Normalize to -1..1
        float AbsSample = FMath::Abs(Sample);
        TotalEnergy += Sample * Sample;
        MaxAmplitude = FMath::Max(MaxAmplitude, AbsSample);
    }
    TotalEnergy = FMath::Sqrt(TotalEnergy / (NumFrameSamples / NumChannels));
    
    // Enhanced high-frequency energy calculation for spectral analysis
    float HighFreqEnergy = 0.0f;
    float MidFreqEnergy = 0.0f;
    float LowFreqEnergy = 0.0f;
    
    // Simple frequency analysis using time-domain differences
    for (int32 i = StartSample; i < EndSample - NumChannels; i += NumChannels)
    {
        float Sample1 = (float)Samples[i] / 32767.0f;
        float Sample2 = (float)Samples[i + NumChannels] / 32767.0f;
        float Diff = FMath::Abs(Sample2 - Sample1);
        
        // Frequency band separation
        if (i % 3 == 0) // High frequency approximation
        {
            HighFreqEnergy += Diff * Diff;
        }
        else if (i % 2 == 0) // Mid frequency
        {
            MidFreqEnergy += Diff * Diff;
        }
        else // Low frequency
        {
            LowFreqEnergy += Diff * Diff;
        }
    }
    
    int32 NumDiffs = FMath::Max(1, (NumFrameSamples / NumChannels) - 1);
    HighFreqEnergy = FMath::Sqrt(HighFreqEnergy / (NumDiffs / 3.0f + 1));
    MidFreqEnergy = FMath::Sqrt(MidFreqEnergy / (NumDiffs / 3.0f + 1));
    LowFreqEnergy = FMath::Sqrt(LowFreqEnergy / (NumDiffs / 3.0f + 1));
    
    // Enhanced zero crossing rate for pitch detection
    int32 ZeroCrossings = 0;
    float LastSample = 0.0f;
    for (int32 i = StartSample; i < EndSample; i += NumChannels)
    {
        float Sample = (float)Samples[i] / 32767.0f;
        if ((LastSample >= 0.0f && Sample < 0.0f) || (LastSample < 0.0f && Sample >= 0.0f))
        {
            ZeroCrossings++;
        }
        LastSample = Sample;
    }
    float ZeroCrossingRate = (float)ZeroCrossings / FMath::Max(1, (NumFrameSamples / NumChannels) - 1);
    
    // Spectral centroid approximation
    float SpectralCentroid = (HighFreqEnergy * 3.0f + MidFreqEnergy * 2.0f + LowFreqEnergy * 1.0f) / 
                            FMath::Max(0.001f, HighFreqEnergy + MidFreqEnergy + LowFreqEnergy);
    
    // Enhanced intensity calculation with adaptive scaling
    float RawIntensity = TotalEnergy;
    
    // Adaptive scaling based on content type
    if (MaxAmplitude > 0.5f) // Loud speech
    {
        RawIntensity *= 1.2f; // Boost for louder signals
    }
    else if (MaxAmplitude < 0.1f) // Quiet speech
    {
        RawIntensity *= 3.5f; // Boost weak signals aggressively
    }
    else
    {
        RawIntensity *= 2.5f; // Boost normal speech
    }
    
    // Dynamic range compression
    RawIntensity = FMath::Pow(RawIntensity, 0.9f);
    
    // Silence detection with improved threshold
    if (TotalEnergy < 0.002f || MaxAmplitude < 0.01f)
    {
        OutVisemeName = "sil";
        OutIntensity = FMath::Lerp(LastFrameIntensity, 0.0f, 0.4f);
        LastFrameIntensity = OutIntensity;
        return;
    }
    
    // Enhanced viseme classification with multiple audio features
    
    // Primary vowel detection with energy-based classification
    if (TotalEnergy > 0.04f && ZeroCrossingRate < 0.35f && SpectralCentroid < 2.2f)
    {
        if (LowFreqEnergy > HighFreqEnergy * 1.3f) // Low formant dominance
        {
            if (MidFreqEnergy > LowFreqEnergy * 0.6f)
            {
                OutVisemeName = "aa"; // Open vowel (mouth wide)
            }
            else
            {
                OutVisemeName = "oh"; // Rounded vowel
            }
        }
        else if (HighFreqEnergy > LowFreqEnergy * 0.6f) // Higher formants
        {
            if (SpectralCentroid > 1.8f)
            {
                OutVisemeName = "ih"; // Close front vowel
            }
            else
            {
                OutVisemeName = "ou"; // U sound for variation
            }
        }
        else // Balanced formants
        {
            OutVisemeName = "E"; // Mid vowel
        }
    }
    // Fricative and sibilant detection
    else if (HighFreqEnergy > 0.08f || (ZeroCrossingRate > 0.4f && SpectralCentroid > 2.0f))
    {
        if (HighFreqEnergy > 0.2f && ZeroCrossingRate > 0.6f) // Strong sibilants
        {
            OutVisemeName = "SS"; // S, Z, SH sounds
        }
        else if (TotalEnergy > 0.03f && HighFreqEnergy > 0.08f) // Fricatives
        {
            if (SpectralCentroid > 2.2f)
            {
                OutVisemeName = "FF"; // F, V, TH sounds
            }
            else
            {
                OutVisemeName = "CH"; // Softer fricatives
            }
        }
        else // Weak fricatives
        {
            OutVisemeName = "TH"; // Dental fricatives
        }
    }
    // Plosive and stop consonant detection
    else if (TotalEnergy > 0.04f && ZeroCrossingRate > 0.25f && MaxAmplitude > 0.15f)
    {
        if (HighFreqEnergy > MidFreqEnergy * 1.0f) // High-frequency bursts
        {
            if (SpectralCentroid > 1.8f)
            {
                OutVisemeName = "kk"; // Velar stops (K, G)
            }
            else
            {
                OutVisemeName = "DD"; // Alveolar stops (D, T)
            }
        }
        else if (LowFreqEnergy > HighFreqEnergy * 0.8f) // Low-frequency emphasis
        {
            OutVisemeName = "PP"; // Bilabial stops (P, B)
        }
        else
        {
            OutVisemeName = "DD"; // Default dental/alveolar
        }
    }
    // Nasal and liquid consonant detection
    else if (TotalEnergy > 0.02f)
    {
        if (ZeroCrossingRate < 0.2f && LowFreqEnergy > HighFreqEnergy * 1.1f) // Low-frequency dominated
        {
            if (MidFreqEnergy > LowFreqEnergy * 0.3f)
            {
                OutVisemeName = "nn"; // Nasal consonants (N, M, NG)
            }
            else
            {
                OutVisemeName = "RR"; // Liquid consonants (R, L)
            }
        }
        else if (ZeroCrossingRate > 0.15f && ZeroCrossingRate < 0.4f) // Moderate modulation
        {
            if (SpectralCentroid > 1.4f)
            {
                OutVisemeName = "ih"; // Weak vowels or consonant transitions
            }
            else
            {
                OutVisemeName = "RR"; // Weak liquids
            }
        }
        else if (TotalEnergy > 0.015f)
        {
            // Low energy but still detectable - use varied visemes
            if (ZeroCrossingRate > 0.3f)
            {
                OutVisemeName = "SS"; // Weak sibilants
            }
            else if (ZeroCrossingRate > 0.2f)
            {
                OutVisemeName = "FF"; // Weak fricatives
            }
            else
            {
                OutVisemeName = "aa"; // Very weak sounds - use vowel
            }
        }
        else // Very low energy content
        {
            OutVisemeName = "sil"; // Near silence
        }
    }
    else
    {
        // Very low energy but not complete silence
        OutVisemeName = "sil";
    }
    
    // Enhanced intensity calculation with viseme-specific multipliers
    float IntensityMultiplier = 1.0f;
    
    // Viseme importance weighting
    if (OutVisemeName == "aa" || OutVisemeName == "oh" || OutVisemeName == "ou")
    {
        IntensityMultiplier = 2.0f; // Boost vowels for more expression
    }
    else if (OutVisemeName == "PP" || OutVisemeName == "FF" || OutVisemeName == "DD")
    {
        IntensityMultiplier = 1.8f; // Boost consonants slightly
    }
    else if (OutVisemeName == "SS" || OutVisemeName == "CH" || OutVisemeName == "TH")
    {
        IntensityMultiplier = 1.6f; // Boost fricatives
    }
    else if (OutVisemeName == "nn" || OutVisemeName == "RR")
    {
        IntensityMultiplier = 1.7f; // Enhance subtle consonants
    }
    else if (OutVisemeName == "E" || OutVisemeName == "ih")
    {
        IntensityMultiplier = 1.8f; // Boost weak vowels
    }
    else if (OutVisemeName == "kk")
    {
        IntensityMultiplier = 1.9f; // Boost K/G sounds for visibility
    }
    
    // Apply intensity scaling
    RawIntensity *= IntensityMultiplier;
    
    // Enhanced smoothing with adaptive interpolation
    float SmoothingFactor = 0.25f; // Default smoothing
    
    // Adaptive smoothing based on energy change
    float EnergyDelta = FMath::Abs(RawIntensity - LastFrameIntensity);
    if (EnergyDelta > 0.3f) // Large energy change
    {
        SmoothingFactor = 0.15f; // Less smoothing for quick changes
    }
    else if (EnergyDelta < 0.05f) // Small energy change
    {
        SmoothingFactor = 0.4f; // More smoothing for stability
    }
    
    // Apply smoothing
    OutIntensity = FMath::Lerp(LastFrameIntensity, RawIntensity, SmoothingFactor);
    
    // Minimum intensity enforcement for non-silence
    if (OutVisemeName != "sil")
    {
        OutIntensity = FMath::Max(OutIntensity, 0.25f); // Higher minimum intensity
    }
    
    // Enhanced final clamping with soft limits
    OutIntensity = FMath::Clamp(OutIntensity, 0.0f, 1.0f);
    
    // Soft limit near maximum to prevent harsh animation
    if (OutIntensity > 0.85f)
    {
        OutIntensity = 0.85f + (OutIntensity - 0.85f) * 0.3f; // Gentle compression at high values
    }
    
    // Store for next frame smoothing
    LastFrameIntensity = OutIntensity;
}

int32 UADSMetahumanLipSync::ParseWAVHeader(const TArray<uint8>& AudioData, int32& OutSampleRate, int32& OutNumChannels)
{
    if (AudioData.Num() < 44)
    {
        return 0;
    }
    
    // Check WAV signature
    if (AudioData[0] != 'R' || AudioData[1] != 'I' || AudioData[2] != 'F' || AudioData[3] != 'F')
    {
        return 0;
    }
    
    // Read parameters from WAV header
    OutNumChannels = *(int16*)(AudioData.GetData() + 22);
    OutSampleRate = *(int32*)(AudioData.GetData() + 24);
    
    // Find PCM data start (search for "data" chunk)
    int32 DataOffset = 44; // Default
    for (int32 i = 12; i < AudioData.Num() - 8; i++)
    {
        if (AudioData[i] == 'd' && AudioData[i+1] == 'a' && AudioData[i+2] == 't' && AudioData[i+3] == 'a')
        {
            DataOffset = i + 8; // Skip "data" + size (4 bytes)
            break;
        }
    }
    
    return DataOffset;
}