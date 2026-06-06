using System;

class Calculator
{
    static void Main()
    {
        while (true)
        {
            Console.Write("Enter expression (or 'exit' to quit): ");
            string input = Console.ReadLine();
            
            if (input.ToLower() == "exit")
                break;
            
            try
            {
                double result = Evaluate(input);
                Console.WriteLine($"Result: {result}\n");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}\n");
            }
        }
    }

    static double Evaluate(string expression)
    {
        if (string.IsNullOrWhiteSpace(expression))
            throw new ArgumentException("Expression cannot be empty");

        var parser = new ExpressionParser(expression.Replace(" ", ""));
        double result = parser.ParseExpression();
        
        if (parser.Position < parser.Expression.Length)
            throw new ArgumentException("Invalid expression");
            
        return result;
    }

    class ExpressionParser
    {
        public string Expression { get; }
        public int Position { get; set; }

        public ExpressionParser(string expression)
        {
            Expression = expression;
            Position = 0;
        }

        public double ParseExpression()
        {
            double result = ParseTerm();
            
            while (Position < Expression.Length && (Expression[Position] == '+' || Expression[Position] == '-'))
            {
                char op = Expression[Position++];
                double right = ParseTerm();
                result = op == '+' ? result + right : result - right;
            }
            
            return result;
        }

        double ParseTerm()
        {
            double result = ParseFactor();
            
            while (Position < Expression.Length && (Expression[Position] == '*' || Expression[Position] == '/'))
            {
                char op = Expression[Position++];
                double right = ParseFactor();
                
                if (op == '/' && right == 0)
                    throw new DivideByZeroException("Division by zero");
                    
                result = op == '*' ? result * right : result / right;
            }
            
            return result;
        }

        double ParseFactor()
        {
            if (Position >= Expression.Length)
                throw new ArgumentException("Unexpected end of expression");

            if (Expression[Position] == '(')
            {
                Position++;
                double result = ParseExpression();
                if (Position >= Expression.Length || Expression[Position] != ')')
                    throw new ArgumentException("Missing closing parenthesis");
                Position++;
                return result;
            }

            return ParseNumber();
        }

        double ParseNumber()
        {
            int start = Position;
            
            if (Position < Expression.Length && (Expression[Position] == '+' || Expression[Position] == '-'))
                Position++;

            bool hasDecimal = false;
            while (Position < Expression.Length && (char.IsDigit(Expression[Position]) || Expression[Position] == '.'))
            {
                if (Expression[Position] == '.')
                {
                    if (hasDecimal)
                        throw new ArgumentException("Invalid number");
                    hasDecimal = true;
                }
                Position++;
            }

            if (start == Position || (start + 1 == Position && (Expression[start] == '+' || Expression[start] == '-')))
                throw new ArgumentException("Invalid number");

            return double.Parse(Expression.Substring(start, Position - start));
        }
    }
}