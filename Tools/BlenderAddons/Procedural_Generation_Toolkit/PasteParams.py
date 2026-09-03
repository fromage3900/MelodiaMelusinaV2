import bpy

import csv
from io import StringIO
import zlib,base64

from .ProceduralGenProperties import DataSingleton

def num(s):
    if s[0] == "(":
        split = s[1:-1].split(",")
        try:
            test = [float(i) for i in split]
            return test
        except ValueError:
            try:
                return [int(i) for i in split]
            except ValueError:
                return split
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            if s == "True" or s == "False":
                return s == "True"
            else:
                return s    

def PasteParams(context, encD):
    scene = context.scene
    props = scene.Procedural_Gen_Props
    ExProps = getattr(scene,props.OperationsType)
    try:
        ins = zlib.decompress(base64.b64decode(encD)).decode('ascii')
    except ValueError:
        return

    f = StringIO(ins)
    reader = csv.reader(f, delimiter='*')
    props.PropChangesInProgress = True
    useC = False
    data = DataSingleton()
    
    row = next(reader, None)
    while row:
        if len(row)<2:
            useC = True
            break
        if len(row) == 2 and hasattr(ExProps,row[0]):
            setattr(ExProps,row[0],num(row[1]))
        if len(row) > 2:
            if row[0] == "V":
                for v in data.ActiveOperation.GetActiveViewers():
                    if v.UniqueName == row[1]:
                        t = int(row[2])
                        i = 0
                        for k in v.simpleParams.keys():
                            if t==i:
                                for par in v.simpleParams[k]:
                                    row = next(reader, None)
                                    if row:
                                        setattr(par.hostObj,row[0],num(row[1]))
                                break
                            i+=1
                        break
        row = next(reader, None)


    if useC:
        reader = csv.reader(f, delimiter=',')
        props.PropChangesInProgress = True
        for row in reader:
            setattr(ExProps,row[0],num(row[1]))
    props.PropChangesInProgress = False

class OBJECT_OT_Paste_Params(bpy.types.Operator):
    bl_idname = "object.procedural_gen_paste_parameters"
    bl_label = "Paste Seed"
    bl_description = "Paste The Seed Values"

    
    def execute(self,context):

        encD = bpy.context.window_manager.clipboard

        PasteParams(context, encD)

        return {'FINISHED'}

