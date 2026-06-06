import requests
import json

def consultar_api():
    """Consulta uma API externa e exibe os dados"""
    
    # URL de uma API pública (JSONPlaceholder - API de exemplo)
    url = "https://jsonplaceholder.typicode.com/posts/1"
    
    try:
        # Fazer requisição GET
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        
        # Obter dados em formato JSON
        dados = resposta.json()
        
        # Apresentar resultado ao usuário
        print("=== Resultado da API ===")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        
        return dados
    
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar à API")
    except requests.exceptions.Timeout:
        print("Erro: Timeout na requisição")
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP: {e.response.status_code}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    consultar_api()