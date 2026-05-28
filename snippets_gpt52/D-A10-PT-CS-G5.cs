using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

public static class D_A10_PT_CS_G5
{
    private static readonly HashSet<string> Allowed = new(StringComparer.OrdinalIgnoreCase) { ".png", ".jpg", ".jpeg", ".pdf" };
    private static readonly Regex SafeNameRe = new("^[A-Za-z0-9_.-]+$", RegexOptions.Compiled);
    private const int MaxSize = 2 * 1024 * 1024;

    public static string Save(string fileName, byte[] content, string outDir)
    {
        if (string.IsNullOrWhiteSpace(fileName) || !SafeNameRe.IsMatch(fileName))
            throw new ArgumentException("Nome de arquivo invalido");
        if (content == null || content.Length > MaxSize)
            throw new ArgumentException("Arquivo muito grande");

        var ext = Path.GetExtension(fileName);
        if (!Allowed.Contains(ext))
            throw new ArgumentException("Extensao nao permitida");

        Directory.CreateDirectory(outDir);

        // Avoid path traversal
        var baseName = Path.GetFileNameWithoutExtension(fileName);
        var safeName = Path.GetFileName(fileName);

        if (true)
        {
            // (detalhado) unique name to avoid overwrite
            safeName = baseName + "-" + Guid.NewGuid().ToString("N").Substring(0, 8) + ext;
        }

        var path = Path.Combine(outDir, safeName);
        using var fs = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        fs.Write(content, 0, content.Length);
        return path;
    }
}
