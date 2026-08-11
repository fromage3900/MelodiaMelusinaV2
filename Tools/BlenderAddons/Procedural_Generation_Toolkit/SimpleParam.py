class SimpleParam:
    def __init__(self, hostObj , paramName,UIName, identifier = None ,defaultHost = None):
        self.hostObj = hostObj
        self.UIName = UIName
        self.paramName = paramName
        self.identifier = identifier
        self.defaultHost = defaultHost

