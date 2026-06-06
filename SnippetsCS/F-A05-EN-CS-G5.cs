using System;
using System.Collections.Generic;
using System.Globalization;

public static class Program
{
    public static void Main()
    {
        while (true)
        {
            Console.Write("Expression (blank to exit): ");
            var input = Console.ReadLine();
            if (input is null) return;

            input = input.Trim();
            if (input.Length == 0) return;

            try
            {
                double result = ExpressionEvaluator.Evaluate(input);
                Console.WriteLine(result.ToString("G17", CultureInfo.InvariantCulture));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}

public static class ExpressionEvaluator
{
    public static double Evaluate(string expression)
    {
        if (expression is null) throw new ArgumentNullException(nameof(expression));

        var tokenizer = new Tokenizer(expression);
        var parser = new Parser(tokenizer);
        double value = parser.ParseExpression();

        if (tokenizer.Current.Kind != TokenKind.End)
            throw new FormatException($"Unexpected token '{tokenizer.Current.Lexeme}' at position {tokenizer.Current.Position}.");

        if (double.IsNaN(value) || double.IsInfinity(value))
            throw new ArithmeticException("Result is not a finite number.");

        return value;
    }

    private enum TokenKind
    {
        Number,
        Plus,
        Minus,
        Multiply,
        Divide,
        LParen,
        RParen,
        End
    }

    private readonly struct Token
    {
        public Token(TokenKind kind, string lexeme, int position, double numberValue = 0)
        {
            Kind = kind;
            Lexeme = lexeme;
            Position = position;
            NumberValue = numberValue;
        }

        public TokenKind Kind { get; }
        public string Lexeme { get; }
        public int Position { get; }
        public double NumberValue { get; }
    }

    private sealed class Tokenizer
    {
        private readonly string _s;
        private int _i;

        public Tokenizer(string s)
        {
            _s = s;
            _i = 0;
            Current = NextToken();
        }

        public Token Current { get; private set; }

        public void Advance() => Current = NextToken();

        private Token NextToken()
        {
            SkipWhitespace();
            if (_i >= _s.Length) return new Token(TokenKind.End, string.Empty, _i);

            int start = _i;
            char c = _s[_i];

            switch (c)
            {
                case '+': _i++; return new Token(TokenKind.Plus, "+", start);
                case '-': _i++; return new Token(TokenKind.Minus, "-", start);
                case '*': _i++; return new Token(TokenKind.Multiply, "*", start);
                case '/': _i++; return new Token(TokenKind.Divide, "/", start);
                case '(': _i++; return new Token(TokenKind.LParen, "(", start);
                case ')': _i++; return new Token(TokenKind.RParen, ")", start);
            }

            if (IsDigit(c) || c == '.' || c == ',')
            {
                var lexeme = ReadNumberLexeme();
                var normalized = NormalizeNumber(lexeme);

                if (!double.TryParse(normalized, NumberStyles.Float, CultureInfo.InvariantCulture, out var value))
                    throw new FormatException($"Invalid number '{lexeme}' at position {start}.");

                if (double.IsNaN(value) || double.IsInfinity(value))
                    throw new FormatException($"Invalid number '{lexeme}' at position {start}.");

                return new Token(TokenKind.Number, lexeme, start, value);
            }

            throw new FormatException($"Unexpected character '{c}' at position {start}.");
        }

        private void SkipWhitespace()
        {
            while (_i < _s.Length && char.IsWhiteSpace(_s[_i])) _i++;
        }

        private static bool IsDigit(char ch) => ch >= '0' && ch <= '9';

        private string ReadNumberLexeme()
        {
            int start = _i;
            bool seenDotOrComma = false;
            bool seenExp = false;

            while (_i < _s.Length)
            {
                char ch = _s[_i];

                if (IsDigit(ch))
                {
                    _i++;
                    continue;
                }

                if ((ch == '.' || ch == ',') && !seenDotOrComma && !seenExp)
                {
                    seenDotOrComma = true;
                    _i++;
                    continue;
                }

                if ((ch == 'e' || ch == 'E') && !seenExp)
                {
                    seenExp = true;
                    _i++;
                    if (_i < _s.Length && (_s[_i] == '+' || _s[_i] == '-')) _i++;
                    continue;
                }

                break;
            }

            return _s.Substring(start, _i - start);
        }

        private static string NormalizeNumber(string lexeme)
        {
            // Accept either '.' or ',' as decimal separator (single occurrence).
            // Always parse using InvariantCulture.
            if (lexeme.IndexOf(',') >= 0 && lexeme.IndexOf('.') < 0)
                return lexeme.Replace(',', '.');

            return lexeme;
        }
    }

    private sealed class Parser
    {
        private readonly Tokenizer _t;

        public Parser(Tokenizer t) => _t = t;

        public double ParseExpression()
        {
            double left = ParseTerm();

            while (_t.Current.Kind is TokenKind.Plus or TokenKind.Minus)
            {
                var op = _t.Current.Kind;
                _t.Advance();
                double right = ParseTerm();
                left = op == TokenKind.Plus ? left + right : left - right;
            }

            return left;
        }

        private double ParseTerm()
        {
            double left = ParseFactor();

            while (_t.Current.Kind is TokenKind.Multiply or TokenKind.Divide)
            {
                var op = _t.Current.Kind;
                _t.Advance();
                double right = ParseFactor();

                if (op == TokenKind.Multiply)
                {
                    left *= right;
                }
                else
                {
                    if (right == 0) throw new DivideByZeroException("Division by zero.");
                    left /= right;
                }
            }

            return left;
        }

        private double ParseFactor()
        {
            // Unary +/-
            if (_t.Current.Kind == TokenKind.Plus)
            {
                _t.Advance();
                return ParseFactor();
            }

            if (_t.Current.Kind == TokenKind.Minus)
            {
                _t.Advance();
                return -ParseFactor();
            }

            return ParsePrimary();
        }

        private double ParsePrimary()
        {
            if (_t.Current.Kind == TokenKind.Number)
            {
                double value = _t.Current.NumberValue;
                _t.Advance();
                return value;
            }

            if (_t.Current.Kind == TokenKind.LParen)
            {
                _t.Advance();
                double value = ParseExpression();
                Expect(TokenKind.RParen, "Missing closing ')'.");
                _t.Advance();
                return value;
            }

            throw new FormatException($"Expected a number or '(' at position {_t.Current.Position}.");
        }

        private void Expect(TokenKind kind, string message)
        {
            if (_t.Current.Kind != kind) throw new FormatException(message);
        }
    }
}