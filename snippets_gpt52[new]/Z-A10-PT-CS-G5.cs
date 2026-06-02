using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

public sealed class Program
{
    private static readonly HttpClient Http = new HttpClient
    {
        Timeout = TimeSpan.FromSeconds(30)
    };

    public static async Task Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;

        var url = args.Length > 0 ? args[0] : "https://jsonplaceholder.typicode.com/posts/1";

        using var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.Accept.ParseAdd("application/json");

            using var resp = await Http.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, cts.Token);
            resp.EnsureSuccessStatusCode();

            await using var stream = await resp.Content.ReadAsStreamAsync(cts.Token);

            using var doc = await JsonDocument.ParseAsync(stream, cancellationToken: cts.Token);

            var pretty = JsonSerializer.Serialize(doc.RootElement, new JsonSerializerOptions { WriteIndented = true });

            Console.WriteLine("Resultado da API:");
            Console.WriteLine(pretty);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Operação cancelada.");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Erro HTTP: {ex.Message}");
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"Erro ao processar JSON: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro inesperado: {ex.Message}");
        }

        Console.WriteLine();
        Console.WriteLine("Pressione ENTER para sair...");
        Console.ReadLine();
    }
}