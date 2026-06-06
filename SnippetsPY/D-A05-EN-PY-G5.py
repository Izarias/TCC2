import ast
import operator as op

BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub,
)

def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed")

    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](_eval_node(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return BIN_OPS[type(node.op)](left, right)

    raise ValueError("Unsupported expression")

def calculate(expr: str):
    if not isinstance(expr, str):
        raise ValueError("Expression must be a string")
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty expression")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError("Invalid syntax") from e

    for n in ast.walk(tree):
        if not isinstance(n, ALLOWED_NODES):
            raise ValueError("Only basic arithmetic is allowed")

    return _eval_node(tree.body)

def main():
    while True:
        try:
            s = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if s.lower() in {"quit", "exit"}:
            break

        try:
            result = calculate(s)
        except ZeroDivisionError:
            print("Error: division by zero")
        except ValueError as e:
            print(f"Error: {e}")
        except OverflowError:
            print("Error: number too large")
        else:
            print(result)

if __name__ == "__main__":
    main()