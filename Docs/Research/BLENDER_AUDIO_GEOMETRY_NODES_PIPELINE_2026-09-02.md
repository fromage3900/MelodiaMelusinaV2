# Blender Audio -> Geometry Nodes Pipeline - Research Report
**Date:** 2026-09-02 | **Task:** 5-8 concrete tools/repos/threads with URLs + Melodia Blender->UE integration
**Context:** Melodia Studio on Blender 5.2 (surreal_architecture_gen, 173 GN builders) -> UE 5.8 (PCG, Substrate, cymatic fabric, Sea Above)

---

## TL;DR Recommendation

**Adopt 2-track strategy:**
1. **Procedural (Blender 5.2 native)** - Sample Sound Frequencies node for live GN authoring
2. **Baked (UE-shippable)** - Sound Reaktor or Sound Nodes bake to keyframes/textures -> Alembic / image sequence / F-Curve JSON for UE

Do NOT rely on legacy bpy.ops.graph.sound_bake alone - mono, low-res, collapses stereo. New native node + SciPy addons replace it.

---

## 1. Blender 5.2 Native: Sample Sound Frequencies Node [PRIMARY]

**URLs:**
- Manual: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/sound/sample_sound_frequencies.html
- Release notes: https://developer.blender.org/docs/release_notes/5.2/geometry_nodes
- PR: https://projects.blender.org/blender/blender/pulls/156247
- Video: https://www.youtube.com/watch?v=h_Q91x_8dd4
- Cartesian Caramel demos: https://yelzkizi.org/cartesian-caramel-geometry-nodes-tests-sound-blender
- Summary: https://blendereverything.com/download.php?category=post&id=182

**What it does:** First-class GN nodes (Sample Sound, Sample Sound Frequencies). Drop audio into VSE -> GN picks strip directly -> outputs summed amplitude for a Hz range at a time (seconds). FFT Size 128-32768, windows Hann/Hamming/Blackman. Fully procedural, scrub-safe.

**Inputs:** Sound data-block, Time (seconds), All Channels / Channel, Low/High Hz, FFT Size, Window
**Output:** Amplitude (float) -> drive any GN field

**Maturity:** Ships in 5.2 LTS (Melodia already on 5.2). FFmpeg-backed; codec-dependent accuracy per PR.

**Melodia -> UE Integration:**
- Author builder GN_MEL_AudioReactive_Fabric_v01: 3 bands (bass 20-250Hz -> fabric amplitude, mids 250-2000Hz -> fold freq, highs 2-8kHz -> emissive). Expose Low/High as builder inputs.
- Bake for UE (GN is Blender-only): (a) Store Named Attribute (audio_bass) -> Alembic/USD with animated vertex attributes, or (b) bake bands to 1px-per-band image sequence -> Curve Atlas texture -> UE Material samples by time -> Niagara/PCG.
- Gotcha: Time is seconds not frames - wire Scene Time -> Seconds; All Channels for mono sum or split L/R for stereo cymatics.

---

## 2. Sound Nodes (negdo) - GN-Native Spectrum/Chromagram

**URLs:**
- GitHub (Lite, GPL-3.0, 41 stars): https://github.com/negdo/Sound_Nodes
- Addon page: https://blender-addons.org/sound-nodes/
- Market (full): https://superhivemarket.com/products/sound-nodes?ref=165

**What it does:** Analyzes mp3/wav/flac/ogg -> bakes loudness, avg frequency, beats, spectrogram, chromagram as keyframes -> auto-generates GN nodes (Sound Info, Spectrogram, Chromagram). Lite = limited bands; full = all + 3 demo files.

**Workflow:** GN Editor N-panel -> Load Audio -> Analyze Audio (can limit to scene range) -> nodes appear.

**Maturity:** Last push 2023-10-17, 7 open issues, compute.py / generate_nodes.py. Stable but Lite crippled.

**Melodia -> UE Integration:**
- Best for cymatic fabric: Spectrogram 32-64 bands -> radial displacement (Chladni plate). Chromagram (12-TET) -> wardrobe hue / palette (ties to music-as-key puzzle).
- Export: baked keyframes on hidden empties -> bpy.data.actions -> CSV/JSON -> UE DataTable / CurveFloat. Or bake GN to Alembic. Keep Blender band defs in sync with UE MetaSound FFT bins.
- Install: pip deps via Install Requirements button. Test Lite on 5.2 before buying.

---

## 3. Sound Reaktor (Inoshiro/Yatima) - SciPy Bake Replacement [MOST POWERFUL BAKE]

**URLs:**
- Thread: https://blenderartists.org/t/addon-sound-reaktor-animate-anything-in-blender-with-audio/1633918
- Market (Pro v2.6, 2026-07-23): https://superhivemarket.com/products/sound-reaktor
- Docs: https://superhivemarket.com/products/sound-reaktor/docs
- FAQ: https://superhivemarket.com/products/sound-reaktor/faq

