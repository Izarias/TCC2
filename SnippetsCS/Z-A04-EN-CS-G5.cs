using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("Default") ?? "Data Source=app.db"));

builder.Services.AddScoped<IPasswordHasher<AppUser>, PasswordHasher<AppUser>>();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
}

app.MapPost("/api/register", async (RegisterRequest request, AppDbContext db, IPasswordHasher<AppUser> hasher) =>
{
    var validationErrors = Validate(request);
    if (validationErrors.Count > 0)
        return Results.ValidationProblem(validationErrors);

    var normalizedEmail = request.Email.Trim().ToUpperInvariant();
    var normalizedUserName = request.UserName.Trim().ToUpperInvariant();

    var emailInUse = await db.Users.AnyAsync(u => u.NormalizedEmail == normalizedEmail);
    if (emailInUse)
        return Results.Conflict(new { error = "Email is already registered." });

    var userNameInUse = await db.Users.AnyAsync(u => u.NormalizedUserName == normalizedUserName);
    if (userNameInUse)
        return Results.Conflict(new { error = "Username is already taken." });

    var user = new AppUser
    {
        Id = Guid.NewGuid(),
        Email = request.Email.Trim(),
        NormalizedEmail = normalizedEmail,
        UserName = request.UserName.Trim(),
        NormalizedUserName = normalizedUserName,
        CreatedAtUtc = DateTimeOffset.UtcNow
    };

    user.PasswordHash = hasher.HashPassword(user, request.Password);

    db.Users.Add(user);

    try
    {
        await db.SaveChangesAsync();
    }
    catch (DbUpdateException)
    {
        return Results.Conflict(new { error = "A user with the same email or username already exists." });
    }

    return Results.Created($"/api/users/{user.Id}", new
    {
        id = user.Id,
        email = user.Email,
        userName = user.UserName,
        createdAtUtc = user.CreatedAtUtc
    });
});

app.Run();

static Dictionary<string, string[]> Validate(RegisterRequest request)
{
    var errors = new Dictionary<string, string[]>(StringComparer.Ordinal);

    var email = (request.Email ?? string.Empty).Trim();
    var userName = (request.UserName ?? string.Empty).Trim();
    var password = request.Password ?? string.Empty;

    if (string.IsNullOrWhiteSpace(email))
        errors["email"] = ["Email is required."];
    else if (!new EmailAddressAttribute().IsValid(email))
        errors["email"] = ["Email is not valid."];

    if (string.IsNullOrWhiteSpace(userName))
        errors["userName"] = ["Username is required."];
    else if (userName.Length is < 3 or > 32)
        errors["userName"] = ["Username must be between 3 and 32 characters."];
    else if (!userName.All(c => char.IsLetterOrDigit(c) || c is '.' or '_' or '-'))
        errors["userName"] = ["Username can contain letters, numbers, '.', '_', and '-' only."];

    if (string.IsNullOrWhiteSpace(password))
        errors["password"] = ["Password is required."];
    else
    {
        var pwErrors = new List<string>();

        if (password.Length < 8) pwErrors.Add("Password must be at least 8 characters.");
        if (!password.Any(char.IsLower)) pwErrors.Add("Password must include a lowercase letter.");
        if (!password.Any(char.IsUpper)) pwErrors.Add("Password must include an uppercase letter.");
        if (!password.Any(char.IsDigit)) pwErrors.Add("Password must include a digit.");
        if (password.Length > 128) pwErrors.Add("Password is too long.");

        if (pwErrors.Count > 0)
            errors["password"] = pwErrors.ToArray();
    }

    return errors;
}

public sealed record RegisterRequest(
    [property: Required, EmailAddress] string Email,
    [property: Required] string UserName,
    [property: Required] string Password);

public sealed class AppUser
{
    public Guid Id { get; set; }

    public string Email { get; set; } = string.Empty;
    public string NormalizedEmail { get; set; } = string.Empty;

    public string UserName { get; set; } = string.Empty;
    public string NormalizedUserName { get; set; } = string.Empty;

    public string PasswordHash { get; set; } = string.Empty;

    public DateTimeOffset CreatedAtUtc { get; set; }
}

public sealed class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<AppUser> Users => Set<AppUser>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<AppUser>(entity =>
        {
            entity.ToTable("Users");
            entity.HasKey(x => x.Id);

            entity.Property(x => x.Email).IsRequired().HasMaxLength(320);
            entity.Property(x => x.NormalizedEmail).IsRequired().HasMaxLength(320);

            entity.Property(x => x.UserName).IsRequired().HasMaxLength(32);
            entity.Property(x => x.NormalizedUserName).IsRequired().HasMaxLength(32);

            entity.Property(x => x.PasswordHash).IsRequired();
            entity.Property(x => x.CreatedAtUtc).IsRequired();

            entity.HasIndex(x => x.NormalizedEmail).IsUnique();
            entity.HasIndex(x => x.NormalizedUserName).IsUnique();
        });
    }
}