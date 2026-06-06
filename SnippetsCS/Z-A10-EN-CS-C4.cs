using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Program
{
    static async Task Main(string[] args)
    {
        await QueryApiAndDisplayResult();
    }

    static async Task QueryApiAndDisplayResult()
    {
        using (HttpClient client = new HttpClient())
        {
            try
            {
                // Query the API
                string apiUrl = "https://jsonplaceholder.typicode.com/posts/1";
                HttpResponseMessage response = await client.GetAsync(apiUrl);

                // Check if request was successful
                if (response.IsSuccessStatusCode)
                {
                    // Get the response content
                    string jsonContent = await response.Content.ReadAsStringAsync();

                    // Deserialize JSON to object
                    var post = JsonConvert.DeserializeObject<Post>(jsonContent);

                    // Present result to user
                    Console.WriteLine("=== API Response ===");
                    Console.WriteLine($"User ID: {post.UserId}");
                    Console.WriteLine($"ID: {post.Id}");
                    Console.WriteLine($"Title: {post.Title}");
                    Console.WriteLine($"Body: {post.Body}");
                }
                else
                {
                    Console.WriteLine($"Error: {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception: {ex.Message}");
            }
        }
    }
}

public class Post
{
    [JsonProperty("userId")]
    public int UserId { get; set; }

    [JsonProperty("id")]
    public int Id { get; set; }

    [JsonProperty("title")]
    public string Title { get; set; }

    [JsonProperty("body")]
    public string Body { get; set; }
}