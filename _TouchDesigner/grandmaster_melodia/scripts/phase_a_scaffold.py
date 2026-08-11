# ================================================================
# GRANDMASTER MELODIA v2 — Phase A: Foundation Scaffold
# Run in TouchDesigner Textport (Alt+T)
# ================================================================
import time

# Auto-detect project root
me = op('/project1')
if me is None:
    roots = root().findChildren(type=COMP, depth=0, maxDepth=0)
    me = roots[0] if roots else root()

print('Grandmaster Melodia Phase A — Building in: {}'.format(me.path))
print('')

# ── 1. AUDIO ENGINE ─────────────────────────────────────────────
audio = me.create(baseCOMP, 'audio')
audio.nodeX = -1200; audio.nodeY = 0
audio.comment = 'Melusina VoiceSynth audio analysis engine'

afi = audio.create(audiofileinCHOP, 'melusina_in')
afi.nodeX = 0; afi.nodeY = 0

pitch = audio.create(pitchCHOP, 'pitch_analyzer')
pitch.nodeX = 250; pitch.nodeY = 0
pitch.inputConnectors[0].connect(afi)

env = audio.create(envelopeCHOP, 'amp_envelope')
env.nodeX = 250; env.nodeY = -120
env.inputConnectors[0].connect(afi)

spec = audio.create(spectrumCHOP, 'spectral_analyzer')
spec.nodeX = 250; spec.nodeY = -240
spec.inputConnectors[0].connect(afi)

beat = audio.create(beatCHOP, 'beat_detector')
beat.nodeX = 500; beat.nodeY = 0
beat.inputConnectors[0].connect(afi)

wave = audio.create(waveCHOP, 'waveform_scope')
wave.nodeX = 500; wave.nodeY = -120
wave.inputConnectors[0].connect(afi)

# Null hub
audio_hub = audio.create(nullCHOP, 'audio_hub')
audio_hub.nodeX = 750; audio_hub.nodeY = 0

chs = [pitch, env, spec, beat, wave]
for i, ch in enumerate(chs):
    audio_hub.inputConnectors[i].connect(ch)

print('[OK] Audio engine: 5 CHOPs + null hub')

# ── 2. POST-FX CHAIN ────────────────────────────────────────────
postfx = me.create(baseCOMP, 'postfx')
postfx.nodeX = -1200; postfx.nodeY = 400
postfx.comment = 'Nikki bloom chain (3-pass Gaussian) + LUT + DOF'

thresh = postfx.create(lumaKeyTOP, 'bloom_threshold')
thresh.nodeX = 0; thresh.nodeY = 0
thresh.par.threshold = 0.75

blur5 = postfx.create(blurTOP, 'bloom_blur_5')
blur5.nodeX = 250; blur5.nodeY = 0
blur5.par.filtertype = 'gaussian'
blur5.par.filterpixels = 5
blur5.inputConnectors[0].connect(thresh)

blur15 = postfx.create(blurTOP, 'bloom_blur_15')
blur15.nodeX = 250; blur15.nodeY = -120
blur15.par.filtertype = 'gaussian'
blur15.par.filterpixels = 15
blur15.inputConnectors[0].connect(thresh)

blur30 = postfx.create(blurTOP, 'bloom_blur_30')
blur30.nodeX = 250; blur30.nodeY = -240
blur30.par.filtertype = 'gaussian'
blur30.par.filterpixels = 30
blur30.inputConnectors[0].connect(thresh)

bloom_comp = postfx.create(compositeTOP, 'bloom_composite')
bloom_comp.nodeX = 500; bloom_comp.nodeY = 0
bloom_comp.inputConnectors[0].connect(blur5)
bloom_comp.inputConnectors[1].connect(blur15)
bloom_comp.inputConnectors[2].connect(blur30)

lut_ramp = postfx.create(rampTOP, 'nikki_lut_preview')
lut_ramp.nodeX = 0; lut_ramp.nodeY = -360
lut_ramp.comment = 'Nikki warm-golden color grade LUT'

vig_ramp = postfx.create(rampTOP, 'vignette')
vig_ramp.nodeX = 250; vig_ramp.nodeY = -360
vig_ramp.par.type = 'radial'

vig_over = postfx.create(overTOP, 'vignette_over')
vig_over.nodeX = 500; vig_over.nodeY = -240

postfx_out = postfx.create(nullTOP, 'postfx_out')
postfx_out.nodeX = 750; postfx_out.nodeY = 0

print('[OK] Post-FX: 3-pass bloom + LUT + vignette')

# ── 3. PARTICLE SYSTEMS ─────────────────────────────────────────
particles = me.create(baseCOMP, 'particles')
particles.nodeX = -1200; particles.nodeY = 800
particles.comment = 'Nikki particle systems (POP networks)'

