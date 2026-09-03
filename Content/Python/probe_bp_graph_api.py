import unreal
for c in [unreal.Blueprint,unreal.EdGraph,unreal.K2Node_CallFunction,unreal.K2Node_FunctionEntry,unreal.K2Node_FunctionResult]:
 print(c,[x for x in dir(c) if any(k in x.lower() for k in ['graph','node','function','pin','add','remove'])][:120])
