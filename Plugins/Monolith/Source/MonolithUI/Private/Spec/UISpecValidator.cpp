// Copyright tumourlove. All Rights Reserved.
#include "Spec/UISpecValidator.h"

#include "MonolithUICommon.h"          // LogMonolithUISpec

#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace MonolithUI::SpecValidatorInternal
{
    /**
     * Build the canonical "missing rootWidget" finding. Centralised here so
     * the JSON-string path and the parsed-document path emit identical
     * messages (matters for LLM-targeted error matching).
     */
    static FUISpecError MakeMissingRootError()
    {
        FUISpecError Err;
        Err.Severity    = EUISpecErrorSeverity::Error;
        Err.Category    = TEXT("Structure");
        Err.JsonPath    = TEXT("/rootWidget");
        Err.Message     = TEXT("UISpec document is missing required field 'rootWidget' (FUISpecDocument::Root).");
        Err.SuggestedFix = TEXT("Add a 'rootWidget' object describing the top-level widget node.");
        Err.ValidOptions = { TEXT("rootWidget") };
        return Err;
    }

    /**
     * Phase H — animation ref pre-flight. Walks the spec tree and verifies
     * every `AnimationRefs` entry on every node resolves to a named entry in
     * `Document.Animations`. Pushes one warning-severity finding per missing
     * ref (warning, not error: missing animation refs degrade gracefully —
     * the widget builds, the animation simply doesn't fire).
     */
    static void ValidateAnimationRefs(
        const FUISpecNode& Node,
        const TSet<FName>& KnownAnimNames,
        FUISpecValidationResult& OutResult)
    {
        for (const FName& Ref : Node.AnimationRefs)
        {
            if (Ref.IsNone()) continue;
            if (!KnownAnimNames.Contains(Ref))
            {
                FUISpecError W;
                W.Severity = EUISpecErrorSeverity::Warning;
                W.Category = TEXT("AnimationRef");
                W.WidgetId = Node.Id;
                W.JsonPath = FString::Printf(TEXT("/.../%s/animationRefs"), *Node.Id.ToString());
                W.Message  = FString::Printf(
                    TEXT("Node '%s' references animation '%s' which is not defined in document.animations."),
                    *Node.Id.ToString(), *Ref.ToString());
                W.SuggestedFix = TEXT("Add the animation to document.animations, or remove the ref.");
                OutResult.Warnings.Add(MoveTemp(W));
            }
        }
        for (const TSharedPtr<FUISpecNode>& Child : Node.Children)
        {
            if (Child.IsValid())
            {
                ValidateAnimationRefs(*Child, KnownAnimNames, OutResult);
            }
        }
    }

    /**
     * Phase H — style ref pre-flight. Same shape as the animation check.
     * Missing style refs degrade gracefully (the widget builds without the
     * extra style overlay), so we record a warning rather than blocking.
     */
    static void ValidateStyleRefs(
        const FUISpecNode& Node,
        const TSet<FName>& KnownStyleNames,
        FUISpecValidationResult& OutResult)
    {
        if (!Node.StyleRef.IsNone())
        {
            if (!KnownStyleNames.Contains(Node.StyleRef))
            {
                FUISpecError W;
                W.Severity = EUISpecErrorSeverity::Warning;
                W.Category = TEXT("StyleRef");
                W.WidgetId = Node.Id;
                W.JsonPath = FString::Printf(TEXT("/.../%s/styleRef"), *Node.Id.ToString());
                W.Message  = FString::Printf(
                    TEXT("Node '%s' references style '%s' which is not defined in document.styles."),
                    *Node.Id.ToString(), *Node.StyleRef.ToString());
                W.SuggestedFix = TEXT("Add the style to document.styles, or remove the ref.");
                OutResult.Warnings.Add(MoveTemp(W));
            }
        }
        for (const TSharedPtr<FUISpecNode>& Child : Node.Children)
        {
            if (Child.IsValid())
            {
                ValidateStyleRefs(*Child, KnownStyleNames, OutResult);
            }
        }
    }
}

FUISpecValidationResult FUISpecValidator::Validate(const FUISpecDocument& Document)
{
    using namespace MonolithUI::SpecValidatorInternal;

    FUISpecValidationResult Result;

    // Structural: root must exist.
    if (!Document.Root.IsValid())
    {
        Result.Errors.Add(MakeMissingRootError());
        UE_LOG(LogMonolithUISpec, Verbose,
            TEXT("FUISpecValidator: rejected document — missing root node."));
        Result.bIsValid = false;
        return Result;
    }

    // Phase H — animation refs.
    {
        TSet<FName> KnownAnims;
        KnownAnims.Reserve(Document.Animations.Num());
        for (const FUISpecAnimation& A : Document.Animations)
        {
            if (!A.Name.IsNone())
            {
                KnownAnims.Add(A.Name);
            }
        }
        ValidateAnimationRefs(*Document.Root, KnownAnims, Result);
    }

    // Phase H — style refs.
    {
        TSet<FName> KnownStyles;
        KnownStyles.Reserve(Document.Styles.Num());
        for (const TPair<FName, FUISpecStyle>& Pair : Document.Styles)
        {
            KnownStyles.Add(Pair.Key);
        }
        ValidateStyleRefs(*Document.Root, KnownStyles, Result);
    }

    // NOTE: depth limit + cycle detection + per-node type-registry lookup are
    // performed by `FUISpecBuilder` during the dry-walk because they need
    // access to the live registry (which lives in an editor subsystem the
    // pure validator deliberately doesn't reach into). Validator findings
    // produced by the dry-walk are appended to the same FUISpecValidationResult.

    Result.bIsValid = (Result.Errors.Num() == 0);
    return Result;
}