sparkles = particles.create(particlesGpuCOMP, 'sparkles')
sparkles.nodeX = 0; sparkles.nodeY = 0
sparkles.par.particles = 40
sparkles.par.lifespan = 8
sparkles.par.speed = 0.05
sparkles.par.speedrand = 0.08
sparkles.par.birthtype = 'spread'
sparkles.par.spread = 0.3
sparkles.comment = '40x 4-point star sparkles, gold-to-pink, sin-wave drift'

motes = particles.create(particlesGpuCOMP, 'motes')
motes.nodeX = 300; motes.nodeY = 0
motes.par.particles = 50
motes.par.lifespan = 12
motes.par.speed = 0.02
motes.par.speedrand = 0.04
motes.par.birthtype = 'spread'
motes.par.spread = 0.6
motes.comment = '50x soft radial dots, cream-to-lavender, very slow drift'

burst = particles.create(particlesGpuCOMP, 'wish_burst')
burst.nodeX = 600; burst.nodeY = 0
burst.par.particles = 120
burst.par.lifespan = 2.5
burst.par.speed = 0.3
burst.par.speedrand = 0.5
burst.par.birthtype = 'explode'
burst.par.force = 1.5
burst.comment = '120x wish energy burst, gold-to-hot-pink, audio triggered'

particle_bloom = particles.create(blurTOP, 'particle_bloom')
particle_bloom.nodeX = 900; particle_bloom.nodeY = 0
particle_bloom.par.filtertype = 'gaussian'
particle_bloom.par.filterpixels = 8

print('[OK] Particles: 3 POPs (40+50+120) + bloom')

# ── 4. SHADER LAB ───────────────────────────────────────────────
shaders = me.create(baseCOMP, 'shaders')
shaders.nodeX = -1200; shaders.nodeY = 1200
shaders.comment = 'GLSL shader prototyping — Nikki/Melodia toon library'

glsl_toon = shaders.create(glslmultiTOP, 'glsl_nikki_toon')
glsl_toon.nodeX = 0; glsl_toon.nodeY = 0
glsl_toon.comment = 'Nikki soft toon: half-Lambert diffuse wrap + warm Fresnel rim'

glsl_satin = shaders.create(glslmultiTOP, 'glsl_satin_fabric')
glsl_satin.nodeX = 300; glsl_satin.nodeY = 0
glsl_satin.comment = 'Anisotropic satin fabric: direction-dependent specular'

glsl_crystal = shaders.create(glslmultiTOP, 'glsl_crystal')
glsl_crystal.nodeX = 600; glsl_crystal.nodeY = 0
glsl_crystal.comment = 'Crystal/refraction: internal caustic + cube-map env'

glsl_star = shaders.create(glslmultiTOP, 'glsl_sparkle')
glsl_star.nodeX = 900; glsl_star.nodeY = 0
glsl_star.comment = '4-point star SDF generator: gold-to-pink gradient'

print('[OK] Shader lab: 4 GLSL TOPs')

# ── 5. OSC ROUTING HUB ──────────────────────────────────────────
osc = me.create(baseCOMP, 'osc')
osc.nodeX = -600; osc.nodeY = 0
osc.comment = 'OSC routing hub: Blender:9000 <-> TD <-> UE:8000'

osc_in_bl = osc.create(oscinCHOP, 'in_blender')
osc_in_bl.nodeX = 0; osc_in_bl.nodeY = 0
osc_in_bl.par.port = 9000
osc_in_bl.comment = 'Receive camera/geometry from Blender'

osc_out_mat = osc.create(oscoutCHOP, 'out_ue_material')
osc_out_mat.nodeX = 0; osc_out_mat.nodeY = -150
osc_out_mat.par.port = 8000
osc_out_mat.par.address = '127.0.0.1'
osc_out_mat.comment = 'Push material toon_params + preset to UE'

osc_out_niag = osc.create(oscoutCHOP, 'out_ue_niagara')
osc_out_niag.nodeX = 0; osc_out_niag.nodeY = -300
osc_out_niag.par.port = 8000
osc_out_niag.par.address = '127.0.0.1'
osc_out_niag.comment = 'Push Niagara spawn rates + wind + audio to UE'

osc_table = osc.create(tableDAT, 'routing_table')
osc_table.nodeX = 350; osc_table.nodeY = 0
osc_table.comment = 'Live OSC routing table — source of truth'

print('[OK] OSC hub: 1 in + 2 out + routing table')

# ── 6. GEOMETRY LOADER ──────────────────────────────────────────
geo = me.create(baseCOMP, 'geo')
geo.nodeX = -600; geo.nodeY = 400
geo.comment = 'FBX/USD geometry loader + camera rig + lighting'

fbx = geo.create(fbxCOMP, 'fbx_import')
fbx.nodeX = 0; fbx.nodeY = 0
fbx.comment = 'Load FBX from _TouchDesigner/exports/'

cam = geo.create(cameraCOMP, 'camera_rig')
cam.nodeX = 0; cam.nodeY = -200
cam.comment = 'Cinematic orbit: 20s loop, 25deg elevation, CW rotation'

