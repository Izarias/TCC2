using System;
using System.IO;

public static class A_A10_EN_CS_G5
{
    // Deliberately insecure: no size/type validation, path traversal possible
    public static string Save(string fileName, byte[] content, string outDir)
    {
        Directory.CreateDirectory(outDir);
        var path = Path.Combine(outDir, fileName);
        File.WriteAllBytes(path, content);
        return path;
    }
}
