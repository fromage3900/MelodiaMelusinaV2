#!/usr/bin/env bash
# website_pass_variants_20260920.sh — website renders for the silhouette presets.
# Per variant (star_citadel, lissajous_veil): 4 skies x 3 still views + 2 loops
# (turntable, sweep on editorial_dark, 48f @ 720x900 for fast first delivery).
# Variant objects are built runtime-only (variant_prep.py); the saved blend is
# never modified. Flower stills/loops are never touched (variant-prefixed names).
# Run: bash Saved/Audit/website_pass_variants_20260920.sh
set -u
cd "P:/MelodiaMelusinaV2-Laptop"
BL="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
BLEND="${BLEND:-P:/MelodiaMelusinaV2-Laptop/Saved/MelusinasHouse/FlowerBrooch.blend}"
LOG="Saved/Audit/website_pass_variants_20260920.log"
RAW="Saved/Website/Brooch/stills_raw"
RAWV="Saved/Website/Brooch/stills_raw_variants"
FR="Saved/Website/Brooch/frames"
: > "$LOG"
say() { echo "$@"; echo "$@" >> "$LOG"; }
SILS="${SILS:-star_citadel lissajous_veil}"
SAMPLES="${SAMPLES:-64}"
LFRAMES="${LFRAMES:-48}"
LRES="${LRES:-720x900}"
LSAMPLES="${LSAMPLES:-48}"
say "=== variant pass start $(date) sils=$SILS stills_s=$SAMPLES loops=${LFRAMES}f@${LRES}/${LSAMPLES}s"

for SIL in $SILS; do
  # ---- stills
  RAWD="$RAWV/$SIL"; mkdir -p "$RAWD"
  for V in editorial_dark forte radiant tide; do
    say "--- stills $SIL $V"
    MK="$RAWD/.stamp_${V}"; touch "$MK"
    if "$BL" -b "$BLEND" --python-exit-code 1 --python Tools/brooch_website/variant_prep.py \
         --python Tools/brooch_pres_rig.py --python Tools/brooch_pres_shot.py \
         -- --sky "$V" --samples "$SAMPLES" --silhouette "$SIL" >> "$LOG" 2>&1; then
      say "stills $SIL $V OK"
    else
      say "stills $SIL $V FAIL"
    fi
    find Saved/Audit -maxdepth 1 -name 'sky_*.png' -newer "$MK" -exec mv {} "$RAWD"/ \;
    rm -f "$MK"
  done
  if python Tools/brooch_website/variant_convert.py "$RAWD" "Website/Brooch/stills_variants" "sil_${SIL}" >> "$LOG" 2>&1; then
    say "convert $SIL OK"
  else
    say "convert $SIL FAIL"
  fi

  # ---- loops (marker-based rename: only frames written by THIS run are retagged)
  for L in turntable sweep; do
    TAG="sil_${SIL}_${L}_editorial_dark"
    say "--- loop $TAG"
    MK="$FR/.stamp_loop"; mkdir -p "$FR"; touch "$MK"
    if "$BL" -b "$BLEND" --python-exit-code 1 --python Tools/brooch_website/variant_prep.py \
         --python Tools/brooch_pres_rig.py --python Tools/brooch_web_anim.py \
         -- --loop "$L" --sky editorial_dark --frames "$LFRAMES" --res "$LRES" --samples "$LSAMPLES" \
         --silhouette "$SIL" >> "$LOG" 2>&1; then
      say "loop $TAG OK"
    else
      say "loop $TAG FAIL"
      rm -f "$MK"
      continue
    fi
    for F in $(find "$FR" -maxdepth 1 -name "${L}_editorial_dark_*.png" -newer "$MK"); do
      B="$(basename "$F")"
      mv "$F" "$FR/${TAG}_${B#${L}_editorial_dark_}"
    done
    rm -f "$MK"
    if python Saved/Audit/frames_check.py "$FR" "$TAG" $((LFRAMES - 1)) "$L" >> "$LOG" 2>&1; then
      say "check $TAG OK"
    else
      say "check $TAG FAIL"
    fi
  done
done

if python Tools/brooch_website/variant_encode.py >> "$LOG" 2>&1; then say "encode OK"; else say "encode FAIL"; fi
say "=== variant pass done $(date)"
