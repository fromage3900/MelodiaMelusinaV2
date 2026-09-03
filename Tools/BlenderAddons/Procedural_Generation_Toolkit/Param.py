class Param:
    def __init__(self, VarName = "", paramName = '', ShowInUI = True ,expand = False, slider = False,toggle = False,SkipNewRow = False,Randomize = True, useArr = False, arrIndex = 0, UseLable = False, Lable = "", Column = False,Share=True,UseBoolDropdown = False,BoolOnProps = [], BoolOffProps = [],CustomUICode = False,UILambda=None,Reset=True):
        self.paramName = paramName
        self.ShowInUI = ShowInUI
        self.VarName = VarName
        self.useArr = useArr
        self.arrIndex = arrIndex
        self.expand = expand
        self.slider = slider
        self.toggle = toggle
        self.SkipNewRow = SkipNewRow
        self.Randomize = Randomize
        self.UseLable = UseLable
        self.Lable = Lable
        self.Column = Column
        self.Share = Share
        self.UseBoolDropdown = UseBoolDropdown
        self.BoolOnProps = BoolOnProps
        self.BoolOffProps = BoolOffProps        
        self.CustomUICode = CustomUICode
        self.UILambda = UILambda
        self.Reset = Reset
