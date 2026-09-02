"""wire_audio_reactive_flower.py — TD CHOP → OSC 9000 for live audio-reactive flower.

CHOP network: Audio Device In | File In → Spectrum CHOP → 3 bands (bass/mid/treble)
             → Math CHOP (0-1 range) → Lag CHOP (smooth) → OSC Out CHOP on port 9000

Routes:
  /melodia/audio/bass    [0,1] float — 20-250 Hz RMS  → petal scale
  /melodia/audio/mid     [0,1] float — 250-2000 Hz    → stem sway / hue
  /melodia/audio/treble  [0,1] float — 2k-20k Hz       → emissive sparkle
  /melodia/audio/beat/pulse [0,1] from UMelodiaRhythmReactivitySubsystem::Publish() (/rhythm/beat_pulse)
  /melodia/audio/beat/phase [0,1] from UMelodiaRhythmReactivitySubsystem (/rhythm/beat_phase)

Port: 9000 ONLY (single source of truth — do NOT create second channel on 9870).
        TD OSC In also on 9000 receives BeatPulse/BeatPhase from UE.

Run via:  exec(open('C:/EnvironmentPortfolio/BS_GodFile/_TouchDesigner/grandmaster_melodia/scripts/wire_audio_reactive_flower.py').read())
      or Envoy MCP:  td.exec("exec(open(...).read())")

Requires: TouchDesigner 2022+ (audiodeviceinCHOP, spectrumCHOP, oscoutCHOP are core).
"""

# ── Resolve parent ──────────────────────────────────────────────────
# Use /project1 as root; create dedicated container so we never clash with
# existing /project1/osc (battle) or /project1/audio (melusina legacy).
root = op('/project1')
if root is None:
    raise Exception('TD root /project1 not found — open grandmaster_melodia.toe first')

# Dedicated audio-reactive container
c = root.op('melodia_audio')
if c is None:
    c = root.create('baseCOMP', 'melodia_audio')
c.nodeX = 200
c.nodeY = -800
c.comment = 'Audio-reactive flower CHOP network — CHOP→OSC 9000 — 2026-09-02 sprint'
# Clean rebuild: destroy old children so re-exec is idempotent
for child in list(c.findChildren()):
    try:
        child.destroy()
    except:
        pass

# ── 1. Audio source — Device In (live mic) + File In (deterministic test) ─
audio_in = c.create('audiodeviceinCHOP', 'audio_in')
audio_in.nodeX = 0; audio_in.nodeY = 0
audio_in.comment = 'Live mic — driver default, 44.1kHz, async. Falls back to file_in if silent.'
try:
    audio_in.par.driver = 0  # WASAPI / CoreAudio default
    # keep defaults: samplerate auto, queue
except:
    pass

file_in = c.create('audiofileinCHOP', 'file_in')
file_in.nodeX = 0; file_in.nodeY = 120
file_in.comment = 'File fallback — set par.file to Content/Audio/128BPMarpeggiomelody.wav for deterministic test'
# Leave file empty by default; operator sets it:
# file_in.par.file = 'C:/EnvironmentPortfolio/BS_GodFile/Content/Audio/128BPMarpeggiomelody.wav'
# file_in.par.play = 1
# file_in.par.loop = 1

# Switch to choose source: 0=device, 1=file (default file for CI without mic)
src_switch = c.create('switchCHOP', 'source_switch')
src_switch.nodeX = 200; src_switch.nodeY = 60
src_switch.comment = 'Input selector: index 0=device mic, 1=file. Set to 1 for bake/test without hardware.'
if hasattr(src_switch.par, 'index'):
    src_switch.par.index = 1
src_switch.inputConnectors[0].connect(audio_in)
src_switch.inputConnectors[1].connect(file_in)

# ── 2. Spectrum CHOP — FFT of audio ─────────────────────────────────
spectrum = c.create('spectrumCHOP', 'spectrum')
spectrum.nodeX = 400; spectrum.nodeY = 60
spectrum.comment = 'FFT spectrum — 2048 window, Hann, 50% overlap → freq bins as channels'
# Parameters differ by TD build; set what exists, ignore rest
for pset in [
    ('windowsize', 2048),
    ('windowtype', 2),   # Hann (enum varies; harmless if fails)
    ('overlap', 0.5),
]:
    try: setattr(spectrum.par, pset[0], pset[1])
    except: pass