**What it does:** Does NOT use native bake sound to F-Curves. Uses NumPy/SciPy/PyAV. 6 methods: FFT (smooth), Onset (beat), RMS (volume), Spectral Centroid (brightness), Spectral Flatness (tonality), Rolloff. 9 presets (kick/snare/vocals...), sensitivity + smoothing + noise filter. Two modes: Keyframes and Drivers (multi-property, auto-updates on audio swap). Pro v2.4.2+ adds GN + Shader node groups with 9 outputs. 50-200x faster than native.

**Modes:** Position/Rotation/Scale + Custom mode (if you can copy its data path, Sound Reaktor can animate it - any GN input, light, shader, modifier).

**Maturity:** Most active/polished; Pro paid (Lite retired 2026-07-21). v2.6 latest.

**Melodia -> UE Integration:**
- Primary bake path for UE: Drivers mode during authoring (fast), then Bake Drivers before export. Custom mode -> drive GN builder socket melodia_audio_reactive directly -> Alembic/texture bake. Solves UE incompatibility: Blender drivers do not export, baked keyframes do.
- Sea Above: FFT bands -> GN Set Position on fabric plane; RMS -> emissive pulse; Onset -> wardrobe beat triggers.
- Data bridge: bpy.ops.nla.bake -> per-frame floats to Content/Audio/BakedCurves/{track}_bass.json -> UE UMelodiaAudioReactiveSubsystem / MetaSound reads for music-as-key sync.

---

## 4. AudVis (example-sk/audvis) - Real-Time + MIDI + Scriptable

**URLs:**
- GitHub (GPL-2.0, 68 stars, 153 commits): https://github.com/example-sk/audvis
- Market: https://superhivemarket.com/products/audvis
- Docs: https://github.com/example-sk/audvis/blob/main/doc/sequence.md , https://github.com/example-sk/audvis/blob/main/doc/realtime.md
- Thread: https://blenderartists.org/t/audvis-audio-visualization-add-on/1183964

**What it does:** Two analyzers: Sequence Analyzer (VSE strips) and Realtime Analyzer (live mic). Also MIDI File + MIDI Realtime, Driver Values, Shape Modifier, Generate Armature, Scripting, Spectrogram, Video Capture. Most scriptable - Python API to spread drivers across many objects.

**Maturity:** 2.8+ maintained, 2021 origin, GPL-2. Good for live playtest.

**Melodia -> UE Integration:**
- Unique value: Only tool with MIDI in alongside spectrum - mirrors Melodia MIDI-driven Resonant World / piano puzzle + wardrobe.
- Live playtest: Realtime Analyzer -> drive Blender viewport GN while PIE via LiveLink (port 9876 / Melodia Studio Live Bridge). WIP preview, not shipping bake.
- Bake: Sequence Analyzer -> drivers -> Alembic. Scripting API can auto-generate 100s of GN instances (choir, fabric tiles) for L_KaleidoNave / L_FallenMoon PCG.

---

## 5. Animation Nodes - Sound Spectrum Node (Legacy Reference)

**URLs:**
- Docs: https://docs.animation-nodes.com/documentation/nodes/sound/sound_spectrum
- Release notes: https://docs.animation-nodes.com/release_notes/v1_6

**What it does:** AN Sound Spectrum node. Inputs: Sound, Frame, Attack/Release, Amplitude, Scene. Outputs: Spectrum (float list). Advanced: Reduction Max/Mean, Smoothing Samples, Kaiser Beta, Min Duration. Modes: Full / Single (Low/High 0-1) / Custom (pins).

**Maturity:** AN is 2.9-3.x era, not updated for 5.2. But cleanest prior art for exposing spectrum as list/field.

**Melodia -> UE Integration:**
- Reference only - do not build new AN graphs. Steal its API shape for GN builder design: expose Sound Spectrum as GN group returning Field of N bins (like AN Full mode). Use docs to spec builder inputs (Attack/Release -> simulation zone damping).
- Migration: AN Low/High 0-1 normalized -> Hz via map_range to Sample Sound Frequencies.

---

## 6. Simple Audio Visualizer (polyfjord) - Minimal Bake-to-Objects

**URLs:**
- GitHub (GPL-3.0, 22 stars): https://github.com/polyfjord/Simple-Audio-Visualizer
- Extensions: https://extensions.blender.org/add-ons/simple-audio-visualizer/
- Upstream: https://github.com/soerenmetje/Blender-Music-Visualisation-Python-Script

**What it does:** Minimal extension in Graph Editor sidebar. Create Visualizer (N cubes, auto-bakes spectrum via sound_bake to scale) and Visualize Selected Objects (distributes spectrum across selected objects alphabetically, per-axis Location/Rotation/Scale, Additive, Mirror, Multiplier).

**Maturity:** 4 commits, trivial codebase - onboarding, not hero fabric.

**Melodia -> UE Integration:**
- Rapid prototype: select kit props -> Visualize Selected -> instant audio-reactive blockout for art review without GN network. Useful for "make cathedral react to this stem" in 30 sec.
- Bake to F-Curves on objects -> FBX baked animation -> UE sequencer. Good for background crowd / set dressing.

---

## 7. GSoC 2026 Proposal - Wavelet Transient + Spectrum Field (Forward-Looking)

