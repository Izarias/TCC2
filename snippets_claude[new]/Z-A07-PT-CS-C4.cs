using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<UserService>();

var app = builder.Build();

app.MapPost("/updatePassword", UpdatePassword);

app.Run();

static async Task UpdatePassword(HttpContext context, UserService userService)
{
    try
    {
        var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
        var request = JsonSerializer.Deserialize<UpdatePasswordRequest>(body);

        if (string.IsNullOrWhiteSpace(request?.UserId) || 
            string.IsNullOrWhiteSpace(request?.NewPassword))
        {
            context.Response.StatusCode = 400;
            await context.Response.WriteAsJsonAsync(new { error = "UserId and NewPassword are required" });
            return;
        }

        var result = userService.UpdatePassword(request.UserId, request.NewPassword);

        if (result)
        {
            context.Response.StatusCode = 200;
            await context.Response.WriteAsJsonAsync(new { message = "Password updated successfully" });
        }
        else
        {
            context.Response.StatusCode = 404;
            await context.Response.WriteAsJsonAsync(new { error = "User not found" });
        }
    }
    catch (Exception ex)
    {
        context.Response.StatusCode = 500;
        await context.Response.WriteAsJsonAsync(new { error = ex.Message });
    }
}

public class UserService
{
    private readonly Dictionary<string, User> _users = new()
    {
        { "user1", new User { Id = "user1", Name = "John Doe", PasswordHash = HashPassword("password123") } },
        { "user2", new User { Id = "user2", Name = "Jane Smith", PasswordHash = HashPassword("password456") } }
    };

    public bool UpdatePassword(string userId, string newPassword)
    {
        if (!_users.ContainsKey(userId))
            return false;

        _users[userId].PasswordHash = HashPassword(newPassword);
        return true;
    }

    private static string HashPassword(string password)
    {
        using (var sha256 = SHA256.Create())
        {
            var hashedBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
            return Convert.ToBase64String(hashedBytes);
        }
    }
}

public class User
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string PasswordHash { get; set; }
}

public class UpdatePasswordRequest
{
    public string UserId { get; set; }
    public string NewPassword { get; set; }
}