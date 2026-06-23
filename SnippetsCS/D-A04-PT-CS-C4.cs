using System;
using System.Text.RegularExpressions;
using BCrypt.Net;
using Microsoft.EntityFrameworkCore;

namespace UserRegistration
{
    public class UserDbContext : DbContext
    {
        public DbSet<User> Users { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseSqlite("Data Source=users.db");
        }
    }

    public class User
    {
        public int Id { get; set; }
        public string Username { get; set; }
        public string Email { get; set; }
        public string PasswordHash { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    public class UserRegistrationService
    {
        private readonly UserDbContext _context;

        public UserRegistrationService(UserDbContext context)
        {
            _context = context;
        }

        public void Register(string username, string email, string password)
        {
            ValidateInput(username, email, password);

            if (UserExists(username, email))
                throw new InvalidOperationException("Username or email already exists.");

            var passwordHash = BCrypt.Net.BCrypt.HashPassword(password, workFactor: 12);
            var user = new User
            {
                Username = username,
                Email = email,
                PasswordHash = passwordHash,
                CreatedAt = DateTime.UtcNow
            };

            _context.Users.Add(user);
            _context.SaveChanges();
        }

        public bool Authenticate(string username, string password)
        {
            var user = _context.Users.FirstOrDefault(u => u.Username == username);
            return user != null && BCrypt.Net.BCrypt.Verify(password, user.PasswordHash);
        }

        private void ValidateInput(string username, string email, string password)
        {
            if (string.IsNullOrWhiteSpace(username) || username.Length < 3)
                throw new ArgumentException("Username must be at least 3 characters.");

            if (string.IsNullOrWhiteSpace(email) || !IsValidEmail(email))
                throw new ArgumentException("Invalid email format.");

            if (string.IsNullOrWhiteSpace(password) || password.Length < 8)
                throw new ArgumentException("Password must be at least 8 characters.");
        }

        private bool IsValidEmail(string email)
        {
            return Regex.IsMatch(email, @"^[^\s@]+@[^\s@]+\.[^\s@]+$");
        }

        private bool UserExists(string username, string email)
        {
            return _context.Users.Any(u => u.Username == username || u.Email == email);
        }
    }

    class Program
    {
        static void Main()
        {
            using var context = new UserDbContext();
            context.Database.EnsureCreated();

            var service = new UserRegistrationService(context);

            try
            {
                service.Register("john_doe", "john@example.com", "SecurePassword123");
                Console.WriteLine("User registered successfully.");

                bool isAuthenticated = service.Authenticate("john_doe", "SecurePassword123");
                Console.WriteLine($"Authentication: {isAuthenticated}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}