**URLs:**
- DevTalk: https://devtalk.blender.org/t/draft-gsoc-2026-geometry-nodes-wavelet-transient-detection-and-procedural-audio-analysis/44517
- Related: https://conference.blender.org/2024/presentations/1966/ (Jacob Collier lyric videos - 3000 images, glass sculpture, waveform data-buffer, particle emission)

**What it does (proposed):** Three deliverables: Audio Envelope Simulation Assets (attack/release), Wavelet Transient Node (sample-accurate beat via DWT), Spectrum Field Node (direct bin access as Fields for 512-bar visualizers without 512 Sample Sound nodes).

**Maturity:** Draft, 18 likes, not shipped. Author fixing instancing pipeline + collab with Jacques Lucke.

**Melodia -> UE Integration:**
- Watch & influence - missing piece for scalable cymatics. Today need 1 node per band. Spectrum Field = 1 node -> field on points. Melodia should track / early-test (cymatic fabric = ideal demo). Interim: wrap 32 Sample Sound nodes + Sample Index -> stored attribute.
- Wavelet transient = sample-accurate onset for rhythm_owner gate sync (tighter than windowed Onset).

---

## 8. MIDI-Keyframes + Community Threads (Bridge to Music-as-Key)

**URLs:**
- Blog: https://whoisryosuke.com/blog/2024/midi-powered-animations-in-blender/
- Repo: https://github.com/whoisryosuke/blender-midi-keyframes (mido + pip)
- Variant: https://whoisryosuke.com/blog/2024/midi-keyboard-in-blender + https://github.com/whoisryosuke/blender-gamepad
- Reddit Chladni: https://www.reddit.com/r/blenderhelp/comments/1jfb1y0/geometry_node_input_with_sound/
- Reddit Oscilloscope: https://www.reddit.com/r/blender/comments/100rmvw/use_audio_waveform_with_geometry_nodes_render/
- Reddit bake pain: https://www.reddit.com/r/blenderhelp/comments/17lihmv/weird_properties_regarding_the_bake_sound_to/
- Python bake: https://devhide.com/bake-sound-to-f-curve-on-geometry-node-via-python-api-78184494

**What they do:** MIDI file -> note-on/off -> keyframes on assigned objects/bones; raw waveform -> GN via texture/attribute baking; canonical bpy.ops.graph.sound_bake(filepath, low, high) automation.

**Melodia -> UE Integration:**
- MIDI path: wardrobe bones/props assigned to MIDI notes -> GN + baked skeletal animation -> UE reads same .mid for gameplay (keeps Blender previz and UE runtime in sync).
- Raw waveform: waveform baked to image texture (X=time, Y=amplitude) -> GN Sample Texture -> displace (for string/konchu vibration; spectrum FFT for water/PCG).
- Automation template: loop over stems via sound_bake -> one JSON per stem for batch baking.

---

## How to Wire into Melodia Blender->UE (Concrete)

1. Builder GN_MEL_AudioReactive_Fabric_v01: inputs Sound, BandCount (8/16/32), Time (frame/fps). Internals: per-band Sample Sound Frequencies or Sound Reaktor GN group -> Store Named Attribute (audio_band_00 ...) + Set Position weighted by band. Radial variant: Index/Count -> Angle (center=bass, edge=highs).

2. Baking (required for UE):
   - A: Alembic cache Saved/Baked/AudioFabric_{track}_{fps}fps.abc (animated positions + attributes) -> UE GeometryCache for Sea Above
   - B: Image sequence via Compositor File Output or numpy->EXR -> Curve Atlas -> UE MF_AudioBand_Sample (UV=time)
   - C: bpy.data.actions fcurves -> Content/Python/BakedAudio/{track}.json (frame -> float[32]) -> UE DataTable -> UMelodiaAudioReactiveSubsystem -> Niagara/PCG/MPC

3. UE side (no competing authority): UMelodiaNarrativeSubsystem owns Quill; add UMelodiaAudioReactiveSubsystem (presentation-only) that reads baked curves OR live AudioAnalyzer (MetaSound) -> pumps to PCG params, MPC_AudioBands, Niagara emission, wardrobe preview (DCC only).

4. Validation: commit .blend + .abc/.exr/.json + Saved/Echo/audio_reactive_manifest.json - echo pipeline expects ledger rows.

**Recommended pilot:** Sound Reaktor (drivers) + Blender 5.2 Sample Sound in same blend, bake to Alembic for Sea Above hero + JSON for gameplay triggers. AudVis only if MIDI needed. Simple Audio Visualizer for 30-sec blockouts.

---

## Sources Checked

Reddit r/blender, r/geometrynodes, r/blenderhelp; GitHub (negdo/Sound_Nodes, example-sk/audvis, polyfjord/Simple-Audio-Visualizer, whoisryosuke/blender-midi-keyframes, animation-nodes); Blender Manual / DevTalk / conference.blender.org; Superhive/Blender Market; Blender Artists; YouTube (Polyfjord, Cartesian Caramel).

*Prepared for C:\EnvironmentPortfolio\BS_GodFile - Docs/Research/*
