using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplicationBuilder.CreateBuilder(args);
var app = builder.Build();

var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "João Silva", TotalAmount = 150.50m, Status = "Delivered" },
    new Order { OrderId = 2, CustomerName = "Maria Santos", TotalAmount = 320.00m, Status = "Processing" },
    new Order { OrderId = 3, CustomerName = "Pedro Oliveira", TotalAmount = 89.99m, Status = "Pending" },
    new Order { OrderId = 4, CustomerName = "Ana Costa", TotalAmount = 250.75m, Status = "Shipped" }
};

app.MapGet("/api/orders/{orderId}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);
    
    if (order == null)
        return Results.NotFound(new { message = "Order not found" });
    
    return Results.Ok(order);
});

app.Run("http://localhost:5000");

class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; }
    public decimal TotalAmount { get; set; }
    public string Status { get; set; }
}