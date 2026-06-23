using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplicationBuilder.CreateBuilder(args);
builder.Services.AddControllers();

var app = builder.Build();
app.MapControllers();
app.Run();

public class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; }
    public decimal Total { get; set; }
    public DateTime OrderDate { get; set; }
}

[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    private static readonly List<Order> Orders = new()
    {
        new Order { OrderId = 1, CustomerName = "John Doe", Total = 150.00m, OrderDate = DateTime.Now.AddDays(-5) },
        new Order { OrderId = 2, CustomerName = "Jane Smith", Total = 200.50m, OrderDate = DateTime.Now.AddDays(-3) },
        new Order { OrderId = 3, CustomerName = "Bob Johnson", Total = 75.25m, OrderDate = DateTime.Now.AddDays(-1) }
    };

    [HttpGet("{orderId}")]
    public IActionResult GetOrder(int orderId)
    {
        var order = Orders.FirstOrDefault(o => o.OrderId == orderId);
        
        if (order == null)
            return NotFound(new { message = "Order not found" });

        return Ok(order);
    }
}
