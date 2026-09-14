# 03_tide_listening — The bell beneath the tide

A four-beat optional conversation: discover the submerged bell, listen, choose an answer,
return to the shore. Melusina learns that listening is part of making music.

Run `python Tools/scaffold_chapter.py NN_slug` to copy this folder. The script checks every
emitted gated ID against the real `DA_MelodiaIntegrationConfig` before writing any files.
It refuses existing chapter folders. New chapter intents and persistent Quill variables
use the folder slug; the social stat remains the existing runtime identity.

Validate with `python -m unittest Content.Python.Tests.test_qsc_allowlist_contract`.
Import `quill/TideListening.qsc` into a uniquely named Quill asset, assign the existing Quill
presentation widgets, then add one interaction fixture to `MelodiaIntegrationMap`.
Test both choices, revisit, save/reload, and revisit again with strict allowlists enabled.
The scaffold creates source, not imported assets or runtime proof.
