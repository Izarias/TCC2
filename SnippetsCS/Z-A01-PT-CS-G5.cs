using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// In-memory data store for demonstration purposes
var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "Alice", TotalAmount = 150.75m },
    new Order { OrderId = 2, CustomerName = "Bob", TotalAmount = 89.99m },
    new Order { OrderId = 3, CustomerName = "Charlie", TotalAmount = 249.50m }
};

// Endpoint to retrieve order details by orderId
app.MapGet("/orders/{orderId:int}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);

    if (order == null)
        return Results.NotFound(new { message = "Order not found" });

    return Results.Ok(order);
});

app.Run();

public class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public decimal TotalAmount { get; set; }
}