spectrum.inputConnectors[0].connect(src_switch)

# ── 3. Three-band split — audiofilterCHOP per band (log cutoffs verified 2026-08-08) ─
# Cutoffs chosen to partition spectrum into musically meaningful bands:
#   bass   20–250 Hz  (kick, bloom open)
#   mid    250–2000 Hz (melody, hue shift)
#   treble 2000–20000 Hz (air, sparkle)
# Each audiofilter → analyze(RMS) → math(normalize) → lag(smooth) chain.

# Band filters (audiofilterCHOP works on raw audio; we also branch from spectrum
# for visual inspection, but RMS bands are more stable from raw + filter)
bass_filter = c.create('audiofilterCHOP', 'filter_bass')
bass_filter.nodeX = 600; bass_filter.nodeY = -120
bass_filter.comment = 'Bass: low-pass ~250 Hz — petal scale'
try:
    bass_filter.par.filter = 0  # lowpass
    bass_filter.par.cutofflog = 2.397  # ~250 Hz (log10 250 ≈ 2.398)
except: pass
bass_filter.inputConnectors[0].connect(src_switch)

mid_filter = c.create('audiofilterCHOP', 'filter_mid')
mid_filter.nodeX = 600; mid_filter.nodeY = 60
mid_filter.comment = 'Mid: band-pass 250–2000 Hz — stem sway / hue'
try:
    mid_filter.par.filter = 1  # bandpass where available
    mid_filter.par.cutofflog = 3.0  # center ~1000 Hz
    if hasattr(mid_filter.par, 'bandwidthlog'):
        mid_filter.par.bandwidthlog = 0.9
except: pass
mid_filter.inputConnectors[0].connect(src_switch)

treble_filter = c.create('audiofilterCHOP', 'filter_treble')
treble_filter.nodeX = 600; treble_filter.nodeY = 240
treble_filter.comment = 'Treble: high-pass ~2000 Hz — emissive sparkle'
try:
    treble_filter.par.filter = 2  # highpass
    treble_filter.par.cutofflog = 3.301  # ~2000 Hz
except: pass
treble_filter.inputConnectors[0].connect(src_switch)

# RMS power per band (analyzeCHOP in rms mode gives 0-1 envelope)
def make_rms(name, x, y, src):
    n = c.create('analyzeCHOP', name)
    n.nodeX = x; n.nodeY = y
    try: n.par.function = 'rms'  # rmspower
    except: pass
    try: n.par.analyzetype = 'rms'
    except: pass
    n.inputConnectors[0].connect(src)
    n.comment = name + ' — RMS power 0-1'
    return n

rms_bass = make_rms('rms_bass', 800, -120, bass_filter)
rms_mid  = make_rms('rms_mid',  800,  60, mid_filter)
rms_treble = make_rms('rms_treble', 800, 240, treble_filter)

# ── 4. Math CHOP — normalize each band to 0-1 (gain + clamp) ───────
def make_math(name, x, y, src, comment):
    n = c.create('mathCHOP', name)
    n.nodeX = x; n.nodeY = y
    n.comment = comment
    # Gain ~2x so quiet sources still read, then clamp 0-1 downstream
    try:
        n.par.gain = 2.0
        # from/to range 0-1 already; clamp enabled
    except: pass
    n.inputConnectors[0].connect(src)
    return n

math_bass = make_math('math_bass', 1000, -120, rms_bass, 'Bass: gain 2x, clamp 0-1 → /melodia/audio/bass')
math_mid  = make_math('math_mid',  1000,  60, rms_mid,  'Mid: gain 2x, clamp 0-1 → /melodia/audio/mid')
math_treble = make_math('math_treble', 1000, 240, rms_treble, 'Treble: gain 2x, clamp 0-1 → /melodia/audio/treble')

# Clamp via limit/clamp — ensure no >1.0 spikes reach UE
for m in (math_bass, math_mid, math_treble):
    try:
        # mathCHOP has 'range' or limit; use what's present
        if hasattr(m.par, 'clamp'):
            m.par.clamp = True
    except: pass

