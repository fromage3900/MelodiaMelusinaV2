#pragma once

#include "CoreMinimal.h"

/**
 * Strips UE-specific macros from C++ source text, replacing with spaces.
 * Preserves newlines at their original character positions so line numbers stay correct.
 *
 * Three categories of macros are handled:
 * 1. Class-level macros with nested parentheses:
 *       UCLASS(...), USTRUCT(...), UENUM(...), UINTERFACE(...)
 *    Uses balanced-parenthesis scanning (regex can't handle nesting).
 *
 * 2. API export macros:
 *       ENGINE_API, CORE_API, COREUOBJECT_API, *_API
 *    Pattern: [A-Z][A-Z0-9]*_API as whole words.
 *
 * 3. GENERATED_BODY variants:
 *       GENERATED_BODY(), GENERATED_UCLASS_BODY(), GENERATED_USTRUCT_BODY()
 */
namespace MonolithUEPreprocessor
{
    /**
     * Replace UE macros with same-length spaces. Output.Len() == Input.Len().
     * Every \n stays at its original character offset.
     */
    FString PreprocessSource(const FString& Source);
}
