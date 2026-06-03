import requests
import json
from typing import Any

def fetch_and_process_data(api_url: str, params: dict = None) -> None:
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        processed_data = process_data(data)
        display_results(processed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError:
        print("Error decoding JSON response")

def process_data(data: Any) -> dict:
    if isinstance(data, list) and len(data) > 0:
        return {
            "count": len(data),
            "first_item": data[0],
            "sample": data[:3]
        }
    elif isinstance(data, dict):
        return {
            "keys": list(data.keys()),
            "data": data
        }
    return {"raw": data}

def display_results(processed: dict) -> None:
    print("\n" + "="*60)
    print("API Response Summary")
    print("="*60)
    for key, value in processed.items():
        if isinstance(value, (list, dict)):
            print(f"{key}:\n{json.dumps(value, indent=2)}")
        else:
            print(f"{key}: {value}")
    print("="*60 + "\n")

if __name__ == "__main__":
    api_endpoint = "https://jsonplaceholder.typicode.com/posts"
    fetch_and_process_data(api_endpoint, params={"_limit": 3})