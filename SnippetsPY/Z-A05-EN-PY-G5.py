import ast
import operator as op

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


def evaluate_expression(expr: str):
    node = ast.parse(expr, mode="eval").body

    def _eval(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN_OPS:
            return _BIN_OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UNARY_OPS:
            return _UNARY_OPS[type(n.op)](_eval(n.operand))
        raise ValueError("Unsupported expression")

    return _eval(node)


def main():
    expr = input("Enter an expression: ").strip()
    if not expr:
        return
    try:
        print(evaluate_expression(expr))
    except ZeroDivisionError:
        print("Error: division by zero")
    except (SyntaxError, ValueError):
        print("Error: invalid or unsupported expression")


if __name__ == "__main__":
    main()