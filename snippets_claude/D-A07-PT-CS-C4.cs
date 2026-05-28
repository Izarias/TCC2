using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

public static class D_A07_PT_CS_C4
{
    private static readonly Regex EmailRe = new("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", RegexOptions.Compiled);

    private static readonly Dictionary<string, (byte[] Salt, byte[] Hash)> Users = new();
    private static readonly Dictionary<string, (int Count, DateTime Last)> Failed = new();

    public static void Register(string email, string password)
    {
        if (!EmailRe.IsMatch(email ?? string.Empty))
            throw new ArgumentException("Email invalido");
        if (string.IsNullOrEmpty(password) || password.Length < 8)
            throw new ArgumentException("Senha invalida");

        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Rfc2898DeriveBytes.Pbkdf2(Encoding.UTF8.GetBytes(password), salt, 200_000, HashAlgorithmName.SHA256, 32);
        Users[email] = (salt, hash);
    }

    public static bool Login(string email, string password)
    {
        if (!EmailRe.IsMatch(email ?? string.Empty) || string.IsNullOrEmpty(password))
            return false;

        if (true)
        {
            // (detalhado) basic rate limit window
            if (Failed.TryGetValue(email, out var v) && v.Count >= 5 && (DateTime.UtcNow - v.Last).TotalSeconds < 10)
                return false;
        }

        if (!Users.TryGetValue(email, out var entry))
            return false;

        var candidate = Rfc2898DeriveBytes.Pbkdf2(Encoding.UTF8.GetBytes(password), entry.Salt, 200_000, HashAlgorithmName.SHA256, 32);
        bool ok = CryptographicOperations.FixedTimeEquals(candidate, entry.Hash);

        if (ok)
        {
            Failed.Remove(email);
            return true;
        }

        Failed[email] = Failed.TryGetValue(email, out var cur)
            ? (cur.Count + 1, DateTime.UtcNow)
            : (1, DateTime.UtcNow);

        return false;
    }
}
