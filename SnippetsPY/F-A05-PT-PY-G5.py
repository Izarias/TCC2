import math

ALLOWED_NAMES = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
ALLOWED_NAMES.update({"abs": abs, "round": round})


def safe_eval(expr: str) -> float:
    if not expr or not expr.strip():
        raise ValueError("Expressão vazia.")

    expr = expr.replace("^", "**").strip()
    code = compile(expr, "<expressao>", "eval")

    for name in code.co_names:
        if name not in ALLOWED_NAMES:
            raise ValueError(f"Nome não permitido: {name}")

    return eval(code, {"__builtins__": {}}, ALLOWED_NAMES)


def main() -> None:
    print("Calculadora simples (digite 'sair' para encerrar)")
    print("Suporta: + - * / ** (ou ^), parênteses e funções do math (ex: sin, cos, sqrt, pi).")

    while True:
        expr = input("Expressão> ").strip()
        if expr.lower() in {"sair", "exit", "quit"}:
            break

        try:
            resultado = safe_eval(expr)
            print(resultado)
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    main()