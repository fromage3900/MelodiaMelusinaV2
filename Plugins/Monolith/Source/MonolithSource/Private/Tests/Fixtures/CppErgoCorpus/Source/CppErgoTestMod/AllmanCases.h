// Fixture for Monolith.Source.CppErgonomics.AllmanClassIndexing.
// NOT compiled into any module — read as data by the indexer during the test.
// Macro-free (no UCLASS/USTRUCT/UINTERFACE/UPROPERTY/GENERATED_BODY), so UHT
// ignores it entirely and it stays a plain `.h`.
//
// Every declaration below exercises one assertion in the AllmanClassIndexing
// test (Phase-B allman lookahead + template-param guard + forward-decl drop).
#pragma once

// 1) Plain allman class — opening brace on the NEXT line. Members inside the body
//    must be extracted (Member, GetMember).
//
//    REALLOCATION REGRESSION GUARD (use-after-free): ExtractMembers Adds every member
//    to Result.Symbols. With many members, that array reallocates MID-extraction; the
//    old buffer is freed. If the ParentClass argument were a reference into that buffer
//    (e.g. Result.Symbols.Last().Name) it would dangle, and the next member's
//    `Sym.ParentClass = ParentClass` would read freed memory -> AV. We declare 14
//    members below (TArray growth from a small size reallocates several times across
//    14 Adds) so the test deterministically crosses a reallocation boundary, and assert
//    EVERY member is extracted with the correct FAllmanPlain ParentClass.
class FAllmanPlain
{
public:
	int32 Member;

	int32 GetMember() const;

	int32 Member00;
	int32 Member01;
	int32 Member02;
	int32 Member03;
	int32 Member04;
	int32 Member05;
	int32 Member06;
	int32 Member07;
	int32 Member08;
	int32 Member09;
	int32 Member10;
	int32 Member11;
};

// 2) Allman class with a SAME-LINE inheritance list. Base class FAllmanPlain must
//    be recorded; the brace still opens the next line.
class FAllmanDerived : public FAllmanPlain
{
public:
	void DerivedMethod();
};

// 3) Same-line-brace one-liner (today's K&R / "87-style" form) — must still index
//    with no regression. The brace opens the body on the declaration line.
struct FOneLiner {
	int32 X;
};

// 4) Forward declaration — NO definition follows, so NO symbol row may be produced.
class FAllmanFwd;

// 5) Multi-line template parameter list. `class T` sits alone on a line with the
//    real class's brace within the lookahead window — the template-param guard must
//    suppress a bogus `T` symbol while STILL indexing FAllmanTpl.
template<
	class T
>
class FAllmanTpl
{
public:
	T Stored;
};

// 6) Two ADJACENT one-line structs — both must index (the cursor-advance guard:
//    the brace lookahead for FStructA must not skip FStructB).
struct FStructA {};
struct FStructB {};

// 7) UNTERMINATED allman body at EOF — the opening brace has NO matching `}` before
//    end-of-file. FindClosingBrace returns the line COUNT (sentinel), which previously
//    drove ExtractMembers' StartIdx past the array -> access violation on the indexer
//    thread. The parser must NOT crash; no members are extracted for this class. This
//    MUST be the last declaration in the file so the brace genuinely runs to EOF.
class FAllmanUnterminated
{
public:
	int32 NeverReached;
