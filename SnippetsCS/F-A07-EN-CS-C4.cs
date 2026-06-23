using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();

var app = builder.Build();
app.MapControllers();
app.Run();

class User
{
    public int Id { get; set; }
    public string Username { get; set; }
    public string Password { get; set; }
}

class PasswordUpdateRequest
{
    public int UserId { get; set; }
    public string NewPassword { get; set; }
}

static class UserDatabase
{
    public static List<User> Users = new()
    {
        new User { Id = 1, Username = "john_doe", Password = "oldpass123" },
        new User { Id = 2, Username = "jane_smith", Password = "securepass456" }
    };
}

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpPost("password-update")]
    public IActionResult UpdatePassword([FromBody] PasswordUpdateRequest request)
    {
        if (request == null || request.UserId <= 0 || string.IsNullOrWhiteSpace(request.NewPassword))
            return BadRequest(new { error = "Invalid request data" });

        if (request.NewPassword.Length < 6)
            return BadRequest(new { error = "Password must be at least 6 characters" });

        var user = UserDatabase.Users.FirstOrDefault(u => u.Id == request.UserId);
        if (user == null)
            return NotFound(new { error = "User not found" });

        user.Password = request.NewPassword;

        return Ok(new { message = "Password updated successfully", userId = user.Id });
    }
}