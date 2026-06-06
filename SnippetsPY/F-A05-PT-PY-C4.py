def calculadora():
    try:
        expressao = input("Digite uma expressão matemática: ")
        resultado = eval(expressao)
        print(f"Resultado: {resultado}")
        return resultado
    except ZeroDivisionError:
        print("Erro: Divisão por zero não permitida.")
    except SyntaxError:
        print("Erro: Expressão matemática inválida.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    calculadora()