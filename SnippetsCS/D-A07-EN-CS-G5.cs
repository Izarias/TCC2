using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var users = new ConcurrentDictionary<int, User>();
users.TryAdd(1, new User { Id = 1, Username = "john", Password = "123456" });
users.TryAdd(2, new User { Id = 2, Username = "mary", Password = "abcdef" });

app.MapPut("/users/update-password", async (UpdatePasswordRequest request) =>
{
    if (request is null || string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "Invalid request data." });

    if (!users.TryGetValue(request.UserId, out var user))
        return Results.NotFound(new { message = "User not found." });

    user.Password = request.NewPassword; // In real apps, hash the password
    users[user.Id] = user; // Persist change in memory

    return Results.Ok(new { message = "Password updated successfully." });
});

app.Run();

record UpdatePasswordRequest(int UserId, string NewPassword);

class User
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}