import sys, importlib
sys.path.append('G:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import retake_scenecapture_still as cap
cap=importlib.reload(cap)
import unreal
cap.PILLARS['DFNear']={'level':'/Game/Melodia/Levels/DistanceFieldBlendLab','camera_prefer':('DFLab_Camera_Hero',),'alias':'distance_field_near','width':1280,'height':720,'fov':45.0}
cap.PILLARS['DFMid']=dict(cap.PILLARS['DFNear'],alias='distance_field_mid')
cap.PILLARS['DFFar']=dict(cap.PILLARS['DFNear'],alias='distance_field_far')
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for name,loc,rot in [('DFNear',(520,-580,330),(0,-24,131.3)),('DFMid',(720,-820,480),(0,-24,131.3)),('DFFar',(1100,-1250,720),(0,-24,131.3))]:
    les.load_level('/Game/Melodia/Levels/DistanceFieldBlendLab')
    cam=next(a for a in eas.get_all_level_actors() if a.get_actor_label()=='DFLab_Camera_Hero')
    cam.set_actor_location(unreal.Vector(*loc), False, True); cam.set_actor_rotation(unreal.Rotator(*rot), False); les.save_current_level()
    unreal.log('[DistanceFieldCapture] '+str(cap.capture_pillar(name)))
