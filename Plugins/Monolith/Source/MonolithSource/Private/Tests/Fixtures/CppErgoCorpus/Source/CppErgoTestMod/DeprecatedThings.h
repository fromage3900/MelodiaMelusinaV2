// Fixture for Monolith.Source.CppErgonomics.DeprecationIndexExtraction.
// NOT compiled into any module — read as data by the indexer during the test.
//
// Two class-body methods carry UE_DEPRECATED macros. Class-body method
// declarations are NOT indexed as `symbols` rows (Step-0 finding), so the
// extractor must parse the symbol NAME from the declaration text following the
// macro and store symbol_id = NULL.
#pragma once

class UDeprecatedThings
{
public:
	UE_DEPRECATED(5.4, "Use Bar instead")
	void Foo();

	UE_DEPRECATED_FORGAME(5.5, "Baz is gone")
	int32 Baz(float Param) const;

	// Not deprecated — must NOT produce a row.
	void StillFine();
};