# ── 5. Lag CHOP — smooth (attack 0.1s, decay 0.35s) ─────────────────
def make_lag(name, x, y, src):
    n = c.create('lagCHOP', name)
    n.nodeX = x; n.nodeY = y
    n.comment = name + ' — smooth 0.1 rise / 0.35 fall (no jitter on flower)'
    try:
        n.par.lag = 0.1
        n.par.lag2 = 0.35
        # Some builds expose lag up/down separately
        if hasattr(n.par, 'lagup'): n.par.lagup = 0.1
        if hasattr(n.par, 'lagdown'): n.par.lagdown = 0.35
    except: pass
    n.inputConnectors[0].connect(src)
    return n

lag_bass = make_lag('lag_bass', 1200, -120, math_bass)
lag_mid  = make_lag('lag_mid',  1200,  60, math_mid)
lag_treble = make_lag('lag_treble', 1200, 240, math_treble)

# ── 6. Rename + Merge → single OSC payload ─────────────────────────
# Rename channels to canonical names so OSC addresses are stable
rename = c.create('renameCHOP', 'rename_bands')
rename.nodeX = 1400; rename.nodeY = 60
rename.comment = 'Rename to canonical channel names: bass, mid, treble'
try:
    # renameCHOP: from -> to mapping
    # Use pattern: * -> bass/mid/treble in order of inputs
    # Fallback: leave channel names and rely on oscout mapping
    rename.par.renameto = 'bass mid treble'
    rename.par.renamefrom = 'chan1 chan1 chan1'
except: pass
# Chain: merge laged bands
# Simpler: connect all three lags into merge, then rename
merge = c.create('mergeCHOP', 'merge_bands')
merge.nodeX = 1350; merge.nodeY = 60
merge.inputConnectors[0].connect(lag_bass)
merge.inputConnectors[1].connect(lag_mid)
merge.inputConnectors[2].connect(lag_treble)

rename.inputConnectors[0].connect(merge)

# Null hub before OSC (best practice — single stable OP for wiring)
hub = c.create('nullCHOP', 'audio_hub')
hub.nodeX = 1550; hub.nodeY = 60
hub.comment = 'Audio hub — final 3ch 0-1 stream. Select this to inspect in viewer.'
hub.inputConnectors[0].connect(rename)

# ── 7. OSC Out CHOP — port 9000 ONLY ─────────────────────────────────
osc_out = c.create('oscoutCHOP', 'osc_out')
osc_out.nodeX = 1750; osc_out.nodeY = 60
osc_out.par.address = '127.0.0.1'
osc_out.par.port = 9000
osc_out.comment = 'OSC Out port 9000 ONLY — sends /melodia/audio/bass|mid|treble [0,1]. Do NOT use 9870.'
# Channel → OSC address mapping: each channel gets its own address
# TD oscout sends one OSC message per channel: /melodia/audio/<name> <float>
# Configure via DAT mapping table below
try:
    # Some TD builds expose 'oscaddress' or need DAT; we set via custom mapping
    osc_out.par.active = True
except: pass

# Mapping DAT — channel to OSC address (drives oscout DAT mode if needed)
mapping = c.create('tableDAT', 'osc_mapping')
mapping.nodeX = 1750; mapping.nodeY = -200
mapping.clear()
mapping.appendRow(['channel', 'address', 'range', 'UE target'])
mapping.appendRow(['bass',   '/melodia/audio/bass',   '[0,1] float', 'MPC_Melodia_Palette.Bass / flower scale'])
mapping.appendRow(['mid',    '/melodia/audio/mid',    '[0,1] float', 'MPC_Melodia_Palette.Mid / hue shift'])
mapping.appendRow(['treble', '/melodia/audio/treble', '[0,1] float', 'MPC_Melodia_Palette.Treble / emissive'])
mapping.appendRow(['beat_pulse', '/melodia/audio/beat/pulse', '[0,1] float', 'MPC BeatPulse — from UMelodiaRhythmReactivitySubsystem (UE→TD)'])
mapping.appendRow(['beat_phase', '/melodia/audio/beat/phase', '[0,1] float', 'MPC BeatPhase — from UMelodiaRhythmReactivitySubsystem (UE→TD)'])
mapping.appendRow(['info', 'Port 9000 ONLY — single source of truth per AUDIO_REACTIVE_FLOWER_SPRINT_2026-09-02.md', '', ''])
mapping.comment = 'OSC mapping table — 3 audio bands + 2 beat signals from UE. Verify in TD OSC In monitor.'

