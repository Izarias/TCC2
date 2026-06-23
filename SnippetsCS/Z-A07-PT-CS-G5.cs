using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Simulated data store
var users = new ConcurrentDictionary<string, User>
{
    ["user1"] = new User { Username = "user1", PasswordHash = Hash("123456") },
    ["user2"] = new User { Username = "user2", PasswordHash = Hash("abcdef") }
};

app.MapPost("/users/update-password", async (HttpRequest request) =>
{
    var payload = await request.ReadFromJsonAsync<UpdatePasswordRequest>();
    if (payload == null || string.IsNullOrWhiteSpace(payload.Username) || string.IsNullOrWhiteSpace(payload.NewPassword))
        return Results.BadRequest(new { message = "Invalid request data." });

    if (!users.TryGetValue(payload.Username, out var user))
        return Results.NotFound(new { message = "User not found." });

    user.PasswordHash = Hash(payload.NewPassword);
    return Results.Ok(new { message = "Password updated successfully." });
});

app.Run();

static string Hash(string input)
{
    using var sha256 = SHA256.Create();
    var bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
    return Convert.ToBase64String(bytes);
}

record User
{
    public string Username { get; init; } = default!;
    public string PasswordHash { get; set; } = default!;
}

record UpdatePasswordRequest
{
    public string Username { get; init; } = default!;
    public string NewPassword { get; init; } = default!;
}