FUISpecValidationResult FUISpecValidator::ValidateFromJson(const FString& JsonText)
{
    using namespace MonolithUI::SpecValidatorInternal;

    // Empty string or pure-whitespace body: treat as a missing root since the
    // test harness needs a deterministic error from `{}` / "" inputs.
    const FString Trimmed = JsonText.TrimStartAndEnd();
    if (Trimmed.IsEmpty())
    {
        FUISpecValidationResult Result;
        Result.Errors.Add(MakeMissingRootError());
        Result.bIsValid = false;
        return Result;
    }

    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    TSharedPtr<FJsonObject> JsonObject;
    if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
    {
        FUISpecValidationResult Result;
        FUISpecError Err;
        Err.Severity = EUISpecErrorSeverity::Error;
        Err.Category = TEXT("Parse");
        Err.JsonPath = TEXT("/");
        Err.Message  = FString::Printf(
            TEXT("UISpec JSON parse failure: %s"),
            *Reader->GetErrorMessage());
        Err.Line   = (int32)Reader->GetLineNumber();
        Err.Column = (int32)Reader->GetCharacterNumber();
        Result.Errors.Add(MoveTemp(Err));
        Result.bIsValid = false;
        return Result;
    }

    return ValidateFromJson(JsonObject);
}

FUISpecValidationResult FUISpecValidator::ValidateFromJson(const TSharedPtr<FJsonObject>& JsonObject)
{
    using namespace MonolithUI::SpecValidatorInternal;

    FUISpecValidationResult Result;

    if (!JsonObject.IsValid())
    {
        Result.Errors.Add(MakeMissingRootError());
        Result.bIsValid = false;
        return Result;
    }

    // Phase A: the only structural rule is "rootWidget must be present".
    const TSharedPtr<FJsonObject>* RootObj = nullptr;
    if (!JsonObject->TryGetObjectField(TEXT("rootWidget"), RootObj) || !RootObj || !(*RootObj).IsValid())
    {
        Result.Errors.Add(MakeMissingRootError());
    }

    Result.bIsValid = (Result.Errors.Num() == 0);
    return Result;
}

// ---------------------------------------------------------------------------
// Phase K — FUISpecError per-finding formatters
//
// Both formatters live here (next to the FUISpecValidationResult aggregate
// formatters they're consumed by) so the dual-audience format conventions
// stay byte-identical between the per-finding and per-aggregate paths.
//
// `ToString` is a one-line human summary suitable for log messages and
// human-debugging surfaces (the editor's Output Log, automation test
// failure messages).
//
// `ToLLMReport` is a stable key:value block. Field order and field names
// MUST stay stable — external automation harnesses may grep on `json_path:`,
// `suggested_fix:`, and `valid_options:` to route validation failures back to
// an upstream LLM with full context. Adding fields is allowed; renaming or
// removing existing ones is a breaking change.

FString FUISpecError::ToString() const
{
    // Compact one-line shape — matches the aggregate ToString rendering of
    // a single finding so log output stays consistent regardless of which
    // formatter the caller reaches for.
    FString Out = FString::Printf(
        TEXT("[%s] %s: %s"),
        (Severity == EUISpecErrorSeverity::Error)   ? TEXT("ERR ") :
        (Severity == EUISpecErrorSeverity::Warning) ? TEXT("WARN") : TEXT("INFO"),
        JsonPath.IsEmpty() ? TEXT("/") : *JsonPath,
        *Message);

    if (!SuggestedFix.IsEmpty())
    {
        Out += FString::Printf(TEXT("  hint: %s"), *SuggestedFix);
    }
    if (ValidOptions.Num() > 0)
    {
        // Compact preview — full enumeration belongs in ToLLMReport. Cap at
        // 5 options + ellipsis so a one-liner stays readable when an enum
        // has 17+ values (e.g. anchor presets).
        const int32 Cap = FMath::Min(ValidOptions.Num(), 5);
        FString Joined = FString::Join(
            TArrayView<const FString>(ValidOptions.GetData(), Cap), TEXT(", "));
        if (ValidOptions.Num() > Cap)
        {
            Joined += FString::Printf(TEXT(", ... (%d total)"), ValidOptions.Num());
        }
        Out += FString::Printf(TEXT("  valid_options: %s"), *Joined);
    }
    return Out;
}

