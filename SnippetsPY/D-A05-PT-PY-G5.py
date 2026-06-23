import ast
import operator as op


class CalculatorError(Exception):
    pass


_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

_UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError("A expressão contém um valor não numérico.")

    if isinstance(node, ast.BinOp):
        fn = _BIN_OPS.get(type(node.op))
        if fn is None:
            raise CalculatorError("Operador não suportado.")
        left = _eval(node.left)
        right = _eval(node.right)
        return fn(left, right)

    if isinstance(node, ast.UnaryOp):
        fn = _UNARY_OPS.get(type(node.op))
        if fn is None:
            raise CalculatorError("Operador unário não suportado.")
        return fn(_eval(node.operand))

    if isinstance(node, ast.ParenExpr):  # Python 3.12+
        return _eval(node.expression)

    raise CalculatorError("A expressão contém elementos não suportados.")


def evaluate(expr: str):
    expr = expr.strip()
    if not expr:
        raise CalculatorError("Entrada vazia.")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise CalculatorError("Expressão inválida (erro de sintaxe).")
    try:
        return _eval(tree)
    except ZeroDivisionError:
        raise CalculatorError("Divisão por zero.")


def main():
    while True:
        try:
            s = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if s.lower() in {"sair", "exit", "quit"}:
            break
        if not s:
            continue

        try:
            result = evaluate(s)
        except CalculatorError as e:
            print(f"Erro: {e}")
        else:
            print(result)


if __name__ == "__main__":
    main()