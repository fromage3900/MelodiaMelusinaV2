import unreal
for n in dir(unreal):
    if 'screenshot' in n.lower() or 'capture' in n.lower(): unreal.log('[CaptureAPI] '+n)
