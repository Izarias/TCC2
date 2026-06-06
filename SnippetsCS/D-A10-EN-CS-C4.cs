using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.Json;

class Program
{
    static async Task Main()
    {
        var client = new HttpClient();
        
        try
        {
            var response = await client.GetAsync("https://jsonplaceholder.typicode.com/posts?_limit=5");
            response.EnsureSuccessStatusCode();
            
            var jsonContent = await response.Content.ReadAsStringAsync();
            var posts = JsonSerializer.Deserialize<List<Post>>(jsonContent);
            
            Console.WriteLine("=== Recent Posts ===\n");
            foreach (var post in posts)
            {
                Console.WriteLine($"[{post.Id}] {post.Title}");
                Console.WriteLine($"{post.Body}\n");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Request failed: {ex.Message}");
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"Failed to parse JSON: {ex.Message}");
        }
        finally
        {
            client.Dispose();
        }
    }
}

class Post
{
    public int UserId { get; set; }
    public int Id { get; set; }
    public string Title { get; set; }
    public string Body { get; set; }
}