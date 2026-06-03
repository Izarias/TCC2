using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Program
{
    static async Task Main(string[] args)
    {
        await ConsultarAPI();
    }

    static async Task ConsultarAPI()
    {
        using (HttpClient client = new HttpClient())
        {
            try
            {
                // URL da API (exemplo: JSONPlaceholder)
                string url = "https://jsonplaceholder.typicode.com/users/1";

                // Realizar requisição GET
                HttpResponseMessage response = await client.GetAsync(url);

                // Verificar se a requisição foi bem-sucedida
                if (response.IsSuccessStatusCode)
                {
                    // Obter o conteúdo da resposta
                    string conteudo = await response.Content.ReadAsStringAsync();

                    // Desserializar JSON (opcional)
                    var usuario = JsonConvert.DeserializeObject<Usuario>(conteudo);

                    // Apresentar resultado ao usuário
                    Console.WriteLine("=== Dados Obtidos ===");
                    Console.WriteLine($"ID: {usuario.Id}");
                    Console.WriteLine($"Nome: {usuario.Name}");
                    Console.WriteLine($"Email: {usuario.Email}");
                    Console.WriteLine($"Telefone: {usuario.Phone}");
                    Console.WriteLine($"Website: {usuario.Website}");
                }
                else
                {
                    Console.WriteLine($"Erro na requisição: {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erro ao consultar API: {ex.Message}");
            }
        }
    }
}

// Classe para desserializar os dados JSON
public class Usuario
{
    [JsonProperty("id")]
    public int Id { get; set; }

    [JsonProperty("name")]
    public string Name { get; set; }

    [JsonProperty("email")]
    public string Email { get; set; }

    [JsonProperty("phone")]
    public string Phone { get; set; }

    [JsonProperty("website")]
    public string Website { get; set; }
}