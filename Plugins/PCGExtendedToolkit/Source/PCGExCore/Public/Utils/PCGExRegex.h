// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Internationalization/Regex.h"

namespace PCGExRegex
{
	/** Lightweight wrapper around FRegexPattern. Compile once in Init(), call Test() per point. */
	struct FPattern
	{
		FPattern()
		{
		}

		~FPattern()
		{
		}

		/**
		 * Stores the pattern for matching. NOTE: UE's FRegexPattern exposes no way to detect an
		 * invalid pattern (ICU compiles lazily and only logs internally), so this cannot report
		 * syntax errors -- a malformed pattern simply matches nothing at Test() time.
		 */
		void Compile(const FString& InPattern)
		{
			CompiledPattern = MakeShared<FRegexPattern>(InPattern);
		}

		/** Tests whether the subject string matches the compiled pattern. */
		bool Test(const FString& Subject) const
		{
			check(CompiledPattern.IsValid());
			FRegexMatcher Matcher(*CompiledPattern, Subject);
			return Matcher.FindNext();
		}

	private:
		TSharedPtr<FRegexPattern> CompiledPattern;
	};
}
