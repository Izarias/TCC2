import ast
import operator as op

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.Num):  # compat
        return node.n

    if isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        fn = OPS.get(type(node.op))
        if fn is None:
            raise ValueError("Operador não permitido")
        return fn(left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand)
        fn = OPS.get(type(node.op))
        if fn is None:
            raise ValueError("Operador não permitido")
        return fn(operand)

    raise ValueError("Expressão inválida")

def calcular(expressao: str):
    expressao = expressao.strip().replace(",", ".")
    tree = ast.parse(expressao, mode="eval")
    return _eval(tree)

def main():
    while True:
        try:
            expr = input("Digite a expressão (Enter para sair): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not expr:
            break
        try:
            print(calcular(expr))
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    main()