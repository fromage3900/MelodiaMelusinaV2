a = op('/project1/audio')

# Destroy any existing children for clean rebuild
for c in list(a.findChildren()):
    c.destroy()

# 1. Audio File In CHOP
afi = a.create('audiofileinCHOP', 'melusina_in')
afi.nodeX = 0; afi.nodeY = 0
afi.comment = 'Load Melusina WAV from VoiceSynthResearch/'
# User sets the file path after WAV is available:
# afi.par.file = 'G:/EnvironmentPortfolio/VoiceSynthResearch/output.wav'

# 2. Pitch analyzer
pitch = a.create('pitchCHOP', 'pitch_analyzer')
pitch.nodeX = 250; pitch.nodeY = 0
pitch.inputConnectors[0].connect(afi)
pitch.comment = 'Fundamental frequency (Hz) -> /melusina/pitch -> UE shader warp'

# 3. Amplitude envelope follower
env = a.create('envelopeCHOP', 'amp_envelope')
env.nodeX = 250; env.nodeY = -120
env.inputConnectors[0].connect(afi)
env.comment = 'RMS amplitude (0-1) -> /melusina/amp -> UE particle spawn rate'

# 4. Spectrum analyzer
spec = a.create('spectrumCHOP', 'spectral_analyzer')
spec.nodeX = 250; spec.nodeY = -240
spec.inputConnectors[0].connect(afi)
spec.comment = 'Frequency spectrum -> particle color temperature'

# 5. Beat detector
beat = a.create('beatCHOP', 'beat_detector')
beat.nodeX = 500; beat.nodeY = 0
beat.inputConnectors[0].connect(afi)
beat.comment = 'Beat trigger -> /melusina/beat -> wish burst'

# 6. Waveform scope (visual only)
wave = a.create('waveformCHOP', 'waveform_scope')
wave.nodeX = 500; wave.nodeY = -120
wave.inputConnectors[0].connect(afi)

# 7. Null hub — collects all outputs
hub = a.create('nullCHOP', 'audio_hub')
hub.nodeX = 750; hub.nodeY = 0

chs = [pitch, env, spec, beat, wave]
for i, ch in enumerate(chs):
    hub.inputConnectors[i].connect(ch)

# 8. OSC Out for audio -> UE
osc_out = a.create('oscoutCHOP', 'out_to_ue')
osc_out.nodeX = 1000; osc_out.nodeY = 0
osc_out.par.port = 8000
osc_out.par.address = '127.0.0.1'
osc_out.comment = 'Audio OSC: /melusina/pitch, /melusina/amp -> UE'

children = [c.name for c in a.findChildren()]
print('AUDIO_DONE:' + str(len(children)) + ':' + ','.join(children))
