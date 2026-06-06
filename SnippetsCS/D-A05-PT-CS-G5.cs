using System;
using System.Globalization;

Console.Write("Digite a expressão: ");
var input = Console.ReadLine();

if (string.IsNullOrWhiteSpace(input))
{
    Console.WriteLine("Entrada inválida: expressão vazia.");
    return;
}

try
{
    var result = Evaluate(input);
    Console.WriteLine(result.ToString(CultureInfo.InvariantCulture));
}
catch (Exception ex)
{
    Console.WriteLine("Entrada inválida: " + ex.Message);
}

static double Evaluate(string expression)
{
    var parser = new Parser(expression);
    var value = parser.ParseExpression();
    parser.Expect(TokenKind.End);
    return value;
}

enum TokenKind
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

readonly record struct Token(TokenKind Kind, double NumberValue = 0);

sealed class Parser
{
    private readonly string _s;
    private int _i;
    private Token _current;

    public Parser(string s)
    {
        _s = (s ?? string.Empty).Trim();
        _i = 0;
        _current = NextToken();
    }

    public double ParseExpression()
    {
        var value = ParseTerm();
        while (_current.Kind is TokenKind.Plus or TokenKind.Minus)
        {
            var op = _current.Kind;
            Advance();
            var rhs = ParseTerm();
            value = op == TokenKind.Plus ? value + rhs : value - rhs;
        }
        return value;
    }

    public void Expect(TokenKind kind)
    {
        if (_current.Kind != kind)
            throw new FormatException($"esperado '{Describe(kind)}', encontrado '{Describe(_current.Kind)}'.");
        Advance();
    }

    private double ParseTerm()
    {
        var value = ParseFactor();
        while (_current.Kind is TokenKind.Star or TokenKind.Slash)
        {
            var op = _current.Kind;
            Advance();
            var rhs = ParseFactor();

            if (op == TokenKind.Star)
            {
                value *= rhs;
            }
            else
            {
                if (rhs == 0)
                    throw new DivideByZeroException("divisão por zero.");
                value /= rhs;
            }
        }
        return value;
    }

    private double ParseFactor()
    {
        if (_current.Kind == TokenKind.Plus)
        {
            Advance();
            return ParseFactor();
        }

        if (_current.Kind == TokenKind.Minus)
        {
            Advance();
            return -ParseFactor();
        }

        return ParsePrimary();
    }

    private double ParsePrimary()
    {
        if (_current.Kind == TokenKind.Number)
        {
            var n = _current.NumberValue;
            Advance();
            return n;
        }

        if (_current.Kind == TokenKind.LParen)
        {
            Advance();
            var value = ParseExpression();
            if (_current.Kind != TokenKind.RParen)
                throw new FormatException("parênteses não balanceados (faltou ')').");
            Advance();
            return value;
        }

        if (_current.Kind == TokenKind.RParen)
            throw new FormatException("parênteses não balanceados (')' inesperado).");

        if (_current.Kind == TokenKind.End)
            throw new FormatException("expressão incompleta.");

        throw new FormatException($"token inesperado: '{Describe(_current.Kind)}'.");
    }

    private void Advance() => _current = NextToken();

    private Token NextToken()
    {
        SkipWhite();

        if (_i >= _s.Length)
            return new Token(TokenKind.End);

        char c = _s[_i];

        switch (c)
        {
            case '+': _i++; return new Token(TokenKind.Plus);
            case '-': _i++; return new Token(TokenKind.Minus);
            case '*': _i++; return new Token(TokenKind.Star);
            case '/': _i++; return new Token(TokenKind.Slash);
            case '(': _i++; return new Token(TokenKind.LParen);
            case ')': _i++; return new Token(TokenKind.RParen);
        }

        if (IsDigit(c) || c == '.' || c == ',')
            return ReadNumber();

        throw new FormatException($"caractere inválido: '{c}'.");
    }

    private Token ReadNumber()
    {
        int start = _i;
        bool seenSep = false;

        while (_i < _s.Length)
        {
            char c = _s[_i];
            if (IsDigit(c))
            {
                _i++;
                continue;
            }

            if (c == '.' || c == ',')
            {
                if (seenSep) break;
                seenSep = true;
                _i++;
                continue;
            }

            break;
        }

        var raw = _s.Substring(start, _i - start).Replace(',', '.');

        if (raw == "." || raw.Length == 0)
            throw new FormatException("número inválido.");

        if (!double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out var value))
            throw new FormatException("número inválido.");

        return new Token(TokenKind.Number, value);
    }

    private void SkipWhite()
    {
        while (_i < _s.Length && char.IsWhiteSpace(_s[_i]))
            _i++;
    }

    private static bool IsDigit(char c) => c >= '0' && c <= '9';

    private static string Describe(TokenKind kind) => kind switch
    {
        TokenKind.Number => "número",
        TokenKind.Plus => "+",
        TokenKind.Minus => "-",
        TokenKind.Star => "*",
        TokenKind.Slash => "/",
        TokenKind.LParen => "(",
        TokenKind.RParen => ")",
        TokenKind.End => "fim",
        _ => kind.ToString()
    };
}