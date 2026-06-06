using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// In-memory user store (for demo purposes)
var users = new ConcurrentDictionary<int, User>();
users.TryAdd(1, new User { Id = 1, Username = "john.doe", Password = "123456" });
users.TryAdd(2, new User { Id = 2, Username = "jane.smith", Password = "abcdef" });

// Endpoint to update user password
app.MapPut("/users/{id}/password", async (int id, UpdatePasswordRequest request) =>
{
    if (string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "New password must be provided." });

    if (!users.TryGetValue(id, out var user))
        return Results.NotFound(new { message = "User not found." });

    if (user.Password != request.CurrentPassword)
        return Results.BadRequest(new { message = "Current password is incorrect." });

    user.Password = request.NewPassword;
    users[id] = user;

    return Results.Ok(new { message = "Password updated successfully." });
});

app.Run();

record User
{
    public int Id { get; init; }
    public string Username { get; init; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

record UpdatePasswordRequest
{
    public string CurrentPassword { get; init; } = string.Empty;
    public string NewPassword { get; init; } = string.Empty;
}