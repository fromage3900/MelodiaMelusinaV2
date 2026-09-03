# Sample Spec 02

Two cascading decisions that supersede one another, for the chain test.

## Replace FindFilesRecursive with IterateDirectoryRecursively

Because the FindFilesRecursive 6th-parameter bClearFileNames defaults
to true (evidence: caught in Phase 1 review), we standardise on the
visitor pattern instead.

Supersedes: 01_decision_with_rationale.md

## Adopt FRegexMatcher for header parsing

Because the parser was previously hand-rolled and brittle, we switch
to FRegexPattern + FRegexMatcher. Rationale captured during the
decision-indexer extraction sweep.

Supersedes: 02_decision_with_supersedes.md#replace-findfilesrecursive-with-iteratedirectoryrecursively
