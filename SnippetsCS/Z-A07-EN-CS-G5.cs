using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// In-memory user store
var users = new ConcurrentDictionary<int, User>
{
    [1] = new User { Id = 1, Username = "alice", PasswordHash = Hash("123456") },
    [2] = new User { Id = 2, Username = "bob", PasswordHash = Hash("password") }
};

// Endpoint to update user password
app.MapPut("/users/{id:int}/password", async (int id, UpdatePasswordRequest request) =>
{
    if (!users.TryGetValue(id, out var user))
        return Results.NotFound(new { message = "User not found." });

    if (string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "New password is required." });

    user.PasswordHash = Hash(request.NewPassword);
    return Results.Ok(new { message = "Password updated successfully." });
});

app.Run();

static string Hash(string input)
{
    using var sha256 = SHA256.Create();
    var bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
    return Convert.ToBase64String(bytes);
}

record UpdatePasswordRequest(string NewPassword);

class User
{
    public int Id { get; set; }
    public string Username { get; set; } = default!;
    public string PasswordHash { get; set; } = default!;
}