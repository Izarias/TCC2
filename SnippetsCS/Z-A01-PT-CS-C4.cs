using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "John Doe", Total = 150.00m, Status = "Completed" },
    new Order { OrderId = 2, CustomerName = "Jane Smith", Total = 250.00m, Status = "Pending" },
    new Order { OrderId = 3, CustomerName = "Bob Johnson", Total = 75.50m, Status = "Shipped" }
};

app.MapGet("/orders/{orderId}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);
    return order != null ? Results.Ok(order) : Results.NotFound(new { message = "Order not found" });
});

app.Run();

public class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; }
}