using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplicationBuilder.CreateBuilder(args);
var app = builder.Build();

var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "John Doe", Total = 150.00m },
    new Order { OrderId = 2, CustomerName = "Jane Smith", Total = 250.50m },
    new Order { OrderId = 3, CustomerName = "Bob Johnson", Total = 75.25m }
};

app.MapGet("/orders/{orderId}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);
    
    if (order == null)
        return Results.NotFound(new { message = "Order not found" });
    
    return Results.Ok(order);
});

app.Run();

class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; }
    public decimal Total { get; set; }
}