using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

var builder = WebApplicationBuilder.CreateBuilder(args);
var app = builder.Build();

var orders = new Dictionary<int, Order>
{
    { 1, new Order { OrderId = 1, CustomerId = 101, Amount = 250.50m, Status = "Shipped" } },
    { 2, new Order { OrderId = 2, CustomerId = 102, Amount = 175.00m, Status = "Processing" } },
    { 3, new Order { OrderId = 3, CustomerId = 103, Amount = 450.75m, Status = "Delivered" } },
    { 4, new Order { OrderId = 4, CustomerId = 104, Amount = 320.25m, Status = "Pending" } }
};

app.MapGet("/orders/{orderId}", (int orderId) =>
{
    if (orders.TryGetValue(orderId, out var order))
    {
        return Results.Ok(order);
    }
    return Results.NotFound(new { message = "Order not found" });
});

app.Run("http://localhost:5000");

class Order
{
    public int OrderId { get; set; }
    public int CustomerId { get; set; }
    public decimal Amount { get; set; }
    public string Status { get; set; }
}