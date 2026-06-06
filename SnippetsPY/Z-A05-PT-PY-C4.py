while True:
    expressao = input("Digite uma expressão matemática (ou 'sair' para encerrar): ")
    
    if expressao.lower() == 'sair':
        break
    
    try:
        resultado = eval(expressao)
        print(f"Resultado: {resultado}\n")
    except Exception as e:
        print(f"Erro: {e}\n")