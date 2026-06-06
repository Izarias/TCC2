using System.ComponentModel.DataAnnotations;
using System.Net.Mail;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Http.HttpResults;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<RegistrationStoreOptions>(opts =>
{
    opts.DataFilePath =
        builder.Configuration["RegistrationStore:DataFilePath"]
        ?? Path.Combine(AppContext.BaseDirectory, "App_Data", "users.json");
});

builder.Services.AddSingleton<IUserRepository, FileUserRepository>();
builder.Services.AddSingleton<IPasswordHasher, Pbkdf2PasswordHasher>();
builder.Services.AddSingleton<IUserService, UserService>();

builder.Services.AddProblemDetails();

var app = builder.Build();

app.UseExceptionHandler();
app.UseStatusCodePages();
app.UseHttpsRedirection();

app.MapPost("/api/register", async Task<Results<Created<UserResponse>, ProblemHttpResult>> (
    RegisterRequest request,
    IUserService userService,
    HttpContext http,
    CancellationToken ct) =>
{
    var result = await userService.RegisterAsync(request, ct);
    if (!result.Success)
        return TypedResults.Problem(title: result.ErrorTitle, detail: result.ErrorDetail, statusCode: result.StatusCode);

    var location = $"{http.Request.Scheme}://{http.Request.Host}/api/users/{result.Value!.Id}";
    return TypedResults.Created(location, result.Value);
})
.WithName("RegisterUser");

app.MapGet("/api/users/{id:guid}", async Task<Results<Ok<UserResponse>, NotFound>> (
    Guid id,
    IUserService userService,
    CancellationToken ct) =>
{
    var user = await userService.GetUserAsync(id, ct);
    return user is null ? TypedResults.NotFound() : TypedResults.Ok(user);
})
.WithName("GetUser");

app.Run();

public sealed class RegistrationStoreOptions
{
    public string DataFilePath { get; set; } = "";
}

public sealed record RegisterRequest(
    string Email,
    string Password,
    string DisplayName
);

public sealed record UserResponse(
    Guid Id,
    string Email,
    string DisplayName,
    DateTimeOffset CreatedUtc
);

public sealed class UserRecord
{
    public Guid Id { get; set; }
    public string EmailNormalized { get; set; } = "";
    public string Email { get; set; } = "";
    public string DisplayName { get; set; } = "";

    public string PasswordHashBase64 { get; set; } = "";
    public string PasswordSaltBase64 { get; set; } = "";
    public int PasswordIterations { get; set; }

    public DateTimeOffset CreatedUtc { get; set; }
}

public sealed record ServiceResult<T>(bool Success, T? Value, int StatusCode, string ErrorTitle, string ErrorDetail)
{
    public static ServiceResult<T> Ok(T value) => new(true, value, StatusCodes.Status200OK, "", "");
    public static ServiceResult<T> Created(T value) => new(true, value, StatusCodes.Status201Created, "", "");
    public static ServiceResult<T> BadRequest(string title, string detail) => new(false, default, StatusCodes.Status400BadRequest, title, detail);
    public static ServiceResult<T> Conflict(string title, string detail) => new(false, default, StatusCodes.Status409Conflict, title, detail);
    public static ServiceResult<T> NotFound(string title, string detail) => new(false, default, StatusCodes.Status404NotFound, title, detail);
}

public interface IUserService
{
    Task<ServiceResult<UserResponse>> RegisterAsync(RegisterRequest request, CancellationToken ct);
    Task<UserResponse?> GetUserAsync(Guid id, CancellationToken ct);
}

public sealed class UserService : IUserService
{
    private readonly IUserRepository _repo;
    private readonly IPasswordHasher _passwordHasher;

    public UserService(IUserRepository repo, IPasswordHasher passwordHasher)
    {
        _repo = repo;
        _passwordHasher = passwordHasher;
    }

