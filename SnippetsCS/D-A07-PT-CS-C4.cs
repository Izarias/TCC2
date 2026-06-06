using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var users = new List<User>
{
    new User { Id = 1, Username = "john", PasswordHash = HashPassword("password123") },
    new User { Id = 2, Username = "jane", PasswordHash = HashPassword("securepass456") }
};

app.MapPost("/api/users/{userId}/change-password", async (int userId, [FromBody] ChangePasswordRequest request) =>
{
    if (string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "New password is required" });

    var user = users.FirstOrDefault(u => u.Id == userId);
    if (user == null)
        return Results.NotFound(new { message = "User not found" });

    user.PasswordHash = HashPassword(request.NewPassword);

    return Results.Ok(new { message = "Password updated successfully", userId = user.Id });
});

app.MapPost("/api/auth/register", async (context) =>
{
    var request = await context.Request.ReadAsAsync<RegisterRequest>();

    if (string.IsNullOrWhiteSpace(request.Username) || string.IsNullOrWhiteSpace(request.Password))
        return Results.BadRequest(new { message = "Username and password are required" });

    if (users.Any(u => u.Username == request.Username))
        return Results.Conflict(new { message = "Username already exists" });

    var newUser = new User 
    { 
        Id = users.Count + 1, 
        Username = request.Username, 
        PasswordHash = HashPassword(request.Password) 
    };

    users.Add(newUser);
    return Results.Created($"/api/users/{newUser.Id}", new { userId = newUser.Id, username = newUser.Username });
});

app.MapGet("/api/users/{userId}", (int userId) =>
{
    var user = users.FirstOrDefault(u => u.Id == userId);
    if (user == null)
        return Results.NotFound();

    return Results.Ok(new { userId = user.Id, username = user.Username });
});

app.Run();

static string HashPassword(string password)
{
    using (var sha256 = SHA256.Create())
    {
        var hashedBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
        return Convert.ToBase64String(hashedBytes);
    }
}

class User
{
    public int Id { get; set; }
    public string Username { get; set; }
    public string PasswordHash { get; set; }
}

class ChangePasswordRequest
{
    public string NewPassword { get; set; }
}

class RegisterRequest
{
    public string Username { get; set; }
    public string Password { get; set; }
}
