# Rokoko CharacterRef

Store the exported `SK_MocapSource.fbx` here for the Rokoko Studio character profile.

1. UE: open `/Game/Melodia/Mocap/Source/SK_MocapSource` → Asset Actions → Export.
2. Save as `SK_MocapSource.fbx` in this folder.
3. Rokoko Studio → Characters → import that FBX → assign to your actor.

Takes exported with a mismatched profile still import, but retarget quality will be wrong — then build `RTG_Rokoko_to_Melusina` instead of reusing `RTG_Mocap_to_Melusina`.

See `Docs/ROKOKO_MELUSINA_MOCAP.md`.
