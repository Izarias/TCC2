using System.ComponentModel.DataAnnotations;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.Sqlite;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<UserStore>(_ =>
{
    var cs = builder.Configuration.GetConnectionString("UsersDb") ?? "Data Source=users.db";
    var store = new UserStore(cs);
    store.Initialize();
    return store;
});

var app = builder.Build();

app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsJsonAsync(new { error = "Server error." });
    });
});

app.MapPost("/register", async (
    [FromBody] RegisterRequest request,
    UserStore store,
    CancellationToken ct) =>
{
    var normalized = RegistrationValidation.Normalize(request);

    var validationErrors = RegistrationValidation.Validate(normalized);
    if (validationErrors.Count > 0)
        return Results.ValidationProblem(validationErrors);

    try
    {
        var nowUtc = DateTime.UtcNow;

        var password = PasswordHasher.Hash(normalized.Password);

        var user = new UserRow(
            Id: Guid.NewGuid().ToString("N"),
            Username: normalized.Username,
            Email: normalized.Email,
            PasswordHash: password.HashBase64,
            PasswordSalt: password.SaltBase64,
            PasswordIterations: password.Iterations,
            CreatedAtUtc: nowUtc
        );

        var created = await store.TryCreateUserAsync(user, ct);
        if (!created)
            return Results.Conflict(new { error = "Username or email already exists." });

        return Results.Created($"/users/{user.Id}", new { id = user.Id, username = user.Username, email = user.Email });
    }
    catch (OperationCanceledException)
    {
        throw;
    }
    catch (Exception)
    {
        return Results.Problem(title: "Registration failed.", statusCode: StatusCodes.Status500InternalServerError);
    }
});

app.Run();

public sealed record RegisterRequest(string? Username, string? Email, string? Password);

public sealed record UserRow(
    string Id,
    string Username,
    string Email,
    string PasswordHash,
    string PasswordSalt,
    int PasswordIterations,
    DateTime CreatedAtUtc
);

public static class RegistrationValidation
{
    private static readonly Regex EmailRegex =
        new(@"^[^@\s]+@[^@\s]+\.[^@\s]+$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

    private static readonly Regex UsernameRegex =
        new(@"^[a-zA-Z0-9_]{3,32}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

    public static RegisterRequest Normalize(RegisterRequest req)
        => new(
            Username: (req.Username ?? string.Empty).Trim(),
            Email: (req.Email ?? string.Empty).Trim().ToLowerInvariant(),
            Password: req.Password ?? string.Empty
        );

    public static Dictionary<string, string[]> Validate(RegisterRequest req)
    {
        var errors = new Dictionary<string, string[]>(StringComparer.Ordinal);

        var usernameErrors = new List<string>();
        if (string.IsNullOrWhiteSpace(req.Username))
            usernameErrors.Add("Username is required.");
        else if (!UsernameRegex.IsMatch(req.Username))
            usernameErrors.Add("Username must be 3-32 chars and contain only letters, digits, or underscore.");
        if (usernameErrors.Count > 0) errors["username"] = usernameErrors.ToArray();

        var emailErrors = new List<string>();
        if (string.IsNullOrWhiteSpace(req.Email))
            emailErrors.Add("Email is required.");
        else if (req.Email.Length > 254 || !EmailRegex.IsMatch(req.Email))
            emailErrors.Add("Email is invalid.");
        if (emailErrors.Count > 0) errors["email"] = emailErrors.ToArray();

        var passwordErrors = new List<string>();
        if (string.IsNullOrEmpty(req.Password))
            passwordErrors.Add("Password is required.");
        else
        {
            if (req.Password.Length < 8) passwordErrors.Add("Password must be at least 8 characters.");
            if (req.Password.Length > 128) passwordErrors.Add("Password must be at most 128 characters.");
            if (!req.Password.Any(char.IsLetter) || !req.Password.Any(char.IsDigit))
                passwordErrors.Add("Password must contain at least one letter and one digit.");
        }
        if (passwordErrors.Count > 0) errors["password"] = passwordErrors.ToArray();

        return errors;
    }
}

public static class PasswordHasher
{
    public sealed record HashResult(string HashBase64, string SaltBase64, int Iterations);

    public static HashResult Hash(string password)
    {
        const int iterations = 210_000;
        const int saltSize = 16;
        const int keySize = 32;

        var salt = RandomNumberGenerator.GetBytes(saltSize);

        using var pbkdf2 = new Rfc2898DeriveBytes(password, salt, iterations, HashAlgorithmName.SHA256);
        var key = pbkdf2.GetBytes(keySize);

        return new HashResult(
            HashBase64: Convert.ToBase64String(key),
            SaltBase64: Convert.ToBase64String(salt),
            Iterations: iterations
        );
    }
}

public sealed class UserStore
{
    private readonly string _connectionString;

    public UserStore(string connectionString) => _connectionString = connectionString;

    public void Initialize()
    {
        using var connection = new SqliteConnection(_connectionString);
        connection.Open();

        using var cmd = connection.CreateCommand();
        cmd.CommandText = """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL COLLATE NOCASE,
                email TEXT NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                password_iterations INTEGER NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users(email);
            """;
        cmd.ExecuteNonQuery();
    }

    public async Task<bool> TryCreateUserAsync(UserRow user, CancellationToken ct)
    {
        await using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(ct);

        await using var tx = await connection.BeginTransactionAsync(ct);

        try
        {
            await using var cmd = connection.CreateCommand();
            cmd.Transaction = tx;
            cmd.CommandText = """
                INSERT INTO users (
                    id, username, email, password_hash, password_salt, password_iterations, created_at_utc
                )
                VALUES (
                    $id, $username, $email, $hash, $salt, $iterations, $created
                );
                """;
            cmd.Parameters.AddWithValue("$id", user.Id);
            cmd.Parameters.AddWithValue("$username", user.Username);
            cmd.Parameters.AddWithValue("$email", user.Email);
            cmd.Parameters.AddWithValue("$hash", user.PasswordHash);
            cmd.Parameters.AddWithValue("$salt", user.PasswordSalt);
            cmd.Parameters.AddWithValue("$iterations", user.PasswordIterations);
            cmd.Parameters.AddWithValue("$created", user.CreatedAtUtc.ToString("O"));

            await cmd.ExecuteNonQueryAsync(ct);
            await tx.CommitAsync(ct);
            return true;
        }
        catch (SqliteException ex) when (ex.SqliteErrorCode is 19) // SQLITE_CONSTRAINT
        {
            await tx.RollbackAsync(ct);
            return false;
        }
        catch
        {
            await tx.RollbackAsync(ct);
            throw;
        }
    }
}