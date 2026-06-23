import re

def calculadora():
    while True:
        try:
            expressao = input("Digite uma expressão (ou 'sair' para encerrar): ").strip()
            
            if expressao.lower() == 'sair':
                print("Encerrando...")
                break
            
            if not expressao:
                print("Entrada vazia. Tente novamente.")
                continue
            
            if not re.match(r'^[\d\s+\-*/%()\.]+$', expressao):
                print("Entrada inválida. Use apenas números, operadores e parênteses.")
                continue
            
            resultado = eval(expressao)
            print(f"Resultado: {resultado}\n")
        
        except ZeroDivisionError:
            print("Erro: Divisão por zero.\n")
        except SyntaxError:
            print("Erro: Expressão matemática inválida.\n")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}\n")

if __name__ == "__main__":
    calculadora()