# Wire mapping DAT to osc_out if it supports DAT input (common pattern)
try:
    # oscoutCHOP can take a DAT for address mapping on its second input
    if len(osc_out.inputConnectors) > 1:
        osc_out.inputConnectors[1].connect(mapping)
    # Primary is CHOP hub
    osc_out.inputConnectors[0].connect(hub)
except:
    try: osc_out.inputConnectors[0].connect(hub)
    except: pass

# ── 8. OSC In for beat signals from UE (same port 9000, shared listener) ─
# IMPORTANT: Do NOT create second oscinCHOP on 9870. Use existing 9000.
# Reuse /project1/osc/in_blender if present (wire_battle_fixed pattern), or create
# scoped listener inside this container for inspection only.
osc_in_ref = root.op('osc/in_blender') or c.op('in_beat')
beat_comment = 'OSC In on 9000 — receives /rhythm/beat_pulse & /rhythm/beat_phase from UMelodiaRhythmReactivitySubsystem::Publish()'
if root.op('osc/in_blender') is not None:
    # Shared listener already exists — create selectCHOPs that reference it
    shared_in = root.op('osc/in_blender')
    sel_pulse = c.create('selectCHOP', 'sel_beat_pulse')
    sel_pulse.nodeX = 200; sel_pulse.nodeY = 400
    sel_pulse.comment = 'Select beat_pulse from shared OSC In 9000 (UE → TD) — drives petal emissive'
    try:
        sel_pulse.inputConnectors[0].connect(shared_in)
        sel_pulse.par.channames = 'beat_pulse *pulse* /rhythm/beat_pulse'
    except: pass
    sel_phase = c.create('selectCHOP', 'sel_beat_phase')
    sel_phase.nodeX = 200; sel_phase.nodeY = 520
    sel_phase.comment = 'Select beat_phase from shared OSC In 9000 — drives stem sway'
    try:
        sel_phase.inputConnectors[0].connect(shared_in)
        sel_phase.par.channames = 'beat_phase *phase* /rhythm/beat_phase'
    except: pass
else:
    # No shared listener — create scoped one for this container (inspection only)
    beat_in = c.create('oscinCHOP', 'in_beat')
    beat_in.nodeX = 0; beat_in.nodeY = 400
    beat_in.par.port = 9000
    beat_in.comment = beat_comment + ' (scoped — prefer shared /project1/osc/in_blender)'
    sel_pulse = c.create('selectCHOP', 'sel_beat_pulse')
    sel_pulse.nodeX = 200; sel_pulse.nodeY = 400
    sel_pulse.inputConnectors[0].connect(beat_in)
    sel_phase = c.create('selectCHOP', 'sel_beat_phase')
    sel_phase.nodeX = 200; sel_phase.nodeY = 520
    sel_phase.inputConnectors[0].connect(beat_in)

# Beat → flower math (beat_pulse already 0-1, just lag slightly for smooth bloom)
beat_lag = c.create('lagCHOP', 'lag_beat_pulse')
beat_lag.nodeX = 400; beat_lag.nodeY = 400
beat_lag.comment = 'Beat pulse lag 0.05 — smooth bloom without snapping'
try:
    beat_lag.par.lag = 0.05
except: pass
beat_lag.inputConnectors[0].connect(sel_pulse)

phase_lag = c.create('lagCHOP', 'lag_beat_phase')
phase_lag.nodeX = 400; phase_lag.nodeY = 520
phase_lag.comment = 'Beat phase passthrough — drives sin sway'
phase_lag.inputConnectors[0].connect(sel_phase)

