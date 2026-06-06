using System;
using System.Collections.Generic;
using System.Globalization;

public static class Program
{
    public static void Main()
    {
        while (true)
        {
            Console.Write("Enter expression (empty to exit): ");
            var input = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(input)) return;

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

internal static class ExpressionEvaluator
{
    private enum TokenType { Number, Operator, LeftParen, RightParen }

    private readonly struct Token
    {
        public TokenType Type { get; }
        public double Number { get; }
        public string Op { get; }

        private Token(TokenType type, double number, string op)
        {
            Type = type;
            Number = number;
            Op = op;
        }

        public static Token Num(double value) => new Token(TokenType.Number, value, "");
        public static Token Oper(string op) => new Token(TokenType.Operator, 0.0, op);
        public static Token LParen() => new Token(TokenType.LeftParen, 0.0, "(");
        public static Token RParen() => new Token(TokenType.RightParen, 0.0, ")");
    }

    private sealed class OpInfo
    {
        public int Precedence { get; }
        public bool RightAssociative { get; }
        public int Arity { get; }
        public Func<double, double, double>? Binary { get; }
        public Func<double, double>? Unary { get; }

        public OpInfo(int precedence, bool rightAssociative, int arity,
            Func<double, double, double>? binary = null,
            Func<double, double>? unary = null)
        {
            Precedence = precedence;
            RightAssociative = rightAssociative;
            Arity = arity;
            Binary = binary;
            Unary = unary;
        }
    }

    private static readonly Dictionary<string, OpInfo> Ops = new Dictionary<string, OpInfo>(StringComparer.Ordinal)
    {
        ["u+"] = new OpInfo(precedence: 5, rightAssociative: true, arity: 1, unary: a => a),
        ["u-"] = new OpInfo(precedence: 5, rightAssociative: true, arity: 1, unary: a => -a),

        ["^"]  = new OpInfo(precedence: 4, rightAssociative: true,  arity: 2, binary: (a, b) => Math.Pow(a, b)),
        ["*"]  = new OpInfo(precedence: 3, rightAssociative: false, arity: 2, binary: (a, b) => a * b),
        ["/"]  = new OpInfo(precedence: 3, rightAssociative: false, arity: 2, binary: (a, b) => a / b),
        ["+"]  = new OpInfo(precedence: 2, rightAssociative: false, arity: 2, binary: (a, b) => a + b),
        ["-"]  = new OpInfo(precedence: 2, rightAssociative: false, arity: 2, binary: (a, b) => a - b),
    };

    public static double Evaluate(string expression)
    {
        if (expression is null) throw new ArgumentNullException(nameof(expression));

        var tokens = Tokenize(expression);
        var rpn = ToRpn(tokens);
        return EvalRpn(rpn);
    }

    private static List<Token> Tokenize(string s)
    {
        var tokens = new List<Token>();
        int i = 0;

        while (i < s.Length)
        {
            char c = s[i];

            if (char.IsWhiteSpace(c))
            {
                i++;
                continue;
            }

            if (c == '(')
            {
                tokens.Add(Token.LParen());
                i++;
                continue;
            }

            if (c == ')')
            {
                tokens.Add(Token.RParen());
                i++;
                continue;
            }

            if (IsOpChar(c))
            {
                tokens.Add(Token.Oper(c.ToString()));
                i++;
                continue;
            }

            if (char.IsDigit(c) || c == '.')
            {
                int start = i;
                bool sawDot = (c == '.');
                i++;

                while (i < s.Length)
                {
                    char ch = s[i];
                    if (char.IsDigit(ch))
                    {
                        i++;
                        continue;
                    }

                    if (ch == '.' && !sawDot)
                    {
                        sawDot = true;
                        i++;
                        continue;
                    }

                    break;
                }

                string numText = s.Substring(start, i - start);
                if (!double.TryParse(numText, NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
                    throw new FormatException($"Invalid number: '{numText}'");

                tokens.Add(Token.Num(value));
                continue;
            }

            throw new FormatException($"Unexpected character '{c}' at position {i + 1}.");
        }

        // Rewrite + and - as unary where appropriate
        var rewritten = new List<Token>(tokens.Count);
        Token? prev = null;

        for (int t = 0; t < tokens.Count; t++)
        {
            var cur = tokens[t];
            if (cur.Type == TokenType.Operator && (cur.Op == "+" || cur.Op == "-"))
            {
                bool unary =
                    prev == null ||
                    prev.Value.Type == TokenType.Operator ||
                    prev.Value.Type == TokenType.LeftParen;

                if (unary)
                    rewritten.Add(Token.Oper(cur.Op == "+" ? "u+" : "u-"));
                else
                    rewritten.Add(cur);
            }
            else
            {
                rewritten.Add(cur);
            }

            prev = rewritten[rewritten.Count - 1];
        }

        return rewritten;
    }

    private static List<Token> ToRpn(List<Token> tokens)
    {
        var output = new List<Token>(tokens.Count);
        var stack = new Stack<Token>();

        foreach (var tok in tokens)
        {
            switch (tok.Type)
            {
                case TokenType.Number:
                    output.Add(tok);
                    break;

                case TokenType.Operator:
                    if (!Ops.TryGetValue(tok.Op, out var o1))
                        throw new InvalidOperationException($"Unknown operator '{tok.Op}'.");

                    while (stack.Count > 0 && stack.Peek().Type == TokenType.Operator)
                    {
                        var top = stack.Peek();
                        var o2 = Ops[top.Op];

                        bool pop =
                            (!o1.RightAssociative && o1.Precedence <= o2.Precedence) ||
                            (o1.RightAssociative && o1.Precedence < o2.Precedence);

                        if (!pop) break;
                        output.Add(stack.Pop());
                    }

                    stack.Push(tok);
                    break;

                case TokenType.LeftParen:
                    stack.Push(tok);
                    break;

                case TokenType.RightParen:
                    bool foundLeft = false;
                    while (stack.Count > 0)
                    {
                        var x = stack.Pop();
                        if (x.Type == TokenType.LeftParen)
                        {
                            foundLeft = true;
                            break;
                        }
                        output.Add(x);
                    }
                    if (!foundLeft) throw new FormatException("Mismatched parentheses.");
                    break;

                default:
                    throw new InvalidOperationException("Unknown token type.");
            }
        }

        while (stack.Count > 0)
        {
            var x = stack.Pop();
            if (x.Type == TokenType.LeftParen || x.Type == TokenType.RightParen)
                throw new FormatException("Mismatched parentheses.");
            output.Add(x);
        }

        return output;
    }

    private static double EvalRpn(List<Token> rpn)
    {
        var st = new Stack<double>();

        foreach (var tok in rpn)
        {
            if (tok.Type == TokenType.Number)
            {
                st.Push(tok.Number);
                continue;
            }

            if (tok.Type != TokenType.Operator)
                throw new InvalidOperationException("Invalid RPN token.");

            var op = Ops[tok.Op];

            if (op.Arity == 1)
            {
                if (st.Count < 1) throw new InvalidOperationException("Insufficient values for unary operator.");
                double a = st.Pop();
                st.Push(op.Unary!(a));
            }
            else if (op.Arity == 2)
            {
                if (st.Count < 2) throw new InvalidOperationException("Insufficient values for binary operator.");
                double b = st.Pop();
                double a = st.Pop();
                double res = op.Binary!(a, b);

                if (double.IsNaN(res) || double.IsInfinity(res))
                    throw new InvalidOperationException("Result is not a finite number.");

                st.Push(res);
            }
            else
            {
                throw new InvalidOperationException("Unsupported operator arity.");
            }
        }

        if (st.Count != 1) throw new InvalidOperationException("Invalid expression.");
        return st.Pop();
    }

    private static bool IsOpChar(char c) => c is '+' or '-' or '*' or '/' or '^';
}