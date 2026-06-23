using Microsoft.AspNetCore.Identity;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var passwordHasher = new PasswordHasher<User>();

var users = new Dictionary<int, User>
{
    [1] = new User
    {
        Id = 1,
        Email = "user@example.com",
        PasswordHash = passwordHasher.HashPassword(null!, "old-password")
    }
};

app.MapPut("/users/{userId:int}/password", (
    int userId,
    UpdatePasswordRequest request) =>
{
    if (string.IsNullOrWhiteSpace(request.NewPassword))
        return Results.BadRequest(new { message = "New password is required." });

    if (!users.TryGetValue(userId, out var user))
        return Results.NotFound(new { message = "User not found." });

    var verificationResult = passwordHasher.VerifyHashedPassword(
        user,
        user.PasswordHash,
        request.CurrentPassword
    );

    if (verificationResult == PasswordVerificationResult.Failed)
        return Results.Unauthorized();

    user.PasswordHash = passwordHasher.HashPassword(user, request.NewPassword);

    PersistUsers(users);

    return Results.Ok(new { message = "Password updated successfully." });
});

app.Run();

static void PersistUsers(Dictionary<int, User> users)
{
    File.WriteAllText(
        "users.txt",
        string.Join(Environment.NewLine, users.Values.Select(u =>
            $"{u.Id};{u.Email};{u.PasswordHash}"))
    );
}

public sealed class User
{
    public int Id { get; set; }
    public string Email { get; set; } = "";
    public string PasswordHash { get; set; } = "";
}

public sealed record UpdatePasswordRequest(
    string CurrentPassword,
    string NewPassword
);