FString FUISpecError::ToLLMReport() const
{
    // Stable key:value block. Field order chosen so the most-disambiguating
    // labels (json_path + category) come first — useful when the LLM is
    // routing a re-prompt by categorisation. severity is emitted unconditionally
    // because the aggregate formatter relies on the per-finding kind label;
    // a standalone finding still benefits from the explicit severity line.
    FString Out;
    Out += FString::Printf(TEXT("category: %s\n"),
        Category.IsNone() ? TEXT("Uncategorized") : *Category.ToString());
    Out += FString::Printf(TEXT("severity: %s\n"),
        (Severity == EUISpecErrorSeverity::Error)   ? TEXT("error") :
        (Severity == EUISpecErrorSeverity::Warning) ? TEXT("warning") : TEXT("info"));
    Out += FString::Printf(TEXT("json_path: %s\n"),
        JsonPath.IsEmpty() ? TEXT("/") : *JsonPath);
    if (!WidgetId.IsNone())
    {
        Out += FString::Printf(TEXT("widget_id: %s\n"), *WidgetId.ToString());
    }
    Out += FString::Printf(TEXT("message: %s\n"), *Message);
    if (!SuggestedFix.IsEmpty())
    {
        Out += FString::Printf(TEXT("suggested_fix: %s\n"), *SuggestedFix);
    }
    if (ValidOptions.Num() > 0)
    {
        Out += TEXT("valid_options:\n");
        for (const FString& Opt : ValidOptions)
        {
            // Two-space indent under the parent key — matches the aggregate
            // formatter's nested indentation so output composes cleanly when
            // the per-finding block is embedded into the larger report.
            Out += FString::Printf(TEXT("  - %s\n"), *Opt);
        }
    }
    if (Line > 0)
    {
        Out += FString::Printf(TEXT("line: %d\n"), Line);
        Out += FString::Printf(TEXT("column: %d\n"), Column);
    }
    return Out;
}

// ---------------------------------------------------------------------------
// FUISpecValidationResult formatters

FString FUISpecValidationResult::ToString() const
{
    FString Out;
    Out += FString::Printf(TEXT("UISpec validation %s — %d error(s), %d warning(s).\n"),
        bIsValid ? TEXT("OK") : TEXT("FAILED"),
        Errors.Num(), Warnings.Num());

    auto AppendOne = [&Out](const FUISpecError& E, const TCHAR* Bucket)
    {
        Out += FString::Printf(
            TEXT("  [%s] %s: %s%s%s\n"),
            Bucket,
            E.JsonPath.IsEmpty() ? TEXT("/") : *E.JsonPath,
            *E.Message,
            E.SuggestedFix.IsEmpty() ? TEXT("") : TEXT("  hint: "),
            E.SuggestedFix.IsEmpty() ? TEXT("") : *E.SuggestedFix);
    };

    for (const FUISpecError& E : Errors)   { AppendOne(E, TEXT("ERR ")); }
    for (const FUISpecError& W : Warnings) { AppendOne(W, TEXT("WARN")); }
    return Out;
}

FString FUISpecValidationResult::ToLLMReport() const
{
    // LLM-targeted format — explicit field labels, no decorative punctuation.
    // Phase K refactor: per-finding rendering now delegates to FUISpecError::
    // ToLLMReport so the same key:value lines emitted in standalone-finding
    // surfaces (action error responses) appear identically inside the aggregate
    // report. Field labels stay stable for grep-based consumers.
    FString Out;
    Out += FString::Printf(TEXT("validation_status: %s\n"),
        bIsValid ? TEXT("ok") : TEXT("failed"));
    Out += FString::Printf(TEXT("error_count: %d\n"), Errors.Num());
    Out += FString::Printf(TEXT("warning_count: %d\n"), Warnings.Num());

    auto AppendOne = [&Out](const FUISpecError& E, const TCHAR* Kind)
    {
        // Discriminator line first ("- kind: error/warning") — preserves the
        // pre-Phase-K aggregate shape so any existing consumer that splits on
        // `^- kind:` keeps working.
        Out += FString::Printf(TEXT("- kind: %s\n"), Kind);
        // Indent the per-finding block by two spaces so the YAML-ish nesting
        // stays valid. Split on newlines + re-emit with the indent prefix
        // because the per-finding formatter naturally emits zero-indent lines.
        const FString PerFinding = E.ToLLMReport();
        TArray<FString> Lines;
        PerFinding.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);
        for (const FString& Line : Lines)
        {
            if (!Line.IsEmpty())
            {
                Out += FString::Printf(TEXT("  %s\n"), *Line);
            }
        }
    };

    for (const FUISpecError& E : Errors)   { AppendOne(E, TEXT("error")); }
    for (const FUISpecError& W : Warnings) { AppendOne(W, TEXT("warning")); }
    return Out;
}
