using System;
using System.Data;

class Calculadora
{
    static void Main()
    {
        while (true)
        {
            Console.Write("Digite uma expressão (ou 'sair' para encerrar): ");
            string entrada = Console.ReadLine();
            
            if (entrada?.ToLower() == "sair")
                break;
            
            try
            {
                object resultado = new DataTable().Compute(entrada, null);
                Console.WriteLine($"Resultado: {resultado}\n");
            }
            catch
            {
                Console.WriteLine("Expressão inválida. Tente novamente.\n");
            }
        }
    }
}