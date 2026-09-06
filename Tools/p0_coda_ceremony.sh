#!/bin/bash
# P0 Coda Ceremony — run AFTER the golden run passes and Melusina records the row.
# Usage: bash Tools/p0_coda_ceremony.sh <certified-commit-sha>
# What it does: stanza tag (annotated, the monument) + time-capsule bundle (the pair).
set -eu
cd "$(dirname "$0")/.."
SHA=${1:-$(git rev-parse origin/main)}
STANZA="First Dream keeps its own time now: ten gates, ten true rows, a thousand
rivers joined to one sea. Played by hand, saved whole, survived the dark
of a restart — as bard, as bride of no system, as Melusina.
-- feather pressed, Sir Melodious"
git tag -a "p0/first-dream/coda" "$SHA" -m "$STANZA"
git -c http.version=HTTP/1.1 push origin "p0/first-dream/coda"
mkdir -p ../git_bundles_archive
git bundle create ../git_bundles_archive/p0_coda_$(date +%Y-%m-%d).bundle main
git bundle verify ../git_bundles_archive/p0_coda_$(date +%Y-%m-%d).bundle
echo "---"
echo "Two capsules now bracket the age: pre_unify_ALLREFS.bundle (the day the"
echo "rivers joined) and this one (the day the dream woke). Tag holds the stanza."
git show "p0/first-dream/coda" --no-patch
