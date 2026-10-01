#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HAL/CriticalSection.h"
#include "ADSMetahumanLipSync.generated.h"

DECLARE_LOG_CATEGORY_EXTERN(ADSMetahumanLipSyncLog, Log, All);

// Delegate to notify when viseme values change
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnVisemeValuesChanged, const TArray<float>&, VisemeValues, FString, ActiveVisemeName, float, ActiveVisemeIntensity);

// Structure for a single viseme frame with timing
USTRUCT(BlueprintType)
struct FVisemeFrame
{
    GENERATED_BODY()

    /** The viseme name (e.g., "aa", "E", "sil") */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viseme")
    FString VisemeName = "sil";
    
    /** Intensity of the viseme (0.0 to 1.0) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viseme")
    float Intensity = 0.8f;
    
    /** Duration to hold this viseme in seconds */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Viseme")
    float Duration = 0.1f;

    FVisemeFrame()
    {
        VisemeName = "sil";
        Intensity = 0.0f;
        Duration = 0.1f;
    }

    FVisemeFrame(const FString& InVisemeName, float InIntensity, float InDuration)
        : VisemeName(InVisemeName), Intensity(InIntensity), Duration(InDuration)
    {
    }
};

// ADS Animation Frame structure for precise timing
USTRUCT(BlueprintType)
struct FADSAnimationFrame
{
    GENERATED_BODY()

    /** Map of viseme/blendshape names to their weights */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    TMap<FName, float> BlendShapes;

    FADSAnimationFrame()
    {
        BlendShapes.Empty();
    }
};

// ADS Animation Sequence structure for precise timing
USTRUCT(BlueprintType)
struct FADSAnimationSequence
{
    GENERATED_BODY()

    /** Array of animation frames */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    TArray<FADSAnimationFrame> AnimationFrames;

    /** Total duration of the sequence in seconds */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    float Duration = 0.0f;

    /** Frame rate (frames per second) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    float FrameRate = 60.0f;

    FADSAnimationSequence()
    {
        AnimationFrames.Empty();
        Duration = 0.0f;
        FrameRate = 60.0f;
    }
};

/**
 * Advanced Metahuman Lip Sync Component with Precise Timing Synchronization
 * 
 * This professional-grade component generates viseme data from audio and broadcasts it to 
 * Animation Blueprints with precise timing synchronization. Designed for Metahuman characters 
 * and high-quality facial animation systems, it supports real-time interpolation between frames 
 * and maintains perfect synchronization with audio playback.
 * 
 * Main Usage:
 * 1. Call GenerateAndBroadcastVisemesFromAudio() with your audio data
 * 2. Subscribe to OnVisemeValuesChanged in your Animation Blueprint
 * 3. Use the viseme values to drive facial bone transforms or blend shapes
 * 
 * The system uses tick-based timing updates for precise synchronization and smooth interpolation,
 * making it ideal for professional character animation and Metahuman integration.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class ASCENTDIALOGUESYSTEM_API UADSMetahumanLipSync : public UActorComponent
{
    GENERATED_BODY()

public:
    UADSMetahumanLipSync();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
    
    // === MAIN WORKFLOW FUNCTION ===
    
    /** 
     * Generate visemes from audio and automatically broadcast them to Animation Blueprint 
     * with precise timing synchronization
     */
    UFUNCTION(BlueprintCallable, Category = "ADS Metahuman LipSync")
    bool GenerateAndBroadcastVisemesFromAudio(const TArray<uint8>& AudioData, int32 SampleRate = 16000, int32 NumChannels = 1, float FrameDuration = 0.016f);
    
    /** Stop the viseme broadcast to Animation Blueprint */
    UFUNCTION(BlueprintCallable, Category = "ADS Metahuman LipSync")
    void StopVisemeBroadcast();
    
    /** Force recalculate the start time for precise synchronization */
    UFUNCTION(BlueprintCallable, Category = "ADS Metahuman LipSync")
    void ForceRecalculateStartTime();
    
    // === ANIMATION BLUEPRINT INTERFACE ===
    
    /** Get current viseme values as array of float (for Animation Blueprint) */
    UFUNCTION(BlueprintPure, Category = "ADS Metahuman LipSync")
    TArray<float> GetCurrentVisemeValues() const;
    
    /** Get current active viseme name and intensity */
    UFUNCTION(BlueprintPure, Category = "ADS Metahuman LipSync")
    void GetCurrentActiveViseme(FString& OutVisemeName, float& OutIntensity) const;
    
    /** Get available viseme names */
    UFUNCTION(BlueprintPure, Category = "ADS Metahuman LipSync")
    TArray<FString> GetAvailableVisemes() const;
    
    /** Check if currently playing a sequence */
    UFUNCTION(BlueprintPure, Category = "ADS Metahuman LipSync")
    bool IsPlaying() const { return bIsPlaying; }

    // === EVENTS ===
    
    /** Called when viseme values change (connect this to your Animation Blueprint) */
    UPROPERTY(BlueprintAssignable)
    FOnVisemeValuesChanged OnVisemeValuesChanged;

private:
    
    // === TIMING AND SYNCHRONIZATION ===
    
    // Calculate starting time for precise timing synchronization
    void CalculateStartingTime();
    
    // Tick-based viseme playback for precise timing
    void TickVisemePlayback();
    
    // Interpolate between two frames for smooth animation
    TMap<FName, float> InterpolateFrames(const TMap<FName, float>& StartFrame, const TMap<FName, float>& EndFrame, float Alpha);
    
    // Apply interpolated frame to current state
    void ApplyInterpolatedFrame(const TMap<FName, float>& FrameData);
    
    // Calculate audio duration from raw data
    float CalculateAudioDuration(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels);
    
    // === PRIVATE IMPLEMENTATION ===
    
    // Send silent frame to reset animation
    void SendSilentFrame();
    
    // Generate visemes from audio buffer
    TArray<FVisemeFrame> GenerateVisemesFromAudio(const TArray<uint8>& AudioData, int32 SampleRate, int32 NumChannels, float FrameDuration);
    
    // Analyze a single audio frame for viseme generation
    void AnalyzeAudioFrame(const int16* Samples, int32 StartSample, int32 EndSample, int32 NumChannels, int32 SampleRate, FString& OutVisemeName, float& OutIntensity);
    
    // Parse WAV header and return PCM data offset
    int32 ParseWAVHeader(const TArray<uint8>& AudioData, int32& OutSampleRate, int32& OutNumChannels);
    
    // Static variables for audio frame analysis smoothing
    static float LastFrameIntensity;
    
    // === PRIVATE MEMBER VARIABLES ===
    
    // Viseme names array
    static const TArray<FString> VisemeNames;
    
    // Timing and synchronization variables
    double StartTime;
    float CurrentSequenceTimePassed;
    bool bIsPlaying;
    
    // Animation sequence buffer for precise timing
    FADSAnimationSequence MainSequenceBuffer;
    
    // Critical section for thread safety
    FCriticalSection SequenceCriticalSection;
    
    // Timer for precise tick-based playback
    FTimerHandle VisemePlaybackTimer;
    
    // Current viseme values for Animation Blueprint access
    UPROPERTY()
    TArray<float> CurrentVisemeValues;
    
    UPROPERTY()
    FString CurrentActiveVisemeName;
    
    UPROPERTY()
    float CurrentActiveVisemeIntensity;
};