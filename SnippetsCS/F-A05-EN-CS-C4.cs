using System;

class Calculator
{
    static void Main()
    {
        Console.WriteLine("=== Simple Calculator ===");
        Console.WriteLine("Enter a mathematical expression (e.g., 5 + 3 * 2):");
        
        string expression = Console.ReadLine();
        
        try
        {
            double result = EvaluateExpression(expression);
            Console.WriteLine($"Result: {result}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
    
    static double EvaluateExpression(string expression)
    {
        if (string.IsNullOrWhiteSpace(expression))
            throw new ArgumentException("Expression cannot be empty.");
        
        try
        {
            System.Data.DataTable table = new System.Data.DataTable();
            var result = table.Compute(expression, null);
            return Convert.ToDouble(result);
        }
        catch
        {
            throw new InvalidOperationException("Invalid mathematical expression.");
        }
    }
}