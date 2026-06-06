using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Program
{
    static async Task Main(string[] args)
    {
        await ConsultarApiExterna();
    }

    static async Task ConsultarApiExterna()
    {
        using (HttpClient client = new HttpClient())
        {
            try
            {
                string url = "https://jsonplaceholder.typicode.com/posts/1";
                
                HttpResponseMessage resposta = await client.GetAsync(url);
                
                if (resposta.IsSuccessStatusCode)
                {
                    string conteudo = await resposta.Content.ReadAsStringAsync();
                    
                    Post post = JsonConvert.DeserializeObject<Post>(conteudo);
                    
                    ExibirResultado(post);
                }
                else
                {
                    Console.WriteLine($"Erro na requisição: {resposta.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erro ao consultar API: {ex.Message}");
            }
        }
    }

    static void ExibirResultado(Post post)
    {
        Console.WriteLine("=== Resultado da Consulta ===");
        Console.WriteLine($"ID: {post.Id}");
        Console.WriteLine($"Usuário ID: {post.UserId}");
        Console.WriteLine($"Título: {post.Title}");
        Console.WriteLine($"Corpo: {post.Body}");
    }
}

class Post
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