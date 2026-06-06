using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;

        using var cts = CreateCancellation();
        var endpoint = GetEndpoint(args);

        try
        {
            var httpClient = HttpClientFactory.Create();

            var json = await ApiClient.GetJsonAsync(httpClient, endpoint, cts.Token);
            var output = JsonFormatter.PrettyPrint(json);

            Console.WriteLine("Resultado da API:");
            Console.WriteLine(output);
            return 0;
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Operação cancelada.");
            return 2;
        }
        catch (ApiException ex)
        {
            Console.WriteLine("Falha ao consultar a API.");
            Console.WriteLine($"Status: {(int?)ex.StatusCode ?? 0}");
            Console.WriteLine($"Mensagem: {ex.Message}");
            if (!string.IsNullOrWhiteSpace(ex.ResponseBody))
            {
                Console.WriteLine("Resposta:");
                Console.WriteLine(ex.ResponseBody);
            }
            return 1;
        }
        catch (Exception ex)
        {
            Console.WriteLine("Erro inesperado.");
            Console.WriteLine(ex.Message);
            return 1;
        }
        finally
        {
            Console.WriteLine();
            Console.WriteLine("Pressione ENTER para sair...");
            Console.ReadLine();
        }
    }

    private static CancellationTokenSource CreateCancellation()
    {
        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };
        return cts;
    }

    private static Uri GetEndpoint(string[] args)
    {
        var defaultUrl = "https://jsonplaceholder.typicode.com/posts/1";
        var url = args.Length > 0 ? args[0] : defaultUrl;

        if (!Uri.TryCreate(url, UriKind.Absolute, out var uri))
            throw new ArgumentException($"URL inválida: {url}");

        return uri;
    }
}

internal static class HttpClientFactory
{
    public static HttpClient Create()
    {
        var httpClient = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(30)
        };

        httpClient.DefaultRequestHeaders.Accept.Clear();
        httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("ApiConsoleClient/1.0");

        return httpClient;
    }
}

internal static class ApiClient
{
    public static async Task<string> GetJsonAsync(HttpClient httpClient, Uri endpoint, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, endpoint);

        using var response = await httpClient.SendAsync(
            request,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken
        );

        var body = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
            throw new ApiException($"A API retornou erro ({(int)response.StatusCode}).", response.StatusCode, body);

        if (string.IsNullOrWhiteSpace(body))
            throw new ApiException("A API retornou resposta vazia.", response.StatusCode, body);

        return body;
    }
}

internal static class JsonFormatter
{
    public static string PrettyPrint(string json)
    {
        using var doc = JsonDocument.Parse(json);
        return JsonSerializer.Serialize(doc.RootElement, new JsonSerializerOptions
        {
            WriteIndented = true
        });
    }
}

internal sealed class ApiException : Exception
{
    public System.Net.HttpStatusCode? StatusCode { get; }
    public string? ResponseBody { get; }

    public ApiException(string message, System.Net.HttpStatusCode? statusCode, string? responseBody, Exception? innerException = null)
        : base(message, innerException)
    {
        StatusCode = statusCode;
        ResponseBody = responseBody;
    }
}