// Program.cs
// dotnet run -- https://api.github.com/repos/dotnet/runtime
// Optional: set env var API_BEARER_TOKEN for authenticated requests.

using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Serialization;

var cts = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

var url = args.Length > 0 ? args[0] : "https://api.github.com/repos/dotnet/runtime";

try
{
    using var api = new ApiClient(
        bearerToken: Environment.GetEnvironmentVariable("API_BEARER_TOKEN"),
        timeout: TimeSpan.FromSeconds(30));

    var repo = await api.GetJsonAsync<GithubRepo>(url, cts.Token);

    Console.WriteLine($"Name        : {repo.FullName}");
    Console.WriteLine($"Description : {repo.Description}");
    Console.WriteLine($"Stars       : {repo.StargazersCount:N0}");
    Console.WriteLine($"Forks       : {repo.ForksCount:N0}");
    Console.WriteLine($"Open Issues : {repo.OpenIssuesCount:N0}");
    Console.WriteLine($"URL         : {repo.HtmlUrl}");
}
catch (OperationCanceledException)
{
    Console.Error.WriteLine("Request canceled.");
    Environment.ExitCode = 1;
}
catch (ApiException ex)
{
    Console.Error.WriteLine($"API error ({(int)ex.StatusCode} {ex.StatusCode}): {ex.Message}");
    if (!string.IsNullOrWhiteSpace(ex.Body))
    {
        Console.Error.WriteLine("---- Response body ----");
        Console.Error.WriteLine(ex.Body);
    }
    Environment.ExitCode = 1;
}
catch (Exception ex)
{
    Console.Error.WriteLine($"Unexpected error: {ex.Message}");
    Environment.ExitCode = 1;
}

sealed class ApiClient : IDisposable
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        NumberHandling = JsonNumberHandling.AllowReadingFromString
    };

    private readonly HttpClient _http;

    public ApiClient(string? bearerToken, TimeSpan timeout)
    {
        var handler = new SocketsHttpHandler
        {
            PooledConnectionLifetime = TimeSpan.FromMinutes(10),
            AutomaticDecompression = System.Net.DecompressionMethods.GZip | System.Net.DecompressionMethods.Deflate
        };

        _http = new HttpClient(handler)
        {
            Timeout = timeout
        };

        // Some public APIs (e.g., GitHub) require a User-Agent.
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("ApiClientSample/1.0");

        if (!string.IsNullOrWhiteSpace(bearerToken))
        {
            _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", bearerToken);
        }

        _http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
    }

    public async Task<T> GetJsonAsync<T>(string url, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, url);
        using var response = await _http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        var body = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            throw new ApiException(response.StatusCode, $"Request to '{url}' failed.", body);
        }

        try
        {
            var result = JsonSerializer.Deserialize<T>(body, JsonOptions);
            if (result is null)
                throw new ApiException(response.StatusCode, "Response JSON was empty or invalid.", body);

            return result;
        }
        catch (JsonException je)
        {
            throw new ApiException(response.StatusCode, $"Failed to parse JSON: {je.Message}", body);
        }
    }

    public void Dispose() => _http.Dispose();
}

sealed class ApiException : Exception
{
    public System.Net.HttpStatusCode StatusCode { get; }
    public string? Body { get; }

    public ApiException(System.Net.HttpStatusCode statusCode, string message, string? body)
        : base(message)
    {
        StatusCode = statusCode;
        Body = body;
    }
}

sealed record GithubRepo(
    [property: JsonPropertyName("full_name")] string FullName,
    [property: JsonPropertyName("description")] string? Description,
    [property: JsonPropertyName("stargazers_count")] long StargazersCount,
    [property: JsonPropertyName("forks_count")] long ForksCount,
    [property: JsonPropertyName("open_issues_count")] long OpenIssuesCount,
    [property: JsonPropertyName("html_url")] string HtmlUrl
);