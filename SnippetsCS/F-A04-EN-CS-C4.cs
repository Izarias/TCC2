using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Mvc;

// Models
public class User
{
    public int Id { get; set; }
    public string Email { get; set; }
    public string FullName { get; set; }
    public string PasswordHash { get; set; }
    public DateTime CreatedAt { get; set; }
    public bool IsActive { get; set; }
}

// DTOs
public class UserRegistrationRequest
{
    [Required(ErrorMessage = "Email is required")]
    [EmailAddress(ErrorMessage = "Invalid email format")]
    public string Email { get; set; }

    [Required(ErrorMessage = "Full name is required")]
    [StringLength(100, MinimumLength = 2, 
        ErrorMessage = "Full name must be between 2 and 100 characters")]
    public string FullName { get; set; }

    [Required(ErrorMessage = "Password is required")]
    [StringLength(100, MinimumLength = 8,
        ErrorMessage = "Password must be at least 8 characters")]
    public string Password { get; set; }

    [Required(ErrorMessage = "Password confirmation is required")]
    [Compare("Password", ErrorMessage = "Passwords do not match")]
    public string ConfirmPassword { get; set; }
}

public class UserRegistrationResponse
{
    public int Id { get; set; }
    public string Email { get; set; }
    public string FullName { get; set; }
    public bool Success { get; set; }
    public string Message { get; set; }
}

// Database Context
public class ApplicationDbContext : DbContext
{
    public DbSet<User> Users { get; set; }

    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email)
            .IsUnique();

        base.OnModelCreating(modelBuilder);
    }
}

// Service Layer
public interface IUserRegistrationService
{
    Task<UserRegistrationResponse> RegisterUserAsync(UserRegistrationRequest request);
}

public class UserRegistrationService : IUserRegistrationService
{
    private readonly ApplicationDbContext _context;

    public UserRegistrationService(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<UserRegistrationResponse> RegisterUserAsync(UserRegistrationRequest request)
    {
        try
        {
            // Check if email already exists
            var existingUser = await _context.Users
                .FirstOrDefaultAsync(u => u.Email == request.Email);

            if (existingUser != null)
            {
                return new UserRegistrationResponse
                {
                    Success = false,
                    Message = "Email is already registered"
                };
            }

            // Create new user
            var user = new User
            {
                Email = request.Email,
                FullName = request.FullName,
                PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
                CreatedAt = DateTime.UtcNow,
                IsActive = true
            };

            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            return new UserRegistrationResponse
            {
                Id = user.Id,
                Email = user.Email,
                FullName = user.FullName,
                Success = true,
                Message = "User registered successfully"
            };
        }
        catch (Exception ex)
        {
            return new UserRegistrationResponse
            {
                Success = false,
                Message = $"An error occurred during registration: {ex.Message}"
            };
        }
    }
}

// Controller
[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IUserRegistrationService _registrationService;

    public AuthController(IUserRegistrationService registrationService)
    {
        _registrationService = registrationService;
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] UserRegistrationRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(new
            {
                Success = false,
                Message = "Invalid input",
                Errors = ModelState.Values.SelectMany(v => v.Errors)
            });
        }

        var result = await _registrationService.RegisterUserAsync(request);

        if (result.Success)
        {
            return Created($"/api/auth/users/{result.Id}", result);
        }

        return BadRequest(result);
    }
}

// Startup Configuration (Program.cs or Startup.cs)
/*
services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer("YourConnectionString"));

services.AddScoped<IUserRegistrationService, UserRegistrationService>();
*/