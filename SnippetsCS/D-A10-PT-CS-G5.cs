using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

public static class Program
{
    private static readonly HttpClient Http = new HttpClient
    {
        Timeout = TimeSpan.FromSeconds(20)
    };

    public static async Task Main()
    {
        try
        {
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(20));

            var baseUrl = "https://api.exchangerate.host";
            var symbols = new[] { "USD", "EUR", "BRL", "GBP" };
            var baseCurrency = "USD";

            var url =
                $"{baseUrl}/latest?base={Uri.EscapeDataString(baseCurrency)}&symbols={Uri.EscapeDataString(string.Join(",", symbols))}";

            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.UserAgent.ParseAdd("ApiClientExample/1.0");

            using var response = await Http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cts.Token);
            response.EnsureSuccessStatusCode();

            await using var stream = await response.Content.ReadAsStreamAsync(cts.Token);

            var jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var payload = await JsonSerializer.DeserializeAsync<ExchangeLatestResponse>(stream, jsonOptions, cts.Token)
                          ?? throw new InvalidOperationException("Resposta JSON vazia ou inválida.");

            if (payload.Rates is null || payload.Rates.Count == 0)
                throw new InvalidOperationException("Nenhuma taxa de câmbio foi retornada pela API.");

            var processed = ProcessRates(payload, baseCurrency);

            PrintResult(processed);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Operação cancelada (timeout).");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Falha HTTP: {ex.Message}");
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"Falha ao interpretar JSON: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro: {ex.Message}");
        }
    }

    private static ProcessedRates ProcessRates(ExchangeLatestResponse payload, string baseCurrency)
    {
        var baseToTargets = payload.Rates!
            .Where(kvp => !string.IsNullOrWhiteSpace(kvp.Key))
            .ToDictionary(kvp => kvp.Key.Trim().ToUpperInvariant(), kvp => kvp.Value);

        var targetsToBase = baseToTargets
            .Where(kvp => kvp.Value > 0)
            .ToDictionary(kvp => kvp.Key, kvp => 1m / kvp.Value);

        var top = baseToTargets
            .OrderByDescending(kvp => kvp.Value)
            .Take(3)
            .Select(kvp => (Currency: kvp.Key, Rate: kvp.Value))
            .ToList();

        return new ProcessedRates(
            BaseCurrency: baseCurrency.ToUpperInvariant(),
            Date: payload.Date ?? "(sem data)",
            BaseToTargets: baseToTargets,
            TargetsToBase: targetsToBase,
            TopByValue: top
        );
    }

    private static void PrintResult(ProcessedRates data)
    {
        Console.WriteLine($"Taxas de câmbio (base: {data.BaseCurrency}) — data: {data.Date}");
        Console.WriteLine(new string('-', 60));

        var culture = CultureInfo.InvariantCulture;

        foreach (var (currency, rate) in data.BaseToTargets.OrderBy(kvp => kvp.Key))
        {
            var inverse = data.TargetsToBase.TryGetValue(currency, out var inv) ? inv : 0m;
            var inverseText = inverse > 0 ? inverse.ToString("0.######", culture) : "n/d";

            Console.WriteLine($"1 {data.BaseCurrency} = {rate.ToString("0.######", culture)} {currency} | 1 {currency} = {inverseText} {data.BaseCurrency}");
        }

        Console.WriteLine();
        Console.WriteLine("Top 3 (maior valor por 1 unidade da base):");
        foreach (var item in data.TopByValue)
            Console.WriteLine($"- {item.Currency}: {item.Rate.ToString("0.######", culture)}");

        Console.WriteLine();
        Console.WriteLine("Concluído.");
    }

    private sealed record ExchangeLatestResponse
    {
        [JsonPropertyName("base")]
        public string? Base { get; init; }

        [JsonPropertyName("date")]
        public string? Date { get; init; }

        [JsonPropertyName("rates")]
        public Dictionary<string, decimal>? Rates { get; init; }
    }

    private sealed record ProcessedRates(
        string BaseCurrency,
        string Date,
        Dictionary<string, decimal> BaseToTargets,
        Dictionary<string, decimal> TargetsToBase,
        List<(string Currency, decimal Rate)> TopByValue
    );
}