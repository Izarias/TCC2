using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Concurrent;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Simulated data store
var users = new ConcurrentDictionary<int, User>
{
    [1] = new User { Id = 1, Username = "john", Password = "123456" },
    [2] = new User { Id = 2, Username = "mary", Password = "abcdef" }
};

app.MapPut("/users/update-password", async (HttpContext context) =>
{
    var request = await context.Request.ReadFromJsonAsync<UpdatePasswordRequest>();

    if (request == null || request.UserId <= 0 || string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "Invalid request data." });

    if (!users.TryGetValue(request.UserId, out var user))
        return Results.NotFound(new { message = "User not found." });

    user.Password = request.NewPassword;

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