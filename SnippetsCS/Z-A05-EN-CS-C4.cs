using System;
using System.Data;

class Calculator
{
    static void Main()
    {
        Console.WriteLine("Simple Calculator");
        Console.WriteLine("Enter a mathematical expression (e.g., 2+3*4, 10/2-1):");
        
        string expression = Console.ReadLine();
        
        try
        {
            DataTable dt = new DataTable();
            var result = dt.Compute(expression, null);
            Console.WriteLine($"Result: {result}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}