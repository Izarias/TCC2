import requests
import json
from typing import Dict, Any

def consultar_api_externa(url: str) -> Dict[str, Any]:
    """
    Consulta uma API externa e retorna os dados obtidos.
    
    Args:
        url: URL da API a ser consultada
        
    Returns:
        Dados retornados pela API em formato de dicionário
        
    Raises:
        requests.exceptions.RequestException: Erro na requisição
    """
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        
        dados = resposta.json()
        return dados
        
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar à API.")
        return {}
    except requests.exceptions.Timeout:
        print("Erro: Requisição expirou.")
        return {}
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP: {e.response.status_code}")
        return {}
    except json.JSONDecodeError:
        print("Erro: Resposta não é JSON válido.")
        return {}

def exibir_resultado(dados: Dict[str, Any]) -> None:
    """
    Exibe os dados obtidos da API de forma formatada.
    
    Args:
        dados: Dicionário contendo os dados da API
    """
    if not dados:
        print("Nenhum dado para exibir.")
        return
    
    print("\n=== Resultado da Consulta ===\n")
    print(json.dumps(dados, indent=2, ensure_ascii=False))
    print("\n" + "="*28)

def main():
    """Função principal que orquestra a consulta e exibição dos dados."""
    url = "https://jsonplaceholder.typicode.com/posts/1"
    
    print("Consultando API...")
    dados = consultar_api_externa(url)
    exibir_resultado(dados)

if __name__ == "__main__":
    main()