using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Program
{
    private static readonly HttpClient client = new HttpClient();

    static async Task Main(string[] args)
    {
        await ConsultarAPIExterna();
    }

    static async Task ConsultarAPIExterna()
    {
        try
        {
            string url = "https://jsonplaceholder.typicode.com/posts/1";
            
            Console.WriteLine("Consultando API externa...\n");
            
            HttpResponseMessage resposta = await client.GetAsync(url);
            
            if (resposta.IsSuccessStatusCode)
            {
                string conteudo = await resposta.Content.ReadAsStringAsync();
                
                dynamic dados = JsonConvert.DeserializeObject(conteudo);
                
                ExibirResultado(dados);
            }
            else
            {
                Console.WriteLine($"Erro na requisição: {resposta.StatusCode}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Erro ao conectar à API: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro inesperado: {ex.Message}");
        }
    }

    static void ExibirResultado(dynamic dados)
    {
        Console.WriteLine("=== Resultado da Consulta ===\n");
        Console.WriteLine($"ID: {dados["id"]}");
        Console.WriteLine($"Usuário ID: {dados["userId"]}");
        Console.WriteLine($"Título: {dados["title"]}");
        Console.WriteLine($"Corpo: {dados["body"]}");
    }
}