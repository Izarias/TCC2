using System;
using System.Globalization;

var input = Console.ReadLine();

if (string.IsNullOrWhiteSpace(input))
    return;

try
{
    var parser = new ExpressionParser(input);
    double result = parser.Parse();

    Console.WriteLine(result.ToString("G17", CultureInfo.InvariantCulture));
}
catch (Exception ex)
{
    Console.Error.WriteLine($"Erro: {ex.Message}");
    Environment.ExitCode = 1;
}

enum TokenType
{
    Number,
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
    End
}

readonly record struct Token(TokenType Type, double NumberValue = 0, int Position = 0);

sealed class ExpressionParser
{
    private readonly string _text;
    private int _index;

    private Token _current;

    public ExpressionParser(string text)
    {
        _text = text ?? string.Empty;
        _index = 0;
        _current = NextToken();
    }

    public double Parse()
    {
        var value = ParseExpression();
        Expect(TokenType.End);
        return value;
    }

    private double ParseExpression()
    {
        double left = ParseTerm();

        while (_current.Type is TokenType.Plus or TokenType.Minus)
        {
            var op = _current.Type;
            _current = NextToken();
            double right = ParseTerm();
            left = op == TokenType.Plus ? left + right : left - right;
        }

        return left;
    }

    private double ParseTerm()
    {
        double left = ParseUnary();

        while (_current.Type is TokenType.Star or TokenType.Slash)
        {
            var op = _current.Type;
            _current = NextToken();
            double right = ParseUnary();

            if (op == TokenType.Star)
            {
                left *= right;
            }
            else
            {
                if (right == 0)
                    throw new DivideByZeroException("Divisão por zero.");

                left /= right;
            }
        }

        return left;
    }

    private double ParseUnary()
    {
        if (_current.Type == TokenType.Plus)
        {
            _current = NextToken();
            return ParseUnary();
        }

        if (_current.Type == TokenType.Minus)
        {
            _current = NextToken();
            return -ParseUnary();
        }

        return ParsePrimary();
    }

    private double ParsePrimary()
    {
        if (_current.Type == TokenType.Number)
        {
            double value = _current.NumberValue;
            _current = NextToken();
            return value;
        }

        if (_current.Type == TokenType.LParen)
        {
            _current = NextToken();
            double value = ParseExpression();
            Expect(TokenType.RParen);
            return value;
        }

        throw new FormatException($"Token inesperado na posição {_current.Position}.");
    }

    private void Expect(TokenType type)
    {
        if (_current.Type != type)
            throw new FormatException($"Esperado '{type}', encontrado '{_current.Type}' na posição {_current.Position}.");

        _current = NextToken();
    }

    private Token NextToken()
    {
        SkipWhitespace();

        if (_index >= _text.Length)
            return new Token(TokenType.End, Position: _index);

        int pos = _index;
        char c = _text[_index];

        switch (c)
        {
            case '+': _index++; return new Token(TokenType.Plus, Position: pos);
            case '-': _index++; return new Token(TokenType.Minus, Position: pos);
            case '*': _index++; return new Token(TokenType.Star, Position: pos);
            case '/': _index++; return new Token(TokenType.Slash, Position: pos);
            case '(': _index++; return new Token(TokenType.LParen, Position: pos);
            case ')': _index++; return new Token(TokenType.RParen, Position: pos);
        }

        if (char.IsDigit(c) || c == '.' || c == ',')
            return ReadNumber();

        throw new FormatException($"Caractere inválido '{c}' na posição {pos}.");
    }

    private Token ReadNumber()
    {
        int start = _index;
        bool seenSeparator = false;

        while (_index < _text.Length)
        {
            char ch = _text[_index];

            if (char.IsDigit(ch))
            {
                _index++;
                continue;
            }

            if (ch == '.' || ch == ',')
            {
                if (seenSeparator)
                    break;

                seenSeparator = true;
                _index++;
                continue;
            }

            break;
        }

        string raw = _text.Substring(start, _index - start).Trim();
        if (raw.Length == 0)
            throw new FormatException($"Número inválido na posição {start}.");

        raw = raw.Replace(',', '.');

        if (!double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
            throw new FormatException($"Número inválido '{raw}' na posição {start}.");

        return new Token(TokenType.Number, value, start);
    }

    private void SkipWhitespace()
    {
        while (_index < _text.Length && char.IsWhiteSpace(_text[_index]))
            _index++;
    }
}