key_light = geo.create(lightCOMP, 'light_key')
key_light.nodeX = 200; key_light.nodeY = -200
key_light.par.lighttype = 'directional'
key_light.comment = 'Warm key: azimuth 240deg, elevation 25deg, color #FFF5E8'

print('[OK] Geometry: FBX loader + camera rig + key light')

# ── 7. RENDER OUTPUT ────────────────────────────────────────────
render = me.create(baseCOMP, 'render')
render.nodeX = -600; render.nodeY = 800
render.comment = 'Final render chain: main + stats overlay + output'

main_render = render.create(renderTOP, 'render_main')
main_render.nodeX = 0; main_render.nodeY = 0
main_render.comment = 'Main render: combines geo + postfx + particles'

overlay = render.create(overTOP, 'stats_overlay')
overlay.nodeX = 250; overlay.nodeY = 0
overlay.comment = 'Overlay stats text on final render'

out_final = render.create(outTOP, 'out_final')
out_final.nodeX = 500; out_final.nodeY = 0
out_final.inputConnectors[0].connect(overlay)

print('[OK] Render: main + overlay + output')

# ── 8. UI / CONTROL PANEL ───────────────────────────────────────
ui = me.create(baseCOMP, 'ui')
ui.nodeX = -600; ui.nodeY = 1200
ui.comment = 'Control panel: presets, sliders, stats, material sheet'

preset_sw = ui.create(sliderCOMP, 'preset_switcher')
preset_sw.nodeX = 0; preset_sw.nodeY = 0
preset_sw.par.label = 'Style Preset'
preset_sw.par.defaultvalue = 0
preset_sw.par.clampmin = 0
preset_sw.par.clampmax = 4
preset_sw.par.clampenable = True
preset_sw.comment = '0=Nikki 1=Madoka 2=Celestial 3=Itto 4=Sakura'

time_sl = ui.create(sliderCOMP, 'day_night_cycle')
time_sl.nodeX = 0; time_sl.nodeY = -150
time_sl.par.label = 'Day/Night Cycle'
time_sl.par.defaultvalue = 0.5
time_sl.comment = '0=dawn 0.25=noon 0.5=dusk 0.75=midnight'

audio_sl = ui.create(sliderCOMP, 'audio_gain')
audio_sl.nodeX = 0; audio_sl.nodeY = -300
audio_sl.par.label = 'Audio Reactivity'
audio_sl.par.defaultvalue = 0.7
audio_sl.par.clampmin = 0.0
audio_sl.par.clampmax = 2.0

part_sl = ui.create(sliderCOMP, 'particle_density')
part_sl.nodeX = 0; part_sl.nodeY = -450
part_sl.par.label = 'Particle Density'
part_sl.par.defaultvalue = 1.0
part_sl.par.clampmin = 0.1
part_sl.par.clampmax = 2.0

stats_txt = ui.create(textTOP, 'stats_overlay')
stats_txt.nodeX = 350; stats_txt.nodeY = 0
stats_txt.comment = 'Live stats: project, tris, meshes, FPS, OSC status'

mat_tbl = ui.create(tableDAT, 'material_sheet')
mat_tbl.nodeX = 350; mat_tbl.nodeY = -200
mat_tbl.comment = 'Material breakdown for current scene'

print('[OK] UI: 4 sliders + stats + material sheet')

# ── 9. EXPORT ───────────────────────────────────────────────────
export = me.create(baseCOMP, 'export')
export.nodeX = -600; export.nodeY = 1600
export.comment = 'Screenshot export + OSC manifest export'

snap = export.create(moviefileoutTOP, 'screenshot')
snap.nodeX = 0; snap.nodeY = 0
snap.comment = 'Capture hero render to PNG sequence'

print('[OK] Export: screenshot output')

# ── 10. SUMMARY ─────────────────────────────────────────────────
print('')
print('=' * 60)
print('  GRANDMASTER MELODIA TD — Phase A COMPLETE')
print('')
print('  9 containers scaffolded in {}'.format(me.path))
print('')
print('  /audio     5 CHOPs  (pitch, envelope, spectrum, beat, wave)')
print('  /postfx    5 TOPs   (threshold, 3x blur, composite)')
print('  /particles 4 POPs   (sparkles, motes, burst, bloom)')
print('  /shaders   4 GLSL   (toon, satin, crystal, sparkle)')
print('  /osc       3 OSC    (blender:9000 in, ue:8000 out x2)')
print('  /geo       3 COMPs  (FBX, camera, light)')
print('  /render    3 TOPs   (main, overlay, output)')
print('  /ui        6 OPs    (4 sliders + text + table)')
print('  /export    1 TOP    (screenshot)')
print('')
print('  Next: Tag each COMP with lctrl+lctrl for TDN export')
print('  Then: Ctrl+Shift+U to externalize all networks')
print('=' * 60)
