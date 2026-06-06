using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var orders = new List<Order>
{
    new Order { Id = 1, CustomerName = "Alice", TotalAmount = 150.75m },
    new Order { Id = 2, CustomerName = "Bob", TotalAmount = 89.99m },
    new Order { Id = 3, CustomerName = "Charlie", TotalAmount = 249.50m }
};

app.MapGet("/orders/{orderId:int}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.Id == orderId);

    if (order is null)
        return Results.NotFound(new { message = $"Order with Id {orderId} not found." });

    return Results.Ok(order);
});

app.Run();

public class Order
{
    public int Id { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public decimal TotalAmount { get; set; }
}