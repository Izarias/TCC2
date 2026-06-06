using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Collections.Generic;
using System.Linq;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var orders = new List<Order>
{
    new Order { OrderId = 1, CustomerName = "João Silva", Amount = 150.00m, Status = "Entregue" },
    new Order { OrderId = 2, CustomerName = "Maria Santos", Amount = 275.50m, Status = "Processando" },
    new Order { OrderId = 3, CustomerName = "Pedro Oliveira", Amount = 89.99m, Status = "Pendente" },
    new Order { OrderId = 4, CustomerName = "Ana Costa", Amount = 420.00m, Status = "Entregue" }
};

app.MapGet("/orders/{orderId}", (int orderId) =>
{
    var order = orders.FirstOrDefault(o => o.OrderId == orderId);
    
    if (order == null)
        return Results.NotFound(new { message = $"Pedido {orderId} não encontrado" });
    
    return Results.Ok(order);
});

app.Run();

class Order
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; }
    public decimal Amount { get; set; }
    public string Status { get; set; }
}