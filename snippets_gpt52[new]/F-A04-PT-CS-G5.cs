// File: Program.cs
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using WebApp.Data;
using WebApp.Dtos;
using WebApp.Repositories;
using WebApp.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite("Data Source=app.db"));

builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService>();

builder.Services.AddEndpointsApiExplorer();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
}

app.MapPost("/users/register", async (
    [FromBody] RegisterUserRequest request,
    IUserService userService,
    CancellationToken ct) =>
{
    var validation = ValidationHelper.Validate(request);
    if (validation is not null)
        return validation;

    var result = await userService.RegisterAsync(request, ct);

    return result.Match(
        ok => Results.Created($"/users/{ok.Id}", ok),
        err => err.ToResult());
})
.WithName("RegisterUser");

app.Run();

static class ValidationHelper
{
    public static IResult? Validate<T>(T model)
    {
        if (model is null)
            return Results.BadRequest(new ProblemDetails { Title = "Invalid payload.", Detail = "Body cannot be null." });

        var ctx = new ValidationContext(model);
        var results = new List<ValidationResult>();
        var isValid = Validator.TryValidateObject(model, ctx, results, validateAllProperties: true);

        if (isValid) return null;

        var errors = results
            .GroupBy(r => (r.MemberNames?.FirstOrDefault() ?? string.Empty))
            .ToDictionary(
                g => string.IsNullOrWhiteSpace(g.Key) ? "_" : g.Key,
                g => g.Select(r => r.ErrorMessage ?? "Invalid value.").ToArray()
            );

        return Results.ValidationProblem(errors);
    }
}

// File: Data/AppDbContext.cs
namespace WebApp.Data;

using Microsoft.EntityFrameworkCore;
using WebApp.Models;

public sealed class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(b =>
        {
            b.HasKey(x => x.Id);
            b.HasIndex(x => x.Email).IsUnique();
            b.Property(x => x.Name).HasMaxLength(120).IsRequired();
            b.Property(x => x.Email).HasMaxLength(320).IsRequired();
            b.Property(x => x.PasswordHash).IsRequired();
            b.Property(x => x.CreatedAtUtc).IsRequired();
        });
    }
}

// File: Models/User.cs
namespace WebApp.Models;

public sealed class User
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = string.Empty;

    public string Email { get; set; } = string.Empty;

    public string PasswordHash { get; set; } = string.Empty;

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
}

// File: Dtos/RegisterUserRequest.cs
namespace WebApp.Dtos;

using System.ComponentModel.DataAnnotations;

public sealed record RegisterUserRequest
{
    [Required]
    [StringLength(120, MinimumLength = 2)]
    public string Name { get; init; } = string.Empty;

    [Required]
    [EmailAddress]
    [StringLength(320, MinimumLength = 5)]
    public string Email { get; init; } = string.Empty;

    [Required]
    [StringLength(72, MinimumLength = 8)]
    public string Password { get; init; } = string.Empty;
}

// File: Dtos/UserResponse.cs
namespace WebApp.Dtos;

public sealed record UserResponse(Guid Id, string Name, string Email, DateTime CreatedAtUtc);

// File: Repositories/IUserRepository.cs
namespace WebApp.Repositories;

using WebApp.Models;

public interface IUserRepository
{
    Task<User?> GetByEmailAsync(string normalizedEmail, CancellationToken ct);
    Task AddAsync(User user, CancellationToken ct);
    Task SaveChangesAsync(CancellationToken ct);
}

// File: Repositories/UserRepository.cs
namespace WebApp.Repositories;

using Microsoft.EntityFrameworkCore;
using WebApp.Data;
using WebApp.Models;

public sealed class UserRepository : IUserRepository
{
    private readonly AppDbContext _db;

    public UserRepository(AppDbContext db) => _db = db;

    public Task<User?> GetByEmailAsync(string normalizedEmail, CancellationToken ct) =>
        _db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Email == normalizedEmail, ct);

    public Task AddAsync(User user, CancellationToken ct) =>
        _db.Users.AddAsync(user, ct).AsTask();

    public Task SaveChangesAsync(CancellationToken ct) =>
        _db.SaveChangesAsync(ct);
}

// File: Services/IUserService.cs
namespace WebApp.Services;

using WebApp.Dtos;

