using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.EntityFrameworkCore;

public class User
{
    public int Id { get; set; }
    public string Username { get; set; }
    public string Email { get; set; }
    public string PasswordHash { get; set; }
    public string PasswordSalt { get; set; }
    public DateTime CreatedAt { get; set; }
}

public class AppDbContext : DbContext
{
    public DbSet<User> Users { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder options)
        => options.UseSqlite("Data Source=app.db");
}

public class RegistrationValidator
{
    private const int MinUsernameLength = 3;
    private const int MaxUsernameLength = 20;
    private const int MinPasswordLength = 8;

    public List<string> Validate(string username, string email, string password)
    {
        var errors = new List<string>();

        if (string.IsNullOrWhiteSpace(username))
            errors.Add("Username is required");
        else if (username.Length < MinUsernameLength || username.Length > MaxUsernameLength)
            errors.Add($"Username must be between {MinUsernameLength} and {MaxUsernameLength} characters");
        else if (!Regex.IsMatch(username, @"^[a-zA-Z0-9_]+$"))
            errors.Add("Username can only contain letters, numbers, and underscores");

        if (string.IsNullOrWhiteSpace(email))
            errors.Add("Email is required");
        else if (!Regex.IsMatch(email, @"^[^\s@]+@[^\s@]+\.[^\s@]+$"))
            errors.Add("Invalid email format");

        if (string.IsNullOrWhiteSpace(password))
            errors.Add("Password is required");
        else if (password.Length < MinPasswordLength)
            errors.Add($"Password must be at least {MinPasswordLength} characters");

        return errors;
    }
}

public class PasswordHasher
{
    public (string hash, string salt) HashPassword(string password)
    {
        using (var rng = new RNGCryptoServiceProvider())
        {
            byte[] saltBytes = new byte[16];
            rng.GetBytes(saltBytes);

            using (var pbkdf2 = new Rfc2898DeriveBytes(password, saltBytes, 10000, HashAlgorithmName.SHA256))
            {
                byte[] hashBytes = pbkdf2.GetBytes(20);
                string salt = Convert.ToBase64String(saltBytes);
                string hash = Convert.ToBase64String(hashBytes);
                return (hash, salt);
            }
        }
    }

    public bool VerifyPassword(string password, string storedHash, string storedSalt)
    {
        byte[] saltBytes = Convert.FromBase64String(storedSalt);
        using (var pbkdf2 = new Rfc2898DeriveBytes(password, saltBytes, 10000, HashAlgorithmName.SHA256))
        {
            byte[] hashBytes = pbkdf2.GetBytes(20);
            string computedHash = Convert.ToBase64String(hashBytes);
            return computedHash == storedHash;
        }
    }
}

public class RegistrationService
{
    private readonly AppDbContext _context;
    private readonly RegistrationValidator _validator;
    private readonly PasswordHasher _hasher;

    public RegistrationService(AppDbContext context)
    {
        _context = context;
        _validator = new RegistrationValidator();
        _hasher = new PasswordHasher();
    }

    public (bool success, string message) Register(string username, string email, string password)
    {
        var validationErrors = _validator.Validate(username, email, password);
        if (validationErrors.Any())
            return (false, string.Join("; ", validationErrors));

        if (_context.Users.Any(u => u.Username == username))
            return (false, "Username already exists");

        if (_context.Users.Any(u => u.Email == email))
            return (false, "Email already registered");

        try
        {
            var (hash, salt) = _hasher.HashPassword(password);
            var user = new User
            {
                Username = username,
                Email = email,
                PasswordHash = hash,
                PasswordSalt = salt,
                CreatedAt = DateTime.UtcNow
            };

            _context.Users.Add(user);
            _context.SaveChanges();
            return (true, "Registration successful");
        }
        catch (Exception ex)
        {
            return (false, $"Registration failed: {ex.Message}");
        }
    }
}

public class Program
{
    public static void Main()
    {
        using (var context = new AppDbContext())
        {
            context.Database.EnsureCreated();
            var service = new RegistrationService(context);

            var result = service.Register("john_doe", "john@example.com", "SecurePass123");
            Console.WriteLine($"Success: {result.success}");
            Console.WriteLine($"Message: {result.message}");

            result = service.Register("john_doe", "jane@example.com", "pass");
            Console.WriteLine($"\nSuccess: {result.success}");
            Console.WriteLine($"Message: {result.message}");
        }
    }
}