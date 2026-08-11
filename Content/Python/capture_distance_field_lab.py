import sys
sys.path.append('G:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import retake_scenecapture_still as cap
import importlib
cap = importlib.reload(cap)
import unreal
unreal.SystemLibrary.execute_console_command(None, 'r.ExposureOffset 0')
cap.PILLARS['DistanceFieldBlendLab'] = {
    'level':'/Game/Melodia/Levels/DistanceFieldBlendLab',
    'camera_prefer':('DFLab_Camera_Hero',),
    'alias':'distance_field_blend_lab', 'width':1280, 'height':720, 'fov':45.0,
}
result=cap.capture_pillar('DistanceFieldBlendLab')
unreal.log('[DistanceFieldCapture] '+str(result))
