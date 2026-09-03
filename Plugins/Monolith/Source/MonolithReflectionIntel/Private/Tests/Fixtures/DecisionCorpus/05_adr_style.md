# Project Architecture Decisions

This file follows the ADR (Architectural Decision Record) convention.

## ADR-001 Adopt SQLite WAL=DELETE mode

WAL is unsupported with read-only opens on Windows — silent failure.
Rationale: see UE57Gotchas.md SQLite section.

## ADR-002 Editor-only namespace registration

Decision recorded during Phase 1 of the Reflection Intelligence plan.
Architectural Decision: indexers run in the editor process only.

Evidence: commandlet mode short-circuits in UMonolithSourceSubsystem.