    public async Task<ServiceResult<UserResponse>> RegisterAsync(RegisterRequest request, CancellationToken ct)
    {
        var validation = RegistrationValidator.Validate(request);
        if (!validation.IsValid)
            return ServiceResult<UserResponse>.BadRequest("Validation failed", validation.ToSingleString());

        var emailNormalized = Normalization.NormalizeEmail(request.Email);
        if (await _repo.EmailExistsAsync(emailNormalized, ct))
            return ServiceResult<UserResponse>.Conflict("Email already registered", "An account with this email already exists.");

        var (salt, hash, iterations) = _passwordHasher.HashPassword(request.Password);

        var record = new UserRecord
        {
            Id = Guid.NewGuid(),
            Email = request.Email.Trim(),
            EmailNormalized = emailNormalized,
            DisplayName = request.DisplayName.Trim(),
            PasswordSaltBase64 = Convert.ToBase64String(salt),
            PasswordHashBase64 = Convert.ToBase64String(hash),
            PasswordIterations = iterations,
            CreatedUtc = DateTimeOffset.UtcNow
        };

        await _repo.AddAsync(record, ct);

        return ServiceResult<UserResponse>.Created(new UserResponse(
            record.Id,
            record.Email,
            record.DisplayName,
            record.CreatedUtc
        ));
    }

    public async Task<UserResponse?> GetUserAsync(Guid id, CancellationToken ct)
    {
        var record = await _repo.GetByIdAsync(id, ct);
        if (record is null) return null;

        return new UserResponse(record.Id, record.Email, record.DisplayName, record.CreatedUtc);
    }
}

public interface IUserRepository
{
    Task<bool> EmailExistsAsync(string emailNormalized, CancellationToken ct);
    Task AddAsync(UserRecord record, CancellationToken ct);
    Task<UserRecord?> GetByIdAsync(Guid id, CancellationToken ct);
}

public sealed class FileUserRepository : IUserRepository
{
    private readonly string _dataFilePath;
    private readonly SemaphoreSlim _gate = new(1, 1);

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public FileUserRepository(Microsoft.Extensions.Options.IOptions<RegistrationStoreOptions> options)
    {
        _dataFilePath = options.Value.DataFilePath;
    }

