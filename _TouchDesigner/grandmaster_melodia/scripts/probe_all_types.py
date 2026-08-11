# Probe ALL operator string names in TD 2025.32460
# Each create fails → try next candidate until success
import td

me = op('/project1')
test = me.create('baseCOMP', 'string_test')

if test is None:
    print('ERROR: baseCOMP create returned None')
else:
    print('Test container created:', test.path)

# Test every op type we need with string names
ops_needed = {
    # COMPs
    'Base COMP':           'baseCOMP',
    'Particles GPU':       'particlesGpuCOMP',
    'FBX Loader':          'fbxCOMP',
    'Camera':              'cameraCOMP',
    'Light':               'lightCOMP',
    'Slider':              'sliderCOMP',
    'Button':              'buttonCOMP',
    
    # CHOPs
    'Audio File In':       'audiofileinCHOP',
    'Pitch':               'pitchCHOP',
    'Envelope':            'envelopeCHOP',
    'Spectrum':            'spectrumCHOP',
    'Beat':                'beatCHOP',
    'Null':                'nullCHOP',
    'OSC In':              'oscinCHOP',
    'OSC Out':             'oscoutCHOP',
    'Waveform':            'waveformCHOP',
    
    # TOPs
    'Blur':                'blurTOP',
    'Composite':           'compositeTOP',
    'Ramp':                'rampTOP',
    'Over':                'overTOP',
    'Null':                'nullTOP',
    'Out':                 'outTOP',
    'Render':              'renderTOP',
    'Movie File Out':      'moviefileoutTOP',
    'Text':                'textTOP',
    'GLSL Multi':          'glslmultiTOP',
    'Luma Level':          'lumaLevelTOP',
    
    # DATs
    'Table':               'tableDAT',
    'Text':                'textDAT',
}

results = {'ok': [], 'fail': []}

for label, op_str in ops_needed.items():
    try:
        op_test = test.create(op_str, 'test_' + label.replace(' ', '_'))
        results['ok'].append((label, op_str))
        op_test.destroy()
    except Exception as e:
        # Try without name
        try:
            op_test2 = test.create(op_str)
            results['ok'].append((label, op_str + ' (no name)'))
            op_test2.destroy()
        except Exception as e2:
            results['fail'].append((label, op_str, str(e)[:80]))

print('')
print('OK ({}) :'.format(len(results['ok'])))
for label, s in results['ok']:
    print('  [OK] {} : td.create({!r})'.format(label, s))

print('')
print('FAIL ({}):'.format(len(results['fail'])))
for label, s, err in results['fail']:
    print('  [FAIL] {} : {!r} -> {}'.format(label, s, err))

test.destroy()
print('')
print('Cleaned up.')
