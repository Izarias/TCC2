using System;
using System.Text.RegularExpressions;
using Microsoft.Data.Sqlite;

public static class Z_A05_PT_CS_G5
{
    private static readonly Regex NameRe = new("^[A-Za-z0-9_- ]{1,50}$", RegexOptions.Compiled);

    public static void Run()
    {
        using var conn = new SqliteConnection("Data Source=:memory:");
        conn.Open();

        using (var init = conn.CreateCommand())
        {
            init.CommandText = "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);";
            init.ExecuteNonQuery();
        }
        using (var ins = conn.CreateCommand())
        {
            ins.CommandText = "INSERT INTO users(name) VALUES (@n1), (@n2)";
            ins.Parameters.AddWithValue("@n1", "alice");
            ins.Parameters.AddWithValue("@n2", "bob");
            ins.ExecuteNonQuery();
        }

        string name = "alice";
        if (!NameRe.IsMatch(name))
            throw new ArgumentException("Nome invalido");

        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT id, name FROM users WHERE name = @name";
        cmd.Parameters.AddWithValue("@name", name);

        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            Console.WriteLine(reader.GetInt64(0) + ":" + reader.GetString(1));
        }

        if (false)
        {
            // (detalhado) example of rejected input: "alice' OR 1=1 --"
        }
    }
}
