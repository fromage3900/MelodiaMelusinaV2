// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialogueSubsystem.h"
#include "ADSVoiceConfigDataAsset.h"

UADSVoiceConfigDataAsset* UADSDialogueDeveloperSettings::GetVoiceConfigDataAsset() const
{
    return Cast<UADSVoiceConfigDataAsset>(VoiceConfigDataAsset.TryLoad());
}

FString UADSDialogueDeveloperSettings::ProcessPayloadTemplate(const FString& SystemPrompt, const FString& UserMessage, const FString& Model, int32 InMaxTokens) const
{
    TMap<FString, FString> TagValues;
    TagValues.Add(TEXT("MODEL"), Model);
    TagValues.Add(TEXT("MAX_TOKENS"), FString::FromInt(InMaxTokens));

    // Proper JSON escaping for strings
    FString EscapedSystemPrompt = SystemPrompt;
    EscapedSystemPrompt = EscapedSystemPrompt.Replace(TEXT("\\"), TEXT("\\\\")); // Escape backslashes first
    EscapedSystemPrompt = EscapedSystemPrompt.Replace(TEXT("\""), TEXT("\\\"")); // Escape quotes
    EscapedSystemPrompt = EscapedSystemPrompt.Replace(TEXT("\n"), TEXT("\\n")); // Escape newlines
    EscapedSystemPrompt = EscapedSystemPrompt.Replace(TEXT("\r"), TEXT("\\r")); // Escape carriage returns
    EscapedSystemPrompt = EscapedSystemPrompt.Replace(TEXT("\t"), TEXT("\\t")); // Escape tabs

    FString EscapedUserMessage = UserMessage;
    EscapedUserMessage = EscapedUserMessage.Replace(TEXT("\\"), TEXT("\\\\")); // Escape backslashes first
    EscapedUserMessage = EscapedUserMessage.Replace(TEXT("\""), TEXT("\\\"")); // Escape quotes
    EscapedUserMessage = EscapedUserMessage.Replace(TEXT("\n"), TEXT("\\n")); // Escape newlines
    EscapedUserMessage = EscapedUserMessage.Replace(TEXT("\r"), TEXT("\\r")); // Escape carriage returns
    EscapedUserMessage = EscapedUserMessage.Replace(TEXT("\t"), TEXT("\\t")); // Escape tabs

    TagValues.Add(TEXT("SYSTEM_PROMPT"), EscapedSystemPrompt);
    TagValues.Add(TEXT("USER_MESSAGE"), EscapedUserMessage);
    TagValues.Add(TEXT("TEMPERATURE"), TEXT("0.7"));

    return ReplaceTags(AIPayloadTemplate, TagValues);
}

TMap<FString, FString> UADSDialogueDeveloperSettings::ProcessHeadersTemplate(const FString& APIKey) const
{
    TMap<FString, FString> TagValues;
    TagValues.Add(TEXT("API_KEY"), APIKey);
    TagValues.Add(TEXT("ANTHROPIC_VERSION"), TEXT("2023-06-01"));

    FString ProcessedHeaders = ReplaceTags(AIRequestHeaders, TagValues);

    // Parse headers into map
    TMap<FString, FString> HeadersMap;
    TArray<FString> HeaderLines;
    ProcessedHeaders.ParseIntoArrayLines(HeaderLines);

    for (const FString& Line : HeaderLines) {
        FString Key, Value;
        if (Line.Split(TEXT(": "), &Key, &Value)) {
            HeadersMap.Add(Key.TrimStartAndEnd(), Value.TrimStartAndEnd());
        }
    }

    return HeadersMap;
}

FString UADSDialogueDeveloperSettings::ProcessTTSPayloadTemplate(const FString& Text, const FString& Voice, const FString& Model) const
{
    TMap<FString, FString> TagValues;
    TagValues.Add(TEXT("MODEL"), Model);
    TagValues.Add(TEXT("VOICE"), Voice);
    TagValues.Add(TEXT("RESPONSE_FORMAT"), TEXT("wav"));
    TagValues.Add(TEXT("SPEED"), TEXT("1.0"));

    // Proper JSON escaping for the input text
    FString EscapedText = Text;
    EscapedText = EscapedText.Replace(TEXT("\\"), TEXT("\\\\")); // Escape backslashes first
    EscapedText = EscapedText.Replace(TEXT("\""), TEXT("\\\"")); // Escape quotes
    EscapedText = EscapedText.Replace(TEXT("\n"), TEXT("\\n")); // Escape newlines
    EscapedText = EscapedText.Replace(TEXT("\r"), TEXT("\\r")); // Escape carriage returns
    EscapedText = EscapedText.Replace(TEXT("\t"), TEXT("\\t")); // Escape tabs

    TagValues.Add(TEXT("INPUT"), EscapedText);

    return ReplaceTags(TTSPayloadTemplate, TagValues);
}

TMap<FString, FString> UADSDialogueDeveloperSettings::ProcessTTSHeadersTemplate(const FString& APIKey) const
{
    TMap<FString, FString> TagValues;
    TagValues.Add(TEXT("API_KEY"), APIKey);

    FString ProcessedHeaders = ReplaceTags(TTSRequestHeaders, TagValues);

    // Parse headers into map
    TMap<FString, FString> HeadersMap;
    TArray<FString> HeaderLines;
    ProcessedHeaders.ParseIntoArrayLines(HeaderLines);

    for (const FString& Line : HeaderLines) {
        FString Key, Value;
        if (Line.Split(TEXT(": "), &Key, &Value)) {
            HeadersMap.Add(Key.TrimStartAndEnd(), Value.TrimStartAndEnd());
        }
    }

    return HeadersMap;
}





FString UADSDialogueDeveloperSettings::ReplaceTags(const FString& Template, const TMap<FString, FString>& TagValues) const
{
    FString Result = Template;

    for (const auto& TagPair : TagValues) {
        const FString TagName = FString::Printf(TEXT("{%s}"), *TagPair.Key);
        Result = Result.Replace(*TagName, *TagPair.Value);
    }

    return Result;
}

