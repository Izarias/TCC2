using Microsoft.AspNetCore.Builder;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var users = new List<User>
{
    new User { Id = 1, Username = "john", PasswordHash = HashPassword("oldpassword") },
    new User { Id = 2, Username = "jane", PasswordHash = HashPassword("oldpassword") }
};

app.MapPost("/api/users/{userId}/password", (int userId, PasswordUpdateRequest request) =>
{
    var user = users.FirstOrDefault(u => u.Id == userId);
    
    if (user == null)
        return Results.NotFound(new { message = "User not found" });
    
    if (string.IsNullOrWhiteSpace(request.NewPassword) || request.NewPassword.Length < 6)
        return Results.BadRequest(new { message = "Password must be at least 6 characters" });
    
    user.PasswordHash = HashPassword(request.NewPassword);
    return Results.Ok(new { message = "Password updated successfully" });
});

app.Run();

string HashPassword(string password)
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