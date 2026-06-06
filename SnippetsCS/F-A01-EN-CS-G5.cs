using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// In-memory order store for demonstration purposes
var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "Alice", Product = "Laptop", Quantity = 1, TotalPrice = 1200.00m },
    new Order { OrderId = 2, CustomerName = "Bob", Product = "Smartphone", Quantity = 2, TotalPrice = 1600.00m },
    new Order { OrderId = 3, CustomerName = "Charlie", Product = "Headphones", Quantity = 3, TotalPrice = 300.00m }
};

// Endpoint to retrieve order details by orderId
app.MapGet("/orders/{orderId:int}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);

    if (order == null)
    {
        return Results.NotFound(new { Message = $"Order with ID {orderId} not found." });
    }

    return Results.Ok(order);
});

app.Run();

public class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public string Product { get; set; } = string.Empty;
    public int Quantity { get; set; }
    public decimal TotalPrice { get; set; }
}