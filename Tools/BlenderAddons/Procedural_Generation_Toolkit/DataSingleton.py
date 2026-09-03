class OneObj:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state
        
class DataSingleton(OneObj):
    Operations = []
    OperationsTypes = []
    PrefOpType = None
    Fractal_Data = dict()
    
    ActiveOperation = None
    IsInitialized = False
    def __init__(self):
        OneObj.__init__(self)
    def __str__(self): return self.val

