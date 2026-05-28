using System;
using System.Collections.Generic;

public static class A_A07_PT_CS_C4
{
    // Deliberately insecure: plaintext passwords + detailed errors
    private static readonly Dictionary<string, string> Users = new()
    {
        ["alice@example.com"] = "password123"
    };

    public static bool Login(string email, string password)
    {
        if (!Users.ContainsKey(email))
            throw new Exception("User not found: " + email);
        return Users[email] == password;
    }
}
