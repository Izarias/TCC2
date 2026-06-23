using System.ComponentModel.DataAnnotations;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<AppDbContext>(opt =>
{
    opt.UseSqlite(builder.Configuration.GetConnectionString("Default") ?? "Data Source=app.db");
});

builder.Services.AddEndpointsApiExplorer();

var app = builder.Build();

await using (var scope = app.Services.CreateAsyncScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.EnsureCreatedAsync();
}

app.MapPost("/users/register", async Task<Results<Created<UserResponse>, ValidationProblem, Conflict<string>>> (
    RegisterRequest req,
    AppDbContext db,
    CancellationToken ct) =>
{
    var errors = Validate(req);
    if (errors.Count > 0) return TypedResults.ValidationProblem(errors);

    var emailNorm = NormalizeEmail(req.Email);

    var exists = await db.Users.AnyAsync(u => u.EmailNormalized == emailNorm, ct);
    if (exists) return TypedResults.Conflict("E-mail já cadastrado.");

    var (hash, salt, iterations) = PasswordHasher.Hash(req.Password);

    var user = new User
    {
        Id = Guid.NewGuid(),
        Name = req.Name.Trim(),
        Email = req.Email.Trim(),
        EmailNormalized = emailNorm,
        PasswordHash = hash,
        PasswordSalt = salt,
        PasswordIterations = iterations,
        CreatedAtUtc = DateTimeOffset.UtcNow
    };

    db.Users.Add(user);
    await db.SaveChangesAsync(ct);

    return TypedResults.Created($"/users/{user.Id}", new UserResponse
    {
        Id = user.Id,
        Name = user.Name,
        Email = user.Email,
        CreatedAtUtc = user.CreatedAtUtc
    });
});

app.MapGet("/users/{id:guid}", async Task<Results<Ok<UserResponse>, NotFound>> (Guid id, AppDbContext db, CancellationToken ct) =>
{
    var user = await db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Id == id, ct);
    if (user is null) return TypedResults.NotFound();

    return TypedResults.Ok(new UserResponse
    {
        Id = user.Id,
        Name = user.Name,
        Email = user.Email,
        CreatedAtUtc = user.CreatedAtUtc
    });
});

app.Run();

static Dictionary<string, string[]> Validate(RegisterRequest req)
{
    var results = new List<ValidationResult>();
    var context = new ValidationContext(req);
    Validator.TryValidateObject(req, context, results, validateAllProperties: true);

    var errors = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
    foreach (var r in results)
    {
        var members = r.MemberNames?.Any() == true ? r.MemberNames : new[] { "" };
        foreach (var m in members)
        {
            if (!errors.TryGetValue(m, out var list))
            {
                list = new List<string>();
                errors[m] = list;
            }
            list.Add(r.ErrorMessage ?? "Valor inválido.");
        }
    }

    // Regras extras
    if (!string.IsNullOrWhiteSpace(req.Password) && req.Password.Length < 8)
    {
        if (!errors.TryGetValue(nameof(RegisterRequest.Password), out var list))
        {
            list = new List<string>();
            errors[nameof(RegisterRequest.Password)] = list;
        }
        list.Add("A senha deve ter pelo menos 8 caracteres.");
    }

    return errors.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToArray(), StringComparer.OrdinalIgnoreCase);
}

static string NormalizeEmail(string email) => email.Trim().ToUpperInvariant();

public sealed class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }
    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var u = modelBuilder.Entity<User>();

        u.HasKey(x => x.Id);

        u.Property(x => x.Name).HasMaxLength(200).IsRequired();
        u.Property(x => x.Email).HasMaxLength(320).IsRequired();
        u.Property(x => x.EmailNormalized).HasMaxLength(320).IsRequired();

        u.Property(x => x.PasswordHash).IsRequired();
        u.Property(x => x.PasswordSalt).IsRequired();
        u.Property(x => x.PasswordIterations).IsRequired();

        u.Property(x => x.CreatedAtUtc).IsRequired();

        u.HasIndex(x => x.EmailNormalized).IsUnique();
    }
}

public sealed class User
{
    public Guid Id { get; set; }

    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public string EmailNormalized { get; set; } = "";

    public byte[] PasswordHash { get; set; } = Array.Empty<byte>();
    public byte[] PasswordSalt { get; set; } = Array.Empty<byte>();
    public int PasswordIterations { get; set; }

    public DateTimeOffset CreatedAtUtc { get; set; }
}

public sealed class RegisterRequest
{
    [Required(ErrorMessage = "Nome é obrigatório.")]
    [MinLength(2, ErrorMessage = "Nome deve ter pelo menos 2 caracteres.")]
    [MaxLength(200, ErrorMessage = "Nome excede o limite de 200 caracteres.")]
    public string Name { get; set; } = "";

    [Required(ErrorMessage = "E-mail é obrigatório.")]
    [EmailAddress(ErrorMessage = "E-mail inválido.")]
    [MaxLength(320, ErrorMessage = "E-mail excede o limite de 320 caracteres.")]
    public string Email { get; set; } = "";

    [Required(ErrorMessage = "Senha é obrigatória.")]
    [MaxLength(200, ErrorMessage = "Senha excede o limite de 200 caracteres.")]
    public string Password { get; set; } = "";
}

public sealed class UserResponse
{
    public Guid Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public DateTimeOffset CreatedAtUtc { get; set; }
}

public static class PasswordHasher
{
    private const int SaltSizeBytes = 16;
    private const int HashSizeBytes = 32; // 256-bit
    private const int DefaultIterations = 150_000;

    public static (byte[] hash, byte[] salt, int iterations) Hash(string password)
    {
        if (password is null) throw new ArgumentNullException(nameof(password));

        var salt = RandomNumberGenerator.GetBytes(SaltSizeBytes);

        using var pbkdf2 = new Rfc2898DeriveBytes(
            password: password,
            salt: salt,
            iterations: DefaultIterations,
            hashAlgorithm: HashAlgorithmName.SHA256);

        var hash = pbkdf2.GetBytes(HashSizeBytes);
        return (hash, salt, DefaultIterations);
    }

    public static bool Verify(string password, byte[] expectedHash, byte[] salt, int iterations)
    {
        if (password is null) return false;
        if (expectedHash is null || expectedHash.Length == 0) return false;
        if (salt is null || salt.Length == 0) return false;
        if (iterations <= 0) return false;

        using var pbkdf2 = new Rfc2898DeriveBytes(
            password: password,
            salt: salt,
            iterations: iterations,
            hashAlgorithm: HashAlgorithmName.SHA256);

        var actualHash = pbkdf2.GetBytes(expectedHash.Length);
        return CryptographicOperations.FixedTimeEquals(actualHash, expectedHash);
    }
}