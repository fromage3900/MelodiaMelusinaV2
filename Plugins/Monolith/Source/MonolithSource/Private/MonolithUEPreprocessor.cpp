#include "MonolithUEPreprocessor.h"
#include "Internationalization/Regex.h"

namespace MonolithUEPreprocessor
{

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

static bool IsAlnumOrUnderscore(TCHAR C)
{
    return (C >= TEXT('A') && C <= TEXT('Z'))
        || (C >= TEXT('a') && C <= TEXT('z'))
        || (C >= TEXT('0') && C <= TEXT('9'))
        || (C == TEXT('_'));
}

/** Replace every non-newline character in Buf[Start, End) with a space. */
static void BlankSpan(TArray<TCHAR>& Buf, int32 Start, int32 End)
{
    for (int32 i = Start; i < End; ++i)
    {
        if (Buf[i] != TEXT('\n'))
        {
            Buf[i] = TEXT(' ');
        }
    }
}

// ---------------------------------------------------------------------------
// Phase 1 — balanced-paren class macros
// ---------------------------------------------------------------------------

static const TCHAR* ClassMacros[] = {
    TEXT("UCLASS"),
    TEXT("USTRUCT"),
    TEXT("UENUM"),
    TEXT("UINTERFACE"),
};
static const int32 NumClassMacros = UE_ARRAY_COUNT(ClassMacros);

static void StripClassMacros(TArray<TCHAR>& Buf)
{
    const int32 Len = Buf.Num() - 1; // exclude null terminator

    int32 i = 0;
    while (i < Len)
    {
        bool bMatched = false;

        for (int32 m = 0; m < NumClassMacros; ++m)
        {
            const TCHAR* Macro    = ClassMacros[m];
            const int32  MacroLen = FCString::Strlen(Macro);

            if (i + MacroLen > Len)
            {
                continue;
            }

            // Case-sensitive prefix match
            if (FMemory::Memcmp(&Buf[i], Macro, MacroLen * sizeof(TCHAR)) != 0)
            {
                continue;
            }

            // Word boundary — preceding char must NOT be alnum/underscore
            if (i > 0 && IsAlnumOrUnderscore(Buf[i - 1]))
            {
                continue;
            }

            // Word boundary — char immediately after macro name must NOT be alnum/underscore
            const int32 After = i + MacroLen;
            if (After < Len && IsAlnumOrUnderscore(Buf[After]))
            {
                continue;
            }

            // Skip optional whitespace (space, tab, CR) to find opening paren
            int32 j = After;
            while (j < Len && (Buf[j] == TEXT(' ') || Buf[j] == TEXT('\t') || Buf[j] == TEXT('\r')))
            {
                ++j;
            }

            if (j >= Len || Buf[j] != TEXT('('))
            {
                continue;
            }

            // Balanced-paren scan to find the matching ')'
            int32 Depth = 1;
            int32 k     = j + 1;
            while (k < Len && Depth > 0)
            {
                if      (Buf[k] == TEXT('(')) { ++Depth; }
                else if (Buf[k] == TEXT(')')) { --Depth; }
                ++k;
            }

            if (Depth != 0)
            {
                // Unbalanced — leave it alone
                continue;
            }

            // Replace [i, k) with spaces, preserving newlines
            BlankSpan(Buf, i, k);
            i       = k;
            bMatched = true;
            break;
        }

        if (!bMatched)
        {
            ++i;
        }
    }
}

// ---------------------------------------------------------------------------
// Phase 2 & 3 — regex-based replacements
// ---------------------------------------------------------------------------

static void StripRegexMatches(TArray<TCHAR>& Buf, const FString& WorkStr, const FString& Pattern)
{
    FRegexPattern RegexPattern(Pattern);
    FRegexMatcher Matcher(RegexPattern, WorkStr);

    while (Matcher.FindNext())
    {
        const int32 Start = Matcher.GetMatchBeginning();
        const int32 End   = Matcher.GetMatchEnding();
        BlankSpan(Buf, Start, End);
    }
}

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

FString PreprocessSource(const FString& Source)
{
    // Copy into a mutable TCHAR array.
    // TArray<TCHAR> includes the null terminator when built from FString data.
    const int32 SourceLen = Source.Len();

    TArray<TCHAR> Buf;
    Buf.SetNumUninitialized(SourceLen + 1);
    FMemory::Memcpy(Buf.GetData(), *Source, (SourceLen + 1) * sizeof(TCHAR));

    // Phase 1: balanced-paren class macros (must run on the mutable buffer
    // directly — regex can't handle arbitrary nesting depth).
    StripClassMacros(Buf);

    // Build a string view of the current buffer for regex phases.
    // We rebuild it after Phase 1 so the regex sees already-blanked UCLASS etc.
    // Buf is null-terminated so FString(const TCHAR*) works directly.
    FString WorkStr(Buf.GetData());

    // Phase 2: GENERATED_BODY / GENERATED_UCLASS_BODY / GENERATED_USTRUCT_BODY
    // Pattern matches the full token including the empty parens.
    StripRegexMatches(
        Buf,
        WorkStr,
        TEXT("\\bGENERATED_(?:UCLASS_|USTRUCT_)?BODY\\s*\\(\\s*\\)")
    );

    // Phase 3: API export macros  e.g. ENGINE_API, CORE_API, MY_MODULE_API
    // ICU lookbehind/lookahead supported by FRegexMatcher.
    StripRegexMatches(
        Buf,
        WorkStr,
        TEXT("(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*_API(?![A-Za-z0-9_])")
    );

    // Build result string from null-terminated buffer.
    FString Result(Buf.GetData());

    // Sanity check: output must be the same length as input.
    check(Result.Len() == SourceLen);

    return Result;
}

} // namespace MonolithUEPreprocessor
