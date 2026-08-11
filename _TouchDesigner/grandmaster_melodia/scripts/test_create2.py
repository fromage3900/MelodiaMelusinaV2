# Test specific operator types that might fail
me = op('/project1')

test_comp = me.create(baseCOMP, 'test_types')

types_to_test = [
    (audiofileinCHOP, 'afi_test'),
    (pitchCHOP, 'pitch_test'),
    (envelopeCHOP, 'env_test'),
    (spectrumCHOP, 'spec_test'),
    (beatCHOP, 'beat_test'),
    (waveCHOP, 'wave_test'),
    (nullCHOP, 'null_test'),
    (lumaKeyTOP, 'luma_test'),
    (blurTOP, 'blur_test'),
    (compositeTOP, 'comp_test'),
    (rampTOP, 'ramp_test'),
    (overTOP, 'over_test'),
    (nullTOP, 'nulltop_test'),
    (outTOP, 'out_test'),
    (particlesGpuCOMP, 'particle_test'),
    (glslmultiTOP, 'glsl_test'),
    (oscinCHOP, 'oscin_test'),
    (oscoutCHOP, 'oscout_test'),
    (tableDAT, 'table_test'),
    (fbxCOMP, 'fbx_test'),
    (cameraCOMP, 'cam_test'),
    (lightCOMP, 'light_test'),
    (renderTOP, 'render_test'),
    (sliderCOMP, 'slider_test'),
    (textTOP, 'text_test'),
    (moviefileoutTOP, 'movie_test'),
]

for op_type, op_name in types_to_test:
    try:
        op_test = test_comp.create(op_type, op_name)
        print('  OK:', op_name)
    except Exception as e:
        print('  FAIL:', op_name, '->', str(e)[:80])

# Cleanup
test_comp.destroy()
print('Done.')