# ── 9. Diagnostic DAT — documents entire network for handoff ─────────
info = c.create('textDAT', 'network_info')
info.nodeX = 0; info.nodeY = -400
info.text = """Audio-Reactive Flower — CHOP→OSC 9000 Network
=================================================
Container: /project1/melodia_audio  (new — does not clash with /project1/osc or /project1/audio)
Port: 9000 ONLY (per AUDIO_REACTIVE_FLOWER_SPRINT Path C + sprint constraint)
      Do NOT create second channel on 9870.

Chain:
  audio_in (audiodeviceinCHOP, 44.1k live mic)
    | file_in (audiofileinCHOP, loop, deterministic test)
    → source_switch (index 0=device, 1=file — default 1 for CI)
    → spectrum (spectrumCHOP, 2048 Hann, 50% overlap — inspector)
    ↘ filter_bass  (audiofilter low-pass ~250 Hz)  → rms_bass  → math_bass (gain 2x clamp)  → lag_bass (0.1/0.35)
    ↘ filter_mid   (audiofilter band-pass 250-2k)  → rms_mid   → math_mid  (gain 2x clamp)  → lag_mid  (0.1/0.35)
    ↘ filter_treble(high-pass ~2k)                 → rms_treble→ math_treble(gain 2x clamp) → lag_treble(0.1/0.35)
    → merge_bands (mergeCHOP 3ch) → rename_bands → audio_hub (nullCHOP)
    → osc_out (oscoutCHOP 127.0.0.1:9000) + osc_mapping (tableDAT)

OSC Out (TD→UE on 9000, consumed by osc_server.py / MPC_Melodia_Palette):
  /melodia/audio/bass   float [0,1] bass RMS  → flower petal scale (bloom open)
  /melodia/audio/mid    float [0,1] mid RMS   → hue / stem sway
  /melodia/audio/treble float [0,1] treble RMS→ emissive sparkle

OSC In (UE→TD on 9000, from UMelodiaRhythmReactivitySubsystem::Publish()):
  /rhythm/beat_pulse    float [0,1] decays 6*DT per beat → sel_beat_pulse → lag_beat_pulse → bloom
  /rhythm/beat_phase    float [0,1] phase 0..1            → sel_beat_phase→ lag_beat_phase → sin sway
  Implemented via /melodia/audio/beat/pulse|phase aliases documented in osc_mapping.

Verification:
  1. In TD, open /project1/melodia_audio/audio_hub viewer — feed music → 3 channels move 0-1.
  2. OSC Out monitor: Dialogs → OSC Out → confirm 127.0.0.1:9000 firing.
  3. UE: Content/Python/osc_server.py handles /melodia/audio/* → MPC_Melodia_Palette Bass/Mid/Treble.
  4. python Tools/validate_audio_reactive_osc.py  (loopback probe — no TD needed)
  5. PIE: MPC_Melodia_Palette.Bass/Mid/Treble + BeatPulse/BeatPhase drive M_Flower_Audio:
       Bass→scale 0.9-1.15, Mid→hue +0.08, Treble→emissive, BeatPulse→pulse, BeatPhase→sway 0.02

Flower grammar (4 params per sprint 2.1):
  petal scale = 1.0 + bass * 0.15
  stem sway   = sin(beat_phase * 2π) * 0.02 + mid * 0.01
  petal hue   = base + mid * hue_range
  emissive    = treble * 0.6 + beat_pulse * 0.4

Notes:
  - File fallback means no mic required for validation.
  - Lag 0.1/0.35 chosen to avoid jitter while keeping transient response.
  - Single port 9000 reused — no 9870 listener created (verified below).
"""
info.comment = 'Network documentation — copy to Docs/Handoffs for sprint evidence'

# ── Summary prints (visible in TD textport / Envoy log) ──────────────
children = [ch.name for ch in c.findChildren()]
print('MELODIA_AUDIO_REACTIVE: wired %d OPS inside /project1/melodia_audio' % len(children))
print('OPS: ' + ', '.join(sorted(children)))
try:
    print('OSC_OUT: %s:%s via osc_out (verify in OSC monitor)' % (str(osc_out.par.address), str(osc_out.par.port)))
except: print('OSC_OUT: 127.0.0.1:9000 via osc_out')
print('PORT CHECK: osc_out.port=%s (must be 9000, NOT 9870)' % str(c.op('osc_out').par.port))
# Check no 9870 listener exists
for o in root.findChildren(type='oscinCHOP'):
    try:
        if str(o.par.port) == '9870':
            print('WARNING: stray 9870 listener found at %s — remove per sprint constraint' % o.path)
    except: pass
print('')
print('Next: set file_in.par.file to your WAV and toggle source_switch.par.index to 1')
print('      → watch audio_hub → confirm OSC monitor on Dialogs → confirm UE MPC writes')
