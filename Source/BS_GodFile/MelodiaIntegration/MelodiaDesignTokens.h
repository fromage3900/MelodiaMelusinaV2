// MelodiaDesignTokens.h
// Design token data asset for Figma → UE token bridge
// Generated from melodia-design-system/tokens.json

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaDesignTokens.generated.h"

/**
 * Single color token with hex value and description
 */
USTRUCT(BlueprintType)
struct FMelodiaColorToken
{
    GENERATED_BODY()

    /** Hex color string (e.g., "#C9A86A") */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Hex;

    /** Linear color value (parsed from hex) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FLinearColor LinearColor;

    /** Description from Figma token */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Description;

    FMelodiaColorToken()
        : Hex("#FFFFFF")
        , LinearColor(FLinearColor::White)
        , Description(TEXT(""))
    {}
};

/**
 * Spacing token (pixels)
 */
USTRUCT(BlueprintType)
struct FMelodiaSpacingToken
{
    GENERATED_BODY()

    /** Spacing value in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float Value;

    /** Description from Figma token */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Description;

    FMelodiaSpacingToken()
        : Value(0.0f)
        , Description(TEXT(""))
    {}
};

/**
 * Border radius token
 */
USTRUCT(BlueprintType)
struct FMelodiaRadiusToken
{
    GENERATED_BODY()

    /** Radius value in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float Value;

    /** Description from Figma token */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Description;

    FMelodiaRadiusToken()
        : Value(0.0f)
        , Description(TEXT(""))
    {}
};

/**
 * Typography token
 */
USTRUCT(BlueprintType)
struct FMelodiaTypographyToken
{
    GENERATED_BODY()

    /** Font family name */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString FontFamily;

    /** Font size in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    int32 FontSize;

    /** Font weight (Light, Regular, Medium, SemiBold, Bold) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString FontWeight;

    /** Line height in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    int32 LineHeight;

    /** Letter spacing (percentage, e.g., "-2%" or "8%") */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString LetterSpacing;

    /** Text case (none, uppercase) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString TextCase;

    /** Description from Figma token */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Description;

    FMelodiaTypographyToken()
        : FontFamily(TEXT("Default"))
        , FontSize(16)
        , FontWeight(TEXT("Regular"))
        , LineHeight(24)
        , LetterSpacing(TEXT("0"))
        , TextCase(TEXT("none"))
        , Description(TEXT(""))
    {}
};

/**
 * Box shadow / glow effect token
 */
USTRUCT(BlueprintType)
struct FMelodiaEffectToken
{
    GENERATED_BODY()

    /** X offset in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float X;

    /** Y offset in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float Y;

    /** Blur radius in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float Blur;

    /** Spread radius in pixels */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    float Spread;

    /** Color (rgba string or linear color) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FLinearColor Color;

    /** Effect type (boxShadow, dropShadow) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Type;

    /** Description from Figma token */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Token")
    FString Description;

    FMelodiaEffectToken()
        : X(0.0f)
        , Y(0.0f)
        , Blur(0.0f)
        , Spread(0.0f)
        , Color(FLinearColor::Black)
        , Type(TEXT("boxShadow"))
        , Description(TEXT(""))
    {}
};

/**
 * Sparkle density tier configuration
 */
USTRUCT(BlueprintType)
struct FMelodiaSparkleTier
{
    GENERATED_BODY()

    /** Particle density multiplier (0.0 = off, 1.0 = full) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sparkle")
    float Density;

    /** Whether motion is enabled */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sparkle")
    bool bMotionEnabled;

    FMelodiaSparkleTier()
        : Density(0.0f)
        , bMotionEnabled(false)
    {}
};

/**
 * Melodia Design Tokens Data Asset
 * 
 * This data asset stores all design tokens from the Figma design system,
 * providing a single source of truth for colors, spacing, typography, and effects.
 * 
 * Usage:
 * - Load this asset in widgets to access design tokens
 * - Use GetColorToken(), GetSpacingToken(), etc. to retrieve values
 * - Tokens are Blueprint-readable for easy UI integration
 */
UCLASS()
class BS_GODFILE_API UMelodiaDesignTokens : public UDataAsset
{
    GENERATED_BODY()

public:
    /** Color tokens (primitives + semantic) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Colors", meta = (TitleProperty = "Hex"))
    TMap<FString, FMelodiaColorToken> Colors;

    /** Spacing tokens */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spacing", meta = (TitleProperty = "Value"))
    TMap<FString, FMelodiaSpacingToken> Spacing;

    /** Border radius tokens */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Radius", meta = (TitleProperty = "Value"))
    TMap<FString, FMelodiaRadiusToken> Radius;

    /** Typography tokens */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Typography", meta = (TitleProperty = "FontFamily"))
    TMap<FString, FMelodiaTypographyToken> Typography;

    /** Effect tokens (shadows, glows) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effects", meta = (TitleProperty = "Type"))
    TMap<FString, FMelodiaEffectToken> Effects;

    /** Game-specific colors (VoidPlate, ParchmentField, GoldBorder, etc.) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Colors")
    TMap<FString, FLinearColor> GameColors;

    /** Keybind colors (Interact, Attack, Skill, Ultimate, Menu, Back) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Keybind Colors")
    TMap<FString, FLinearColor> KeybindColors;

    /** Sparkle density tiers (Full, Soft, Chrome, Off) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sparkle")
    TMap<FString, FMelodiaSparkleTier> SparkleTiers;

    /** Default constructor */
    UMelodiaDesignTokens();

    /** Get a color token by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FLinearColor GetColor(const FString& Key, const FLinearColor& Default = FLinearColor::White) const;

    /** Get a spacing token by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    float GetSpacing(const FString& Key, float Default = 0.0f) const;

    /** Get a radius token by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    float GetRadius(const FString& Key, float Default = 0.0f) const;

    /** Get a typography token by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FMelodiaTypographyToken GetTypography(const FString& Key) const;

    /** Get an effect token by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FMelodiaEffectToken GetEffect(const FString& Key) const;

    /** Get a game color by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FLinearColor GetGameColor(const FString& Key, const FLinearColor& Default = FLinearColor::White) const;

    /** Get a keybind color by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FLinearColor GetKeybindColor(const FString& Key, const FLinearColor& Default = FLinearColor::White) const;

    /** Get a sparkle tier by key */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    FMelodiaSparkleTier GetSparkleTier(const FString& Key) const;

    /** Parse hex string to FLinearColor */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    static FLinearColor HexToLinearColor(const FString& Hex);

    /** Parse FLinearColor to hex string */
    UFUNCTION(BlueprintCallable, Category = "Design Tokens")
    static FString LinearColorToHex(const FLinearColor& Color);
};
