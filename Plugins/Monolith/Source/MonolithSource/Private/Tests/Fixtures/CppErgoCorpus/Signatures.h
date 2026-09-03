// Fixture for Monolith.Source.CppErgonomics.SignatureCompaction.
// Read directly via FFileHelper::LoadFileToStringArray; CompactDeclaration is
// applied at known line offsets. Line numbers are load-bearing for the test:
//   Line 8  : multi-line declaration spanning to the closing paren on line 10
//   Line 13 : inline-defined method whose body must NOT leak into the signature
//   Line 16 : a macro-style declaration with a trailing `\` continuation
#pragma once

float MultiLineDecl(
	int32 First,
	const FString& Second) const;

FTransform GetTransform() const { return Super::GetTransform(); }

#define INLINE_THING(x) \
	void Thing(int32 x) { DoThing(x); }
