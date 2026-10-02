import bpy,sys,os,glob
d=os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--")+1]))
ref=None
for f in sorted(glob.glob(d+"/A_ChoralSheep_*.fbx")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    a=next(o for o in bpy.data.objects if o.type=="ARMATURE")
    names={b.name for b in a.data.bones}
    act=a.animation_data.action if a.animation_data else None
    fr=act.frame_range if act else None
    mv=0;mb=None
    if act:
        s=bpy.context.scene; s.frame_set(int(fr[0])); p0={b.name:b.matrix.translation.copy() for b in a.pose.bones}
        q0={b.name:b.rotation_quaternion.copy() for b in a.pose.bones}
        s.frame_set(int((fr[0]+fr[1])/2))
        for b in a.pose.bones:
            m=(b.matrix.translation-p0[b.name]).length+ (b.rotation_quaternion-q0[b.name]).magnitude*0.1
            if m>mv: mv,mb=m,b.name
    print("V",os.path.basename(f),len(names),fr and tuple(fr),round(mv,4),mb)
