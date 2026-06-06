using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();

var app = builder.Build();
app.MapControllers();

var users = new List<User>
{
    new User { Id = 1, Username = "john_doe", PasswordHash = HashPassword("password123") },
    new User { Id = 2, Username = "jane_smith", PasswordHash = HashPassword("secure456") }
};

app.MapPost("/api/users/{userId}/password", (int userId, [FromBody] PasswordUpdateRequest request) =>
{
    var user = users.FirstOrDefault(u => u.Id == userId);
    
    if (user == null)
        return Results.NotFound(new { message = "User not found" });
    
    if (string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "New password is required" });
    
    user.PasswordHash = HashPassword(request.NewPassword);
    
    return Results.Ok(new { message = "Password updated successfully" });
});

app.MapGet("/api/users", () => users.Select(u => new { u.Id, u.Username }));

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

class PasswordUpdateRequest
{
    public string NewPassword { get; set; }
}