public interface IUserService
{
    Task<Result<UserResponse>> RegisterAsync(RegisterUserRequest request, CancellationToken ct);
}

// File: Services/UserService.cs
namespace WebApp.Services;

using Microsoft.EntityFrameworkCore;
using WebApp.Dtos;
using WebApp.Models;
using WebApp.Repositories;
using WebApp.Security;

public sealed class UserService : IUserService
{
    private readonly IUserRepository _users;

    public UserService(IUserRepository users) => _users = users;

    public async Task<Result<UserResponse>> RegisterAsync(RegisterUserRequest request, CancellationToken ct)
    {
        var email = NormalizeEmail(request.Email);

        var existing = await _users.GetByEmailAsync(email, ct);
        if (existing is not null)
            return Result<UserResponse>.Fail(AppError.Conflict("Email already registered."));

        var user = new User
        {
            Id = Guid.NewGuid(),
            Name = request.Name.Trim(),
            Email = email,
            PasswordHash = PasswordHasher.Hash(request.Password),
            CreatedAtUtc = DateTime.UtcNow
        };

        try
        {
            await _users.AddAsync(user, ct);
            await _users.SaveChangesAsync(ct);
        }
        catch (DbUpdateException)
        {
            return Result<UserResponse>.Fail(AppError.Conflict("Email already registered."));
        }

        return Result<UserResponse>.Ok(new UserResponse(user.Id, user.Name, user.Email, user.CreatedAtUtc));
    }

    private static string NormalizeEmail(string email) =>
        (email ?? string.Empty).Trim().ToUpperInvariant();
}

// File: Services/Result.cs
namespace WebApp.Services;

using Microsoft.AspNetCore.Mvc;

public readonly record struct Result<T>(T? Value, AppError? Error)
{
    public bool IsSuccess => Error is null;

    public static Result<T> Ok(T value) => new(value, null);

    public static Result<T> Fail(AppError error) => new(default, error);

    public TResult Match<TResult>(Func<T, TResult> ok, Func<AppError, TResult> err) =>
        IsSuccess ? ok(Value!) : err(Error!.Value);
}

public readonly record struct AppError(string Code, string Message, int Status)
{
    public static AppError BadRequest(string message) => new("bad_request", message, StatusCodes.Status400BadRequest);
    public static AppError Conflict(string message) => new("conflict", message, StatusCodes.Status409Conflict);
    public static AppError Internal(string message) => new("internal", message, StatusCodes.Status500InternalServerError);

    public IResult ToResult()
    {
        var details = new ProblemDetails
        {
            Title = Code,
            Detail = Message,
            Status = Status
        };
        return Results.Problem(details.Detail, statusCode: details.Status, title: details.Title);
    }
}

// File: Security/PasswordHasher.cs
namespace WebApp.Security;

using System.Security.Cryptography;

public static class PasswordHasher
{
    private const int SaltSize = 16;
    private const int KeySize = 32;
    private const int Iterations = 120_000;

    public static string Hash(string password)
    {
        if (string.IsNullOrWhiteSpace(password))
            throw new ArgumentException("Password cannot be empty.", nameof(password));

        var salt = RandomNumberGenerator.GetBytes(SaltSize);
        var key = Rfc2898DeriveBytes.Pbkdf2(
            password: password,
            salt: salt,
            iterations: Iterations,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength: KeySize);

        // format: v1$iterations$base64(salt)$base64(key)
        return $"v1${Iterations}${Convert.ToBase64String(salt)}${Convert.ToBase64String(key)}";
    }

    public static bool Verify(string password, string storedHash)
    {
        if (string.IsNullOrWhiteSpace(password) || string.IsNullOrWhiteSpace(storedHash))
            return false;

        var parts = storedHash.Split('$');
        if (parts.Length != 4 || parts[0] != "v1")
            return false;

        if (!int.TryParse(parts[1], out var iterations))
            return false;

        var salt = Convert.FromBase64String(parts[2]);
        var expectedKey = Convert.FromBase64String(parts[3]);

        var actualKey = Rfc2898DeriveBytes.Pbkdf2(
            password: password,
            salt: salt,
            iterations: iterations,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength: expectedKey.Length);

        return CryptographicOperations.FixedTimeEquals(actualKey, expectedKey);
    }
}