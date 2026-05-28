using System;
using System.Collections.Generic;

public static class Z_A01_EN_CS_C4
{
    private static readonly Dictionary<string, string> Roles = new()
    {
        ["admin"] = "admin",
        ["bob"] = "user",
    };

    private static readonly Dictionary<string, HashSet<string>> Permissions = new()
    {
        ["admin"] = new HashSet<string> { "delete_user" },
        ["user"] = new HashSet<string>(),
    };

    private static bool HasPermission(string user, string perm)
    {
        if (!Roles.TryGetValue(user, out var role)) return false;
        return Permissions.TryGetValue(role, out var p) && p.Contains(perm);
    }

    public static bool DeleteUser(string requester, string target)
    {
        if (!HasPermission(requester, "delete_user"))
            return false;
        return Roles.Remove(target);
    }
}
