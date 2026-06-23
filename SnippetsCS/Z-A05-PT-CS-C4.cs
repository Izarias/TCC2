using System;
using System.Data;

class Calculadora
{
    static void Main()
    {
        Console.WriteLine("=== Calculadora Simples ===");
        Console.WriteLine("Digite uma expressão matemática (ex: 10 + 5 * 2):");
        
        string expressao = Console.ReadLine();
        
        try
        {
            DataTable tabela = new DataTable();
            var resultado = tabela.Compute(expressao, null);
            Console.WriteLine($"Resultado: {resultado}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro: Expressão inválida. {ex.Message}");
        }
    }
}