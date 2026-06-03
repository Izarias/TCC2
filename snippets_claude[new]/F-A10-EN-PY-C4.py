import requests
import json
from typing import Optional, Dict, Any

def query_external_api(
    endpoint: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Query an external API and return the parsed response.
    
    Args:
        endpoint: The API endpoint URL
        params: Optional query parameters
        headers: Optional request headers
        
    Returns:
        Parsed JSON response from the API
    """
    try:
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to query API: {str(e)}"}


def process_response(data: Dict[str, Any]) -> None:
    """
    Process and display the API response to the user.
    
    Args:
        data: The parsed API response
    """
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print("✓ API Response:")
    print(json.dumps(data, indent=2))


def main() -> None:
    """
    Main function to demonstrate API querying workflow.
    """
    endpoint = "https://jsonplaceholder.typicode.com/posts/1"
    
    print("Querying external API...")
    response_data = query_external_api(endpoint)
    process_response(response_data)


if __name__ == "__main__":
    main()