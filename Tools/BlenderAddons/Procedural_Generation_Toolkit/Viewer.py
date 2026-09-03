import bpy
from .SimpleParam import SimpleParam

class Viewer():
    def __init__(self):
        self.SimpleParam = {}
        self.UniqueName = ""
    def GetAllParams(self):
        params = []
        for k in self.simpleParams.keys():
            for p in self.simpleParams[k]:
                params.append(p)
        return params