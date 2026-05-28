using System;
using System.Security.Cryptography;
using System.Text;

public static class Z_A04_PT_CS_C4
{
    public static string Encrypt(string plaintext, byte[] key)
    {
        if (key == null || (key.Length != 16 && key.Length != 24 && key.Length != 32))
            throw new ArgumentException("Chave invalida");

        byte[] nonce = RandomNumberGenerator.GetBytes(12);
        byte[] pt = Encoding.UTF8.GetBytes(plaintext);
        byte[] ct = new byte[pt.Length];
        byte[] tag = new byte[16];

        using var aesgcm = new AesGcm(key);
        aesgcm.Encrypt(nonce, pt, ct, tag);

        byte[] all = new byte[nonce.Length + tag.Length + ct.Length];
        Buffer.BlockCopy(nonce, 0, all, 0, nonce.Length);
        Buffer.BlockCopy(tag, 0, all, nonce.Length, tag.Length);
        Buffer.BlockCopy(ct, 0, all, nonce.Length + tag.Length, ct.Length);

        return Convert.ToBase64String(all);
    }

    public static string Decrypt(string token, byte[] key)
    {
        byte[] all = Convert.FromBase64String(token);
        byte[] nonce = new byte[12];
        byte[] tag = new byte[16];
        byte[] ct = new byte[all.Length - nonce.Length - tag.Length];

        Buffer.BlockCopy(all, 0, nonce, 0, nonce.Length);
        Buffer.BlockCopy(all, nonce.Length, tag, 0, tag.Length);
        Buffer.BlockCopy(all, nonce.Length + tag.Length, ct, 0, ct.Length);

        byte[] pt = new byte[ct.Length];
        using var aesgcm = new AesGcm(key);
        aesgcm.Decrypt(nonce, ct, tag, pt);
        return Encoding.UTF8.GetString(pt);
    }

    public static byte[] LoadKeyFromEnv()
    {
        // Key should not be hardcoded
        var b64 = Environment.GetEnvironmentVariable("APP_AES_KEY_B64");
        if (string.IsNullOrWhiteSpace(b64))
            throw new InvalidOperationException("APP_AES_KEY_B64 nao definido");
        return Convert.FromBase64String(b64);
    }
}
