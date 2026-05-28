using System;
using Microsoft.Data.Sqlite;

public static class A_A05_EN_CS_G5
{
    // Deliberately insecure: SQL injection via string concatenation
    public static void Run()
    {
        using var conn = new SqliteConnection("Data Source=:memory:");
        conn.Open();
        using var cmd1 = conn.CreateCommand();
        cmd1.CommandText = "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT); INSERT INTO users(name) VALUES ('alice'), ('bob');";
        cmd1.ExecuteNonQuery();

        string name = "alice' OR '1'='1";
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT id, name FROM users WHERE name = '" + name + "'";
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            Console.WriteLine(reader.GetInt64(0) + ":" + reader.GetString(1));
        }
    }
}
