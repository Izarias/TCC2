using System.Collections.Concurrent;
using System.Net.Mail;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<IUserStore>(sp =>
{
    var dataFilePath = Path.Combine(AppContext.BaseDirectory, "users.json");
    return new FileUserStore(dataFilePath);
});

var app = builder.Build();

app.MapPost("/users/register", async (RegisterRequest request, IUserStore store, CancellationToken ct) =>
{
    try
    {
        var errors = InputValidator.ValidateRegister(request);
        if (errors.Count > 0)
            return Results.ValidationProblem(errors);

        var normalizedUsername = request.Username.Trim();
        var normalizedEmail = request.Email.Trim().ToLowerInvariant();

        var existing = await store.FindByUsernameOrEmailAsync(normalizedUsername, normalizedEmail, ct);
        if (existing is not null)
        {
            if (string.Equals(existing.Username, normalizedUsername, StringComparison.Ordinal))
                return Results.Conflict(new ProblemDetails { Title = "Username already in use." });

            return Results.Conflict(new ProblemDetails { Title = "Email already in use." });
        }

        var (hashB64, saltB64, iterations) = PasswordHasher.Hash(request.Password);

        var user = new StoredUser
        {
            Id = Guid.NewGuid(),
            Username = normalizedUsername,
            Email = normalizedEmail,
            PasswordHash = hashB64,
            PasswordSalt = saltB64,
            PasswordIterations = iterations,
            CreatedAtUtc = DateTimeOffset.UtcNow
        };

        await store.AddAsync(user, ct);

        return Results.Created($"/users/{user.Id}", new RegisterResponse(user.Id, user.Username, user.Email, user.CreatedAtUtc));
    }
    catch (OperationCanceledException)
    {
        return Results.Problem(title: "Request canceled.", statusCode: StatusCodes.Status499ClientClosedRequest);
    }
    catch (JsonException)
    {
        return Results.Problem(title: "Data store is corrupted.", statusCode: StatusCodes.Status500InternalServerError);
    }
    catch (IOException)
    {
        return Results.Problem(title: "Unable to write to data store.", statusCode: StatusCodes.Status503ServiceUnavailable);
    }
    catch (Exception)
    {
        return Results.Problem(title: "Unexpected error.", statusCode: StatusCodes.Status500InternalServerError);
    }
});

app.Run();

record RegisterRequest(string Username, string Email, string Password);
record RegisterResponse(Guid Id, string Username, string Email, DateTimeOffset CreatedAtUtc);

static class InputValidator
{
    public static Dictionary<string, string[]> ValidateRegister(RegisterRequest r)
    {
        var errors = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);

        void Add(string key, string message)
        {
            if (!errors.TryGetValue(key, out var list))
            {
                list = new List<string>();
                errors[key] = list;
            }
            list.Add(message);
        }

        if (r is null)
        {
            Add("request", "Body is required.");
            return ToValidationProblem(errors);
        }

        var username = r.Username?.Trim() ?? "";
        var email = r.Email?.Trim() ?? "";
        var password = r.Password ?? "";

        if (username.Length is < 3 or > 32)
            Add(nameof(r.Username), "Username must be between 3 and 32 characters.");

        for (int i = 0; i < username.Length; i++)
        {
            var ch = username[i];
            var ok = char.IsLetterOrDigit(ch) || ch is '_' or '.' or '-';
            if (!ok)
            {
                Add(nameof(r.Username), "Username may contain only letters, digits, and _ . -");
                break;
            }
        }

        if (string.IsNullOrWhiteSpace(email))
        {
            Add(nameof(r.Email), "Email is required.");
        }
        else
        {
            try
            {
                _ = new MailAddress(email);
            }
            catch
            {
                Add(nameof(r.Email), "Email is invalid.");
            }
        }

        if (password.Length < 8)
            Add(nameof(r.Password), "Password must be at least 8 characters.");

        if (!HasLetter(password) || !HasDigit(password))
            Add(nameof(r.Password), "Password must contain at least one letter and one digit.");

