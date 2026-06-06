import requests
import json

def query_api(url, headers=None, params=None):
    """
    Query an external API and return the response data.
    
    Args:
        url (str): The API endpoint URL
        headers (dict): Optional HTTP headers
        params (dict): Optional query parameters
    
    Returns:
        dict: The JSON response data
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}")
        return None

def display_results(data, title="API Results"):
    """
    Display the API results to the user in a formatted way.
    
    Args:
        data (dict): The data to display
        title (str): Title for the results
    """
    if data is None:
        print("No data to display.")
        return
    
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(json.dumps(data, indent=2))
    print(f"{'='*50}\n")

def main():
    # Example: Query the JSONPlaceholder API
    api_url = "https://jsonplaceholder.typicode.com/users/1"
    
    print("Fetching data from API...")
    data = query_api(api_url)
    
    if data:
        display_results(data, "User Information")
        
        # Access specific fields
        print(f"Name: {data.get('name')}")
        print(f"Email: {data.get('email')}")
        print(f"Phone: {data.get('phone')}")

if __name__ == "__main__":
    main()