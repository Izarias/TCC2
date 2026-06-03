import requests
import json
from typing import Dict, Any

def fetch_and_display_api_data(url: str, headers: Dict[str, str] = None) -> None:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        processed_data = process_data(data)
        display_results(processed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON")

def process_data(data: Any) -> Any:
    if isinstance(data, list):
        return data[:5]
    elif isinstance(data, dict):
        return {k: v for k, v in list(data.items())[:10]}
    return data

def display_results(data: Any) -> None:
    print("\n=== Resultados ===")
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            print(f"{i}. {item}")
    elif isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print(data)

if __name__ == "__main__":
    api_url = "https://jsonplaceholder.typicode.com/posts/1"
    fetch_and_display_api_data(api_url)