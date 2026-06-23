// Models/Usuario.cs
using System;

namespace CadastroUsuarios.Models
{
    public class Usuario
    {
        public int Id { get; set; }
        public string Nome { get; set; }
        public string Email { get; set; }
        public string Telefone { get; set; }
        public string Senha { get; set; }
        public DateTime DataCadastro { get; set; }
        public bool Ativo { get; set; }
    }
}

// Data/AppDbContext.cs
using Microsoft.EntityFrameworkCore;
using CadastroUsuarios.Models;

namespace CadastroUsuarios.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

        public DbSet<Usuario> Usuarios { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<Usuario>(entity =>
            {
                entity.HasKey(e => e.Id);
                entity.Property(e => e.Nome).IsRequired().HasMaxLength(100);
                entity.Property(e => e.Email).IsRequired().HasMaxLength(100);
                entity.Property(e => e.Telefone).HasMaxLength(20);
                entity.Property(e => e.Senha).IsRequired();
                entity.Property(e => e.DataCadastro).HasDefaultValueSql("getdate()");
                entity.Property(e => e.Ativo).HasDefaultValue(true);
            });
        }
    }
}

// Services/UsuarioService.cs
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using CadastroUsuarios.Data;
using CadastroUsuarios.Models;
using System.Security.Cryptography;
using System.Text;

namespace CadastroUsuarios.Services
{
    public interface IUsuarioService
    {
        Task<Usuario> CadastrarAsync(Usuario usuario);
        Task<Usuario> ObterPorIdAsync(int id);
        Task<Usuario> ObterPorEmailAsync(string email);
        Task<List<Usuario>> ListarTodosAsync();
        Task<bool> AtualizarAsync(Usuario usuario);
        Task<bool> DeletarAsync(int id);
        Task<bool> ValidarEmailUnicoAsync(string email, int usuarioId = 0);
    }

    public class UsuarioService : IUsuarioService
    {
        private readonly AppDbContext _context;

        public UsuarioService(AppDbContext context)
        {
            _context = context;
        }

        public async Task<Usuario> CadastrarAsync(Usuario usuario)
        {
            if (!await ValidarEmailUnicoAsync(usuario.Email))
                throw new InvalidOperationException("Email já cadastrado.");

            usuario.Senha = CriptografarSenha(usuario.Senha);
            usuario.DataCadastro = DateTime.Now;
            usuario.Ativo = true;

            _context.Usuarios.Add(usuario);
            await _context.SaveChangesAsync();

            return usuario;
        }

        public async Task<Usuario> ObterPorIdAsync(int id)
        {
            return await _context.Usuarios.FirstOrDefaultAsync(u => u.Id == id);
        }

        public async Task<Usuario> ObterPorEmailAsync(string email)
        {
            return await _context.Usuarios.FirstOrDefaultAsync(u => u.Email == email);
        }

        public async Task<List<Usuario>> ListarTodosAsync()
        {
            return await _context.Usuarios.Where(u => u.Ativo).ToListAsync();
        }

        public async Task<bool> AtualizarAsync(Usuario usuario)
        {
            var usuarioExistente = await _context.Usuarios.FindAsync(usuario.Id);
            if (usuarioExistente == null)
                return false;

            usuarioExistente.Nome = usuario.Nome;
            usuarioExistente.Telefone = usuario.Telefone;
            usuarioExistente.Ativo = usuario.Ativo;

            if (usuarioExistente.Email != usuario.Email)
            {
                if (!await ValidarEmailUnicoAsync(usuario.Email, usuario.Id))
                    throw new InvalidOperationException("Email já cadastrado.");
                usuarioExistente.Email = usuario.Email;
            }

            _context.Usuarios.Update(usuarioExistente);
            await _context.SaveChangesAsync();

            return true;
        }

        public async Task<bool> DeletarAsync(int id)
        {
            var usuario = await _context.Usuarios.FindAsync(id);
            if (usuario == null)
                return false;

            usuario.Ativo = false;
            _context.Usuarios.Update(usuario);
            await _context.SaveChangesAsync();

            return true;
        }

