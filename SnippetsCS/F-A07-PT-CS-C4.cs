using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();

var app = builder.Build();
app.UseRouting();
app.MapControllers();
app.Run();

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private static List<User> users = new()
    {
        new User { Id = 1, Username = "john_doe", Password = "hash_pwd123" },
        new User { Id = 2, Username = "jane_smith", Password = "hash_pwd456" }
    };

    [HttpPost("{id}/update-password")]
    public IActionResult UpdatePassword(int id, [FromBody] PasswordUpdateRequest request)
    {
        if (string.IsNullOrWhiteSpace(request?.NewPassword))
            return BadRequest(new { message = "New password is required" });

        var user = users.FirstOrDefault(u => u.Id == id);
        if (user == null)
            return NotFound(new { message = "User not found" });

        user.Password = HashPassword(request.NewPassword);

        return Ok(new { message = "Password updated successfully", userId = user.Id });
    }

    private static string HashPassword(string password)
    {
        return Convert.ToBase64String(System.Security.Cryptography.SHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(password)));
    }
}

public class User
{
    public int Id { get; set; }
    public string Username { get; set; }
    public string Password { get; set; }
}

public class PasswordUpdateRequest
{
    public string NewPassword { get; set; }
}