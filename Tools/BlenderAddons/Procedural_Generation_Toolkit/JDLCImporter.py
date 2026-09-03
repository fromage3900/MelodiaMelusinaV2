import importlib.util
import re
import bpy
import os
from . DataSingleton import DataSingleton
import csv
from io import StringIO

def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class OneObj:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state

class JDLCImporter(OneObj):
    def __init__(self):
        OneObj.__init__(self)
    def __str__(self): return self.val

    def Reaload(self):
        for c in self.Classes:
            importlib.reload(c)

    def Load(self):
        import bpy.utils.previews
        addonPath =bpy.utils.user_resource('SCRIPTS')+"/addons/"
        self.pcoll = bpy.utils.previews.new()
        Paths = next(os.walk(addonPath))[1]
        JDLCs = []
        self.JDLCContent = {}
        self.mods = []
        self.modNames = []
        
        self.Classes = ()
        for p in Paths:
            if "JDLC" in p:
                JDLCs.append(p)

        for DLC in JDLCs:
            filenames = next(os.walk(addonPath+DLC), (None, None, []))[2]
            self.JDLCContent[DLC] = []

            for f in filenames:
                if ".py" in f and not "init" in f:
                    name = f[:-3]
                    mod = module_from_file(name, addonPath+DLC+"/"+f)
                    Tclass = getattr(mod,"Procedural_Gen_"+name+"_Props")
                    self.JDLCContent[DLC].append((name,mod,Tclass))
                    self.Classes = self.Classes + (Tclass,)
                    
    def SavePresets(self,context):
        presets = context.scene.PGT_PROP_LIST
        scene = context.scene
        props = scene.Procedural_Gen_Props
        if props.PropChangesInProgress:
            return
        path = self.GetActiveOpPath()
        if presets:
            f = open(path+props.OperationsType+"_Presets.txt", "w")
            l = []
            for p in presets:
                l.append(p.name+","+p.seed+"\n")

            f.writelines(l)

            f.close()
        elif(os.path.exists(path+props.OperationsType+"_Presets.txt")):
            os.remove(path+props.OperationsType+"_Presets.txt")

    def LoadPresets(self,context):
        #open and read the file after the appending:
        scene = context.scene
        props = scene.Procedural_Gen_Props
        scene.PGT_PROP_LIST.clear()

        path = self.GetActiveOpPath()+props.OperationsType+"_Presets.txt"

        if not os.path.exists(path):
            return

        f = open(path)
        s = StringIO(f.read())
        reader = csv.reader(s, delimiter=',')

        props.PropChangesInProgress = True
        for row in reader:
            item = scene.PGT_PROP_LIST.add()
            item.name = row[0]
            item.seed = row[1]  
        props.PropChangesInProgress = False

        f.close()

    def GetClasses(self):
        return self.Classes

    def Register(self):
        for key in self.JDLCContent:
            for c in self.JDLCContent[key]:
                setattr(bpy.types.Scene, c[0], bpy.props.PointerProperty(type = c[2]) )
                c[1].Register()

    def Unregister(self):
        for key in self.JDLCContent:
            for c in self.JDLCContent[key]:
                c[1].Unregister()
                temp = getattr(bpy.types.Scene,c[0])
                del temp

    def Make(self,context):
        for key in self.JDLCContent:
            for c in self.JDLCContent[key]:
                c[1].Make(context)

    def GetActiveOpPath(self):
        addonPath =bpy.utils.user_resource('SCRIPTS')+"/addons/"
        data = DataSingleton()

        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        key =  next(filter(lambda x: x[0] == props.OperationsType , data.OperationsTypes))[2]
        
        return addonPath+key+"/"

    def LoadTumbFromPath(self,path,fileName):
        thumb = self.pcoll.load(path+fileName, path+fileName, 'IMAGE')
        return thumb

    def SetOpTypes(self):
        i = 0
        addonPath =bpy.utils.user_resource('SCRIPTS')+"/addons/"
        for key in self.JDLCContent:
            for c in self.JDLCContent[key]:
                #DataSingleton().OperationsTypes.append((n,n,"",i))
                thumb = self.LoadTumbFromPath(addonPath+key+"/",c[0]+".png")
                #setattr(thumb,"image_size",[1024,1024])
                #thumb.icon_size.as_pointer() 
                #thumb.reload()
                new = re.sub(r"(\w)([A-Z])", r"\1 \2", c[0])
                DataSingleton().OperationsTypes.append((c[0], new, key, thumb.icon_id, i))

                i += 1