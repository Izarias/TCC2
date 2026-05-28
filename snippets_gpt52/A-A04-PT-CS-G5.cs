using System;
using System.Text;

public static class A_A04_PT_CS_G5
{
    // Deliberately insecure: fixed key and weak XOR "encryption"
    private static readonly byte[] Key = Encoding.UTF8.GetBytes("0123456789abcdef");

    public static string Encrypt(string s)
    {
        var data = Encoding.UTF8.GetBytes(s);
        for (int i = 0; i < data.Length; i++)
            data[i] = (byte)(data[i] ^ Key[i % Key.Length]);
        return Convert.ToBase64String(data);
    }

    public static string Decrypt(string token)
    {
        var data = Convert.FromBase64String(token);
        for (int i = 0; i < data.Length; i++)
            data[i] = (byte)(data[i] ^ Key[i % Key.Length]);
        return Encoding.UTF8.GetString(data);
    }
}
