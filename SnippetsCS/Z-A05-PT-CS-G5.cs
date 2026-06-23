using System;
using System.Globalization;

public static class Program
{
    public static void Main()
    {
        CultureInfo culture = CultureInfo.InvariantCulture;

        while (true)
        {
            Console.Write("Digite uma expressão (ou 'sair'): ");
            string? input = Console.ReadLine();

            if (input is null) return;

            input = input.Trim();
            if (input.Length == 0) continue;

            if (string.Equals(input, "sair", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(input, "exit", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(input, "quit", StringComparison.OrdinalIgnoreCase))
            {
                return;
            }

            try
            {
                var parser = new Parser(input, culture);
                double result = parser.ParseExpression();

                parser.SkipWhitespace();
                if (!parser.IsEnd)
                    throw new FormatException($"Token inesperado na posição {parser.Position}.");

                Console.WriteLine(result.ToString("G17", culture));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erro: {ex.Message}");
            }
        }
    }

    private sealed class Parser
    {
        private readonly string _s;
        private readonly CultureInfo _culture;
        private int _i;

        public Parser(string s, CultureInfo culture)
        {
            _s = s;
            _culture = culture;
            _i = 0;
        }

        public int Position => _i;
        public bool IsEnd => _i >= _s.Length;

        public void SkipWhitespace()
        {
            while (_i < _s.Length && char.IsWhiteSpace(_s[_i])) _i++;
        }

        public double ParseExpression()
        {
            // expression := term (('+'|'-') term)*
            double value = ParseTerm();
            while (true)
            {
                SkipWhitespace();
                if (Match('+'))
                {
                    value += ParseTerm();
                }
                else if (Match('-'))
                {
                    value -= ParseTerm();
                }
                else
                {
                    break;
                }
            }
            return value;
        }

        private double ParseTerm()
        {
            // term := factor (('*'|'/'|'%') factor)*
            double value = ParseFactor();
            while (true)
            {
                SkipWhitespace();
                if (Match('*'))
                {
                    value *= ParseFactor();
                }
                else if (Match('/'))
                {
                    double rhs = ParseFactor();
                    if (rhs == 0.0) throw new DivideByZeroException("Divisão por zero.");
                    value /= rhs;
                }
                else if (Match('%'))
                {
                    double rhs = ParseFactor();
                    if (rhs == 0.0) throw new DivideByZeroException("Módulo por zero.");
                    value %= rhs;
                }
                else
                {
                    break;
                }
            }
            return value;
        }

        private double ParseFactor()
        {
            // factor := unary ('^' factor)?   (right-associative)
            double left = ParseUnary();
            SkipWhitespace();
            if (Match('^'))
            {
                double right = ParseFactor();
                return Math.Pow(left, right);
            }
            return left;
        }

        private double ParseUnary()
        {
            // unary := ('+'|'-') unary | primary
            SkipWhitespace();
            if (Match('+')) return ParseUnary();
            if (Match('-')) return -ParseUnary();
            return ParsePrimary();
        }

        private double ParsePrimary()
        {
            // primary := number | '(' expression ')'
            SkipWhitespace();

            if (Match('('))
            {
                double value = ParseExpression();
                SkipWhitespace();
                if (!Match(')')) throw new FormatException("Faltando ')' .");
                return value;
            }

            return ParseNumber();
        }

        private double ParseNumber()
        {
            SkipWhitespace();
            int start = _i;

            bool sawDigit = false;

            while (_i < _s.Length && char.IsDigit(_s[_i]))
            {
                _i++;
                sawDigit = true;
            }

            if (_i < _s.Length && (_s[_i] == '.' || _s[_i] == ','))
            {
                _i++;
                while (_i < _s.Length && char.IsDigit(_s[_i]))
                {
                    _i++;
                    sawDigit = true;
                }
            }

            if (!sawDigit)
                throw new FormatException($"Número esperado na posição {start}.");

            if (_i < _s.Length && (_s[_i] == 'e' || _s[_i] == 'E'))
            {
                int ePos = _i;
                _i++;

                if (_i < _s.Length && (_s[_i] == '+' || _s[_i] == '-')) _i++;

                int expDigitsStart = _i;
                while (_i < _s.Length && char.IsDigit(_s[_i])) _i++;

                if (_i == expDigitsStart)
                    throw new FormatException($"Expoente inválido na posição {ePos}.");
            }

            string token = _s.Substring(start, _i - start).Replace(',', '.');
            if (!double.TryParse(token, NumberStyles.Float, _culture, out double value))
                throw new FormatException($"Número inválido: '{token}'.");

            return value;
        }

        private bool Match(char c)
        {
            SkipWhitespace();
            if (_i < _s.Length && _s[_i] == c)
            {
                _i++;
                return true;
            }
            return false;
        }
    }
}