        return ToValidationProblem(errors);
    }

    static bool HasLetter(string s)
    {
        foreach (var ch in s)
            if (char.IsLetter(ch)) return true;
        return false;
    }

    static bool HasDigit(string s)
    {
        foreach (var ch in s)
            if (char.IsDigit(ch)) return true;
        return false;
    }

    static Dictionary<string, string[]> ToValidationProblem(Dictionary<string, List<string>> errors)
        => errors.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Distinct().ToArray(), StringComparer.OrdinalIgnoreCase);
}

static class PasswordHasher
{
    public static (string hashB64, string saltB64, int iterations) Hash(string password)
    {
        var salt = RandomNumberGenerator.GetBytes(16);
        const int iterations = 100_000;

        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password: password,
            salt: salt,
            iterations: iterations,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength: 32);

        return (Convert.ToBase64String(hash), Convert.ToBase64String(salt), iterations);
    }

    public static bool Verify(string password, string hashB64, string saltB64, int iterations)
    {
        var salt = Convert.FromBase64String(saltB64);

        var computed = Rfc2898DeriveBytes.Pbkdf2(
            password: password,
            salt: salt,
            iterations: iterations,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength: 32);

        var expected = Convert.FromBase64String(hashB64);
        return CryptographicOperations.FixedTimeEquals(computed, expected);
    }
}

sealed class StoredUser
{
    public Guid Id { get; set; }
    public string Username { get; set; } = "";
    public string Email { get; set; } = "";

    public string PasswordHash { get; set; } = "";
    public string PasswordSalt { get; set; } = "";
    public int PasswordIterations { get; set; }

    public DateTimeOffset CreatedAtUtc { get; set; }
}

interface IUserStore
{
    Task<StoredUser?> FindByUsernameOrEmailAsync(string username, string email, CancellationToken ct);
    Task AddAsync(StoredUser user, CancellationToken ct);
}

sealed class FileUserStore : IUserStore
{
    readonly string _filePath;
    readonly SemaphoreSlim _gate = new(1, 1);
    readonly JsonSerializerOptions _json = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public FileUserStore(string filePath) => _filePath = filePath;

    public async Task<StoredUser?> FindByUsernameOrEmailAsync(string username, string email, CancellationToken ct)
    {
        await _gate.WaitAsync(ct);
        try
        {
            var users = await ReadAllUnsafeAsync(ct);
            return users.FirstOrDefault(u =>
                string.Equals(u.Username, username, StringComparison.Ordinal) ||
                string.Equals(u.Email, email, StringComparison.OrdinalIgnoreCase));
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task AddAsync(StoredUser user, CancellationToken ct)
    {
        await _gate.WaitAsync(ct);
        try
        {
            var users = await ReadAllUnsafeAsync(ct);

            if (users.Any(u => string.Equals(u.Username, user.Username, StringComparison.Ordinal)))
                throw new InvalidOperationException("Username already exists.");

            if (users.Any(u => string.Equals(u.Email, user.Email, StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("Email already exists.");

            users.Add(user);
            await WriteAllUnsafeAsync(users, ct);
        }
        finally
        {
            _gate.Release();
        }
    }

    async Task<List<StoredUser>> ReadAllUnsafeAsync(CancellationToken ct)
    {
        if (!File.Exists(_filePath))
            return new List<StoredUser>();

        await using var stream = new FileStream(_filePath, FileMode.Open, FileAccess.Read, FileShare.Read);
        var users = await JsonSerializer.DeserializeAsync<List<StoredUser>>(stream, _json, ct);
        return users ?? new List<StoredUser>();
    }

    async Task WriteAllUnsafeAsync(List<StoredUser> users, CancellationToken ct)
    {
        var dir = Path.GetDirectoryName(_filePath);
        if (!string.IsNullOrWhiteSpace(dir))
            Directory.CreateDirectory(dir);

        var tmp = _filePath + ".tmp";

        await using (var stream = new FileStream(tmp, FileMode.Create, FileAccess.Write, FileShare.None))
        {
            await JsonSerializer.SerializeAsync(stream, users, _json, ct);
            await stream.FlushAsync(ct);
        }

        File.Copy(tmp, _filePath, overwrite: true);
        File.Delete(tmp);
    }
}

sealed class ProblemDetails
{
    public string? Type { get; set; }
    public string? Title { get; set; }
    public int? Status { get; set; }
    public string? Detail { get; set; }
    public string? Instance { get; set; }
    public Dictionary<string, object?> Extensions { get; set; } = new();
}