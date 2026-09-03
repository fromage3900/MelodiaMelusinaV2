# Probe available operator type names in TD 2025.32460
import td

# Check all the types we need
types_to_check = [
    'audiofileinCHOP', 'pitchCHOP', 'envelopeCHOP', 'spectrumCHOP', 
    'beatCHOP', 'waveCHOP', 'waveformCHOP', 'nullCHOP',
    'lumaKeyTOP', 'lumaLevelTOP', 'lumaTOP', 'thresholdTOP',
    'blurTOP', 'compositeTOP', 'rampTOP', 'overTOP', 'nullTOP', 'outTOP',
    'particlesGpuCOMP', 'particlesGpu', 'particleCOMP',
    'glslmultiTOP', 'glslTOP',
    'oscinCHOP', 'oscoutCHOP', 'oscinDAT', 'oscoutDAT',
    'tableDAT', 'fbxCOMP', 'cameraCOMP', 'lightCOMP',
    'renderTOP', 'sliderCOMP', 'textTOP', 'moviefileoutTOP',
    'baseCOMP', 'containerCOMP',
]

found = []
missing = []
for t in types_to_check:
    if hasattr(td, t):
        found.append(t)
    else:
        missing.append(t)

print('Found ({}) :'.format(len(found)))
for f in sorted(found):
    print('  td.' + f)

print('')
print('Missing ({}):'.format(len(missing)))
for m in sorted(missing):
    print('  ' + m)

# Try to find similar names for missing ones
print('')
print('Similar names search:')
all_types = [x for x in dir(td) if 'CHOP' in x or 'TOP' in x or 'COMP' in x or 'DAT' in x]
for m in missing:
    similar = [x for x in all_types if m[:4].lower() in x.lower()]
    if similar:
        print('  {} -> maybe: {}'.format(m, similar[:5]))
    else:
        print('  {} -> no similar found'.format(m))
