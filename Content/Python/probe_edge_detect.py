"""One-shot: list unreal MaterialExpression classes containing Edge."""
import unreal

hits = sorted(n for n in dir(unreal) if "Edge" in n and "Material" in n)
print("EDGE_EXPR_CLASSES", hits)
for name in (
    "MaterialExpressionEdgeDetect",
    "MaterialExpressionFwidth",
    "MaterialExpressionDDX",
    "MaterialExpressionDDY",
    "MaterialExpressionCustom",
):
    print(name, hasattr(unreal, name))