        public async Task<bool> ValidarEmailUnicoAsync(string email, int usuarioId = 0)
        {
            return !await _context.Usuarios.AnyAsync(u => u.Email == email && u.Id != usuarioId);
        }

        private string CriptografarSenha(string senha)
        {
            using (var sha256 = SHA256.Create())
            {
                var hashedBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(senha));
                return Convert.ToBase64String(hashedBytes);
            }
        }
    }
}

// Controllers/UsuarioController.cs
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using CadastroUsuarios.Models;
using CadastroUsuarios.Services;

namespace CadastroUsuarios.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UsuarioController : ControllerBase
    {
        private readonly IUsuarioService _usuarioService;

        public UsuarioController(IUsuarioService usuarioService)
        {
            _usuarioService = usuarioService;
        }

        [HttpPost("cadastrar")]
        public async Task<ActionResult<Usuario>> Cadastrar([FromBody] Usuario usuario)
        {
            try
            {
                var usuarioCadastrado = await _usuarioService.CadastrarAsync(usuario);
                return CreatedAtAction(nameof(ObterPorId), new { id = usuarioCadastrado.Id }, usuarioCadastrado);
            }
            catch (InvalidOperationException ex)
            {
                return BadRequest(new { mensagem = ex.Message });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { mensagem = "Erro ao cadastrar usuário." });
            }
        }

        [HttpGet("{id}")]
        public async Task<ActionResult<Usuario>> ObterPorId(int id)
        {
            var usuario = await _usuarioService.ObterPorIdAsync(id);
            if (usuario == null)
                return NotFound();

            return Ok(usuario);
        }

        [HttpGet("email/{email}")]
        public async Task<ActionResult<Usuario>> ObterPorEmail(string email)
        {
            var usuario = await _usuarioService.ObterPorEmailAsync(email);
            if (usuario == null)
                return NotFound();

            return Ok(usuario);
        }

        [HttpGet("listar")]
        public async Task<ActionResult<List<Usuario>>> ListarTodos()
        {
            var usuarios = await _usuarioService.ListarTodosAsync();
            return Ok(usuarios);
        }

        [HttpPut("{id}")]
        public async Task<ActionResult> Atualizar(int id, [FromBody] Usuario usuario)
        {
            usuario.Id = id;

            try
            {
                var sucesso = await _usuarioService.AtualizarAsync(usuario);
                if (!sucesso)
                    return NotFound();

                return NoContent();
            }
            catch (InvalidOperationException ex)
            {
                return BadRequest(new { mensagem = ex.Message });
            }
            catch (Exception)
            {
                return StatusCode(500, new { mensagem = "Erro ao atualizar usuário." });
            }
        }

        [HttpDelete("{id}")]
        public async Task<ActionResult> Deletar(int id)
        {
            var sucesso = await _usuarioService.DeletarAsync(id);
            if (!sucesso)
                return NotFound();

            return NoContent();
        }
    }
}

// Startup.cs (ou Program.cs para .NET 6+)
using Microsoft.EntityFrameworkCore;
using CadastroUsuarios.Data;
using CadastroUsuarios.Services;

namespace CadastroUsuarios
{
    public class Startup
    {
        public IConfiguration Configuration { get; }

        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public void ConfigureServices(IServiceCollection services)
        {
            services.AddDbContext<AppDbContext>(options =>
                options.UseSqlServer(Configuration.GetConnectionString("DefaultConnection")));

            services.AddScoped<IUsuarioService, UsuarioService>();

            services.AddControllers();
            services.AddCors(options =>
            {
                options.AddPolicy("AllowAll",
                    builder =>
                    {
                        builder.AllowAnyOrigin()
                               .AllowAnyMethod()
                               .AllowAnyHeader();
                    });
            });
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseHttpsRedirection();
            app.UseRouting();
            app.UseCors("AllowAll");

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
        }
    }
}

// appsettings.json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=.;Database=CadastroUsuarios;Trusted_Connection=true;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "AllowedHosts": "*"
}