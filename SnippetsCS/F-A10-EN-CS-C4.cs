using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class ApiClient
{
    private readonly HttpClient _httpClient;
    private readonly string _apiUrl;

    public ApiClient(string apiUrl)
    {
        _apiUrl = apiUrl;
        _httpClient = new HttpClient();
    }

    public async Task<T> QueryApiAsync<T>(string endpoint)
    {
        try
        {
            string url = $"{_apiUrl}/{endpoint}";
            HttpResponseMessage response = await _httpClient.GetAsync(url);

            if (!response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Error: API returned status {response.StatusCode}");
                return default;
            }

            string content = await response.Content.ReadAsStringAsync();
            T data = JsonConvert.DeserializeObject<T>(content);

            return data;
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Request error: {ex.Message}");
            return default;
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"JSON parsing error: {ex.Message}");
            return default;
        }
    }

    public void DisplayResult<T>(T data)
    {
        if (data == null)
        {
            Console.WriteLine("No data retrieved.");
            return;
        }

        Console.WriteLine("=== API Response ===");
        string jsonOutput = JsonConvert.SerializeObject(data, Formatting.Indented);
        Console.WriteLine(jsonOutput);
    }
}

public class Program
{
    public static async Task Main(string[] args)
    {
        ApiClient client = new ApiClient("https://jsonplaceholder.typicode.com");

        dynamic result = await client.QueryApiAsync<dynamic>("posts/1");
        client.DisplayResult(result);
    }
}