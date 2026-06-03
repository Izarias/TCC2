using System;

class Calculadora
{
    static void Main()
    {
        Console.WriteLine("=== Calculadora Simples ===");
        Console.Write("Digite a expressão matemática: ");
        string expressao = Console.ReadLine();

        try
        {
            double resultado = CalcularExpressao(expressao);
            Console.WriteLine($"Resultado: {resultado}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro: Expressão inválida");
        }
    }

    static double CalcularExpressao(string expressao)
    {
        var dataTable = new System.Data.DataTable();
        return Convert.ToDouble(dataTable.Compute(expressao, null));
    }
}