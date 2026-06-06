using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var orders = new Dictionary<int, Order>
{
    [1] = new Order(1, "Pedro Augusto", "Processing", 149.90m, new[] { "Keyboard", "Mouse" }),
    [2] = new Order(2, "Maria Silva", "Shipped", 299.50m, new[] { "Monitor" }),
    [3] = new Order(3, "John Doe", "Delivered", 89.99m, new[] { "USB-C Cable", "Laptop Stand" })
};

app.MapGet("/orders/{orderId:int}", (int orderId) =>
{
    if (!orders.TryGetValue(orderId, out var order))
        return Results.NotFound(new { message = $"Order with id {orderId} was not found." });

    return Results.Ok(order);
});

app.Run();

record Order(int OrderId, string CustomerName, string Status, decimal TotalAmount, string[] Items);