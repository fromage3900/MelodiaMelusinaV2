me = op('/project1')
test = me.create('baseCOMP', 'type_test')

ops = [
    ('baseCOMP','Base COMP'), ('particlesGpuCOMP','Particles GPU'), ('fbxCOMP','FBX'),
    ('cameraCOMP','Camera'), ('lightCOMP','Light'), ('sliderCOMP','Slider'),
    ('audiofileinCHOP','Audio In'), ('pitchCHOP','Pitch'), ('envelopeCHOP','Envelope'),
    ('spectrumCHOP','Spectrum'), ('beatCHOP','Beat'), ('nullCHOP','Null CHOP'),
    ('oscinCHOP','OSC In'), ('oscoutCHOP','OSC Out'), ('waveformCHOP','Waveform'),
    ('blurTOP','Blur'), ('compositeTOP','Composite'), ('rampTOP','Ramp'),
    ('overTOP','Over'), ('nullTOP','Null TOP'), ('outTOP','Out'), ('renderTOP','Render'),
    ('moviefileoutTOP','Movie Out'), ('textTOP','Text TOP'), ('glslmultiTOP','GLSL Multi'),
    ('lumaLevelTOP','Luma Level'), ('tableDAT','Table'), ('textDAT','Text DAT'),
]

results_ok = []
results_fail = []

for op_str, label in ops:
    try:
        o = test.create(op_str)
        o.destroy()
        results_ok.append(op_str)
    except Exception as e:
        results_fail.append((op_str, label, str(e)[:80]))

test.destroy()

out = 'OK:' + str(len(results_ok)) + ':' + ','.join(results_ok)
print(out)
if results_fail:
    print('FAIL:' + str(len(results_fail)))
    for t, l, e in results_fail:
        print('ERR:' + t + ':' + l + ':' + e)
