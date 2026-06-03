using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

static class Program
{
    private static readonly HttpClient Http = new()
    {
        Timeout = TimeSpan.FromSeconds(20)
    };

    public static async Task Main()
    {
        // Example external API (public): https://jsonplaceholder.typicode.com/todos/1
        var url = "https://jsonplaceholder.typicode.com/todos/1";

        using var cts = new CancellationTokenSource();

        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        try
        {
            Http.DefaultRequestHeaders.Accept.Clear();
            Http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            using var response = await Http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cts.Token);
            response.EnsureSuccessStatusCode();

            await using var stream = await response.Content.ReadAsStreamAsync(cts.Token);
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var todo = await JsonSerializer.DeserializeAsync<Todo>(stream, options, cts.Token);

            if (todo is null)
            {
                Console.WriteLine("API returned no data.");
                return;
            }

            Console.WriteLine("API result:");
            Console.WriteLine($"- UserId  : {todo.UserId}");
            Console.WriteLine($"- Id      : {todo.Id}");
            Console.WriteLine($"- Title   : {todo.Title}");
            Console.WriteLine($"- Completed: {todo.Completed}");
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Request canceled.");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"HTTP error: {ex.Message}");
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"JSON parse error: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Unexpected error: {ex.Message}");
        }
    }

    private sealed record Todo(int UserId, int Id, string Title, bool Completed);
}