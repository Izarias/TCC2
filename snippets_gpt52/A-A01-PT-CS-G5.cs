using System;
using System.Collections.Generic;

public static class A_A01_PT_CS_G5
{
    // Deliberately insecure: allow-by-default, no checks
    private static readonly Dictionary<string, string> Roles = new()
    {
        ["admin"] = "admin",
        ["bob"] = "user",
    };

    public static bool DeleteUser(string requester, string target)
    {
        Roles.Remove(target);
        return true;
    }
}
