using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

var cts = new CancellationTokenSource(TimeSpan.FromSeconds(20));
var token = cts.Token;

const string owner = "dotnet";
const string repo = "runtime";
var url = $"https://api.github.com/repos/{owner}/{repo}";

using var http = new HttpClient();
http.DefaultRequestHeaders.UserAgent.ParseAdd("LeanApiClient/1.0");
http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));

try
{
    using var resp = await http.GetAsync(url, token);
    resp.EnsureSuccessStatusCode();

    await using var stream = await resp.Content.ReadAsStreamAsync(token);
    var data = await JsonSerializer.DeserializeAsync<GitHubRepo>(stream, JsonOptions, token);

    if (data is null)
    {
        Console.WriteLine("No data returned.");
        return;
    }

    var popularity = data.Stars + data.Forks;
    var issuesStatus = data.OpenIssues == 0 ? "No open issues" : $"{data.OpenIssues} open issues";

    Console.WriteLine($"Repository: {data.FullName}");
    Console.WriteLine($"Description: {data.Description ?? "(none)"}");
    Console.WriteLine($"Stars: {data.Stars:N0} | Forks: {data.Forks:N0} | Popularity: {popularity:N0}");
    Console.WriteLine(issuesStatus);
    Console.WriteLine($"Last updated (UTC): {data.UpdatedAt:yyyy-MM-dd HH:mm:ss}");
}
catch (OperationCanceledException)
{
    Console.WriteLine("Request timed out.");
}
catch (HttpRequestException ex)
{
    Console.WriteLine($"HTTP error: {ex.Message}");
}
catch (JsonException ex)
{
    Console.WriteLine($"JSON parse error: {ex.Message}");
}

static readonly JsonSerializerOptions JsonOptions = new()
{
    PropertyNameCaseInsensitive = true
};

sealed record GitHubRepo(
    [property: JsonPropertyName("full_name")] string FullName,
    [property: JsonPropertyName("description")] string? Description,
    [property: JsonPropertyName("stargazers_count")] int Stars,
    [property: JsonPropertyName("forks_count")] int Forks,
    [property: JsonPropertyName("open_issues_count")] int OpenIssues,
    [property: JsonPropertyName("updated_at")] DateTimeOffset UpdatedAt
);