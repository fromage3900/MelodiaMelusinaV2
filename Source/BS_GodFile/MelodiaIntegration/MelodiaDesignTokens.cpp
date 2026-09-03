// MelodiaDesignTokens.cpp
// Design token data asset implementation

#include "MelodiaDesignTokens.h"
#include "Internationalization/Regex.h"

UMelodiaDesignTokens::UMelodiaDesignTokens()
{
    // Initialize with empty maps
}

FLinearColor UMelodiaDesignTokens::GetColor(const FString& Key, const FLinearColor& Default) const
{
    if (const FMelodiaColorToken* Token = Colors.Find(Key))
    {
        return Token->LinearColor;
    }
    return Default;
}

float UMelodiaDesignTokens::GetSpacing(const FString& Key, float Default) const
{
    if (const FMelodiaSpacingToken* Token = Spacing.Find(Key))
    {
        return Token->Value;
    }
    return Default;
}

float UMelodiaDesignTokens::GetRadius(const FString& Key, float Default) const
{
    if (const FMelodiaRadiusToken* Token = Radius.Find(Key))
    {
        return Token->Value;
    }
    return Default;
}

FMelodiaTypographyToken UMelodiaDesignTokens::GetTypography(const FString& Key) const
{
    if (const FMelodiaTypographyToken* Token = Typography.Find(Key))
    {
        return *Token;
    }
    return FMelodiaTypographyToken(); // Return default
}

FMelodiaEffectToken UMelodiaDesignTokens::GetEffect(const FString& Key) const
{
    if (const FMelodiaEffectToken* Token = Effects.Find(Key))
    {
        return *Token;
    }
    return FMelodiaEffectToken(); // Return default
}

FLinearColor UMelodiaDesignTokens::GetGameColor(const FString& Key, const FLinearColor& Default) const
{
    if (const FLinearColor* Color = GameColors.Find(Key))
    {
        return *Color;
    }
    return Default;
}

FLinearColor UMelodiaDesignTokens::GetKeybindColor(const FString& Key, const FLinearColor& Default) const
{
    if (const FLinearColor* Color = KeybindColors.Find(Key))
    {
        return *Color;
    }
    return Default;
}

FMelodiaSparkleTier UMelodiaDesignTokens::GetSparkleTier(const FString& Key) const
{
    if (const FMelodiaSparkleTier* Tier = SparkleTiers.Find(Key))
    {
        return *Tier;
    }
    return FMelodiaSparkleTier(); // Return default (off)
}

FLinearColor UMelodiaDesignTokens::HexToLinearColor(const FString& Hex)
{
    FString CleanHex = Hex;
    
    // Remove # prefix if present
    if (CleanHex.StartsWith("#"))
    {
        CleanHex.RemoveAt(0);
    }
    
    // Handle rgba() format
    if (CleanHex.StartsWith("rgba("))
    {
        // Parse rgba(r, g, b, a)
        FRegexPattern Pattern(TEXT("rgba\\s*\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*([\\d.]+)\\s*\\)"));
        FRegexMatcher Matcher(Pattern, CleanHex);
        
        if (Matcher.FindNext())
        {
            int32 R = FCString::Atoi(*Matcher.GetCaptureGroup(1));
            int32 G = FCString::Atoi(*Matcher.GetCaptureGroup(2));
            int32 B = FCString::Atoi(*Matcher.GetCaptureGroup(3));
            float A = FCString::Atof(*Matcher.GetCaptureGroup(4));
            
            return FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, A);
        }
        
        return FLinearColor::White;
    }
    
    // Handle 6-digit hex (#RRGGBB)
    if (CleanHex.Len() == 6)
    {
        int32 R = FCString::Strtoi(*CleanHex.Mid(0, 2), nullptr, 16);
        int32 G = FCString::Strtoi(*CleanHex.Mid(2, 2), nullptr, 16);
        int32 B = FCString::Strtoi(*CleanHex.Mid(4, 2), nullptr, 16);
        
        return FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f);
    }
    
    // Handle 8-digit hex (#RRGGBBAA)
    if (CleanHex.Len() == 8)
    {
        int32 R = FCString::Strtoi(*CleanHex.Mid(0, 2), nullptr, 16);
        int32 G = FCString::Strtoi(*CleanHex.Mid(2, 2), nullptr, 16);
        int32 B = FCString::Strtoi(*CleanHex.Mid(4, 2), nullptr, 16);
        int32 A = FCString::Strtoi(*CleanHex.Mid(6, 2), nullptr, 16);
        
        return FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, A / 255.0f);
    }
    
    // Handle 3-digit hex (#RGB)
    if (CleanHex.Len() == 3)
    {
        int32 R = FCString::Strtoi(*FString::ChrN(2, CleanHex[0]), nullptr, 16);
        int32 G = FCString::Strtoi(*FString::ChrN(2, CleanHex[1]), nullptr, 16);
        int32 B = FCString::Strtoi(*FString::ChrN(2, CleanHex[2]), nullptr, 16);
        
        return FLinearColor(R / 255.0f, G / 255.0f, B / 255.0f, 1.0f);
    }
    
    return FLinearColor::White;
}

FString UMelodiaDesignTokens::LinearColorToHex(const FLinearColor& Color)
{
    int32 R = FMath::RoundToInt(Color.R * 255.0f);
    int32 G = FMath::RoundToInt(Color.G * 255.0f);
    int32 B = FMath::RoundToInt(Color.B * 255.0f);
    int32 A = FMath::RoundToInt(Color.A * 255.0f);
    
    return FString::Printf(TEXT("#%02X%02X%02X%02X"), R, G, B, A);
}
