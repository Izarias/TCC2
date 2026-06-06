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


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError("Only numbers are allowed.")

    if isinstance(node, ast.UnaryOp):
        fn = _UNARY_OPS.get(type(node.op))
        if fn is None:
            raise CalculatorError("Unsupported unary operator.")
        return fn(_eval_ast(node.operand))

    if isinstance(node, ast.BinOp):
        fn = _BIN_OPS.get(type(node.op))
        if fn is None:
            raise CalculatorError("Unsupported operator.")
        return fn(_eval_ast(node.left), _eval_ast(node.right))

    raise CalculatorError("Invalid expression.")


def calculate(expression: str):
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise CalculatorError("Syntax error.") from e
    return _eval_ast(tree)


def main():
    expr = input("Enter an expression: ").strip()
    if not expr:
        print("No expression provided.")
        return

    try:
        result = calculate(expr)
        print(result)
    except CalculatorError as e:
        print(f"Error: {e}")
    except ZeroDivisionError:
        print("Error: Division by zero.")


if __name__ == "__main__":
    main()