    public async Task<bool> EmailExistsAsync(string emailNormalized, CancellationToken ct)
    {
        await _gate.WaitAsync(ct);
        try
        {
            var db = await LoadAsync(ct);
            return db.Users.Any(u => u.EmailNormalized == emailNormalized);
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task AddAsync(UserRecord record, CancellationToken ct)
    {
        await _gate.WaitAsync(ct);
        try
        {
            var db = await LoadAsync(ct);

            if (db.Users.Any(u => u.EmailNormalized == record.EmailNormalized))
                throw new InvalidOperationException("Duplicate email normalized key.");

            db.Users.Add(record);

            await SaveAsync(db, ct);
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<UserRecord?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        await _gate.WaitAsync(ct);
        try
        {
            var db = await LoadAsync(ct);
            return db.Users.FirstOrDefault(u => u.Id == id);
        }
        finally
        {
            _gate.Release();
        }
    }

    private async Task<UserDatabase> LoadAsync(CancellationToken ct)
    {
        EnsureDirectoryExists();

        if (!File.Exists(_dataFilePath))
            return new UserDatabase();

        await using var stream = File.Open(_dataFilePath, FileMode.Open, FileAccess.Read, FileShare.Read);
        var db = await JsonSerializer.DeserializeAsync<UserDatabase>(stream, JsonOptions, ct);
        return db ?? new UserDatabase();
    }

    private async Task SaveAsync(UserDatabase db, CancellationToken ct)
    {
        EnsureDirectoryExists();

        var tempPath = _dataFilePath + ".tmp";

        await using (var stream = File.Open(tempPath, FileMode.Create, FileAccess.Write, FileShare.None))
        {
            await JsonSerializer.SerializeAsync(stream, db, JsonOptions, ct);
            await stream.FlushAsync(ct);
        }

        if (File.Exists(_dataFilePath))
            File.Replace(tempPath, _dataFilePath, destinationBackupFileName: null, ignoreMetadataErrors: true);
        else
            File.Move(tempPath, _dataFilePath);
    }

    private void EnsureDirectoryExists()
    {
        var dir = Path.GetDirectoryName(_dataFilePath);
        if (!string.IsNullOrWhiteSpace(dir))
            Directory.CreateDirectory(dir);
    }

    private sealed class UserDatabase
    {
        public List<UserRecord> Users { get; set; } = new();
    }
}

public interface IPasswordHasher
{
    (byte[] Salt, byte[] Hash, int Iterations) HashPassword(string password);
    bool Verify(string password, byte[] salt, byte[] expectedHash, int iterations);
}

public sealed class Pbkdf2PasswordHasher : IPasswordHasher
{
    private const int SaltSizeBytes = 16;
    private const int HashSizeBytes = 32;
    private const int Iterations = 210_000;

    public (byte[] Salt, byte[] Hash, int Iterations) HashPassword(string password)
    {
        if (password is null) throw new ArgumentNullException(nameof(password));

        var salt = RandomNumberGenerator.GetBytes(SaltSizeBytes);
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSizeBytes);

        return (salt, hash, Iterations);
    }

    public bool Verify(string password, byte[] salt, byte[] expectedHash, int iterations)
    {
        if (password is null) throw new ArgumentNullException(nameof(password));
        if (salt is null) throw new ArgumentNullException(nameof(salt));
        if (expectedHash is null) throw new ArgumentNullException(nameof(expectedHash));
        if (iterations <= 0) throw new ArgumentOutOfRangeException(nameof(iterations));

        var actual = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256,
            expectedHash.Length);

        return CryptographicOperations.FixedTimeEquals(actual, expectedHash);
    }
}

public static class RegistrationValidator
{
    public static ValidationResult Validate(RegisterRequest request)
    {
        var errors = new List<string>();

        if (request is null)
            return ValidationResult.Fail("Request body is required.");

        var email = request.Email?.Trim() ?? "";
        var password = request.Password ?? "";
        var displayName = request.DisplayName?.Trim() ?? "";

        if (string.IsNullOrWhiteSpace(email))
            errors.Add("Email is required.");
        else if (!MailAddress.TryCreate(email, out _))
            errors.Add("Email format is invalid.");

        if (string.IsNullOrWhiteSpace(displayName))
            errors.Add("DisplayName is required.");
        else if (displayName.Length is < 2 or > 64)
            errors.Add("DisplayName must be between 2 and 64 characters.");

        if (string.IsNullOrWhiteSpace(password))
            errors.Add("Password is required.");
        else
        {
            if (password.Length < 8)
                errors.Add("Password must be at least 8 characters.");
            if (!password.Any(char.IsLetter))
                errors.Add("Password must contain at least one letter.");
            if (!password.Any(char.IsDigit))
                errors.Add("Password must contain at least one number.");
            if (password.Length > 128)
                errors.Add("Password must be at most 128 characters.");
        }

        return errors.Count == 0 ? ValidationResult.Success() : ValidationResult.Fail(errors);
    }
}

public sealed record ValidationResult(bool IsValid, IReadOnlyList<string> Errors)
{
    public static ValidationResult Success() => new(true, Array.Empty<string>());
    public static ValidationResult Fail(string error) => new(false, new[] { error });
    public static ValidationResult Fail(IEnumerable<string> errors) => new(false, errors.ToArray());

    public string ToSingleString() => string.Join(" ", Errors.Select(e => e.Trim()).Where(e => e.Length > 0));
}

public static class Normalization
{
    public static string NormalizeEmail(string email)
    {
        if (email is null) return "";
        return email.Trim().ToUpperInvariant();
    }
}