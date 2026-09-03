// Fixture header for VerifySymbolsComposition + FindExampleUsagePagination.
// NOT compiled into any module — read as data by the indexer during tests.
//
// UCppErgoUsage is indexed as a class symbol row. CallMe is a class-body method
// declaration (Step-0: NOT indexed as a symbols row) — verify_symbols must report
// it exists:true via the owning class row + source_fts declaration hit, NOT via
// symbols-table presence.
//
// The class is declared in Epic's allman style (opening brace on the line after
// the `class` declaration). Phase-B of MonolithCppParser's class extractor looks
// ahead for the brace, so this indexes as a class row exactly like a same-line
// brace would — this fixture is the live regression case for that fix.
#pragma once

class UCppErgoUsage
{
public:
	void Run();

	void CallMe(int32 Value);
};
