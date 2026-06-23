using System;
using System.Globalization;

public static class Program
{
    public static int Main()
    {
        Console.Write("Enter expression: ");
        var input = Console.ReadLine();

        if (string.IsNullOrWhiteSpace(input))
        {
            Console.Error.WriteLine("No expression provided.");
            return 1;
        }

        try
        {
            var result = ExpressionEvaluator.Evaluate(input);
            Console.WriteLine(result.ToString(CultureInfo.InvariantCulture));
            return 0;
        }
        catch (DivideByZeroException)
        {
            Console.Error.WriteLine("Invalid expression: division by zero.");
            return 2;
        }
        catch (OverflowException)
        {
            Console.Error.WriteLine("Invalid expression: number too large.");
            return 2;
        }
        catch (FormatException ex)
        {
            Console.Error.WriteLine("Invalid expression: " + ex.Message);
            return 2;
        }
    }

    private sealed class ExpressionEvaluator
    {
        private readonly string _s;
        private int _i;

        private ExpressionEvaluator(string s) => _s = s ?? string.Empty;

        public static decimal Evaluate(string expression)
        {
            var p = new ExpressionEvaluator(expression);
            var value = p.ParseExpression();
            p.SkipWhite();
            if (!p.IsEnd())
                throw new FormatException($"Unexpected character '{p.Peek()}' at position {p._i + 1}.");
            return value;
        }

        // Grammar:
        // expression := term (('+'|'-') term)*
        // term       := factor (('*'|'/') factor)*
        // factor     := ('+'|'-') factor | primary
        // primary    := number | '(' expression ')'

        private decimal ParseExpression()
        {
            var value = ParseTerm();
            while (true)
            {
                SkipWhite();
                if (Match('+')) value += ParseTerm();
                else if (Match('-')) value -= ParseTerm();
                else break;
            }
            return value;
        }

        private decimal ParseTerm()
        {
            var value = ParseFactor();
            while (true)
            {
                SkipWhite();
                if (Match('*')) value *= ParseFactor();
                else if (Match('/'))
                {
                    var divisor = ParseFactor();
                    if (divisor == 0m) throw new DivideByZeroException();
                    value /= divisor;
                }
                else break;
            }
            return value;
        }

        private decimal ParseFactor()
        {
            SkipWhite();
            if (Match('+')) return ParseFactor();
            if (Match('-')) return -ParseFactor();
            return ParsePrimary();
        }

        private decimal ParsePrimary()
        {
            SkipWhite();

            if (Match('('))
            {
                var value = ParseExpression();
                SkipWhite();
                if (!Match(')'))
                    throw new FormatException($"Missing ')' at position {Math.Min(_i + 1, _s.Length + 1)}.");
                return value;
            }

            return ParseNumber();
        }

        private decimal ParseNumber()
        {
            SkipWhite();

            int start = _i;
            bool hasDigits = false;

            while (!IsEnd() && char.IsDigit(Peek()))
            {
                hasDigits = true;
                _i++;
            }

            if (!IsEnd() && (Peek() == '.' || Peek() == ','))
            {
                _i++;
                while (!IsEnd() && char.IsDigit(Peek()))
                {
                    hasDigits = true;
                    _i++;
                }
            }

            if (!hasDigits)
            {
                if (IsEnd()) throw new FormatException("Unexpected end of input.");
                throw new FormatException($"Expected a number at position {start + 1}, found '{Peek()}'.");
            }

            var token = _s.Substring(start, _i - start).Replace(',', '.');
            return decimal.Parse(token, NumberStyles.Number, CultureInfo.InvariantCulture);
        }

        private void SkipWhite()
        {
            while (!IsEnd() && char.IsWhiteSpace(Peek())) _i++;
        }

        private bool Match(char ch)
        {
            if (!IsEnd() && Peek() == ch)
            {
                _i++;
                return true;
            }
            return false;
        }

        private char Peek() => _i < _s.Length ? _s[_i] : '\0';
        private bool IsEnd() => _i >= _s.Length;
    }
}