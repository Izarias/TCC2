using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using Microsoft.AspNetCore.Mvc;

namespace UserRegistration.Models
{
    public class User
    {
        public int Id { get; set; }
        
        [Required(ErrorMessage = "Nome é obrigatório")]
        [StringLength(100, MinimumLength = 3, ErrorMessage = "Nome deve ter entre 3 e 100 caracteres")]
        public string Name { get; set; }
        
        [Required(ErrorMessage = "Email é obrigatório")]
        [EmailAddress(ErrorMessage = "Email inválido")]
        public string Email { get; set; }
        
        [Required(ErrorMessage = "Senha é obrigatória")]
        [StringLength(100, MinimumLength = 6, ErrorMessage = "Senha deve ter no mínimo 6 caracteres")]
        public string Password { get; set; }
        
        [Phone(ErrorMessage = "Telefone inválido")]
        public string Phone { get; set; }
        
        public DateTime CreatedAt { get; set; }
    }
}

namespace UserRegistration.Services
{
    public interface IUserService
    {
        User Register(User user);
        User GetById(int id);
        List<User> GetAll();
    }

    public class UserService : IUserService
    {
        private static List<User> _users = new List<User>();
        private static int _nextId = 1;

        public User Register(User user)
        {
            if (user == null)
                throw new ArgumentNullException(nameof(user));

            if (_users.Any(u => u.Email == user.Email))
                throw new InvalidOperationException("Email já cadastrado");

            var context = new ValidationContext(user);
            var results = new List<ValidationResult>();
            
            if (!Validator.TryValidateObject(user, context, results, true))
            {
                var errors = string.Join(", ", results.Select(r => r.ErrorMessage));
                throw new ValidationException($"Erro de validação: {errors}");
            }

            user.Id = _nextId++;
            user.CreatedAt = DateTime.Now;
            _users.Add(user);
            
            return user;
        }

        public User GetById(int id)
        {
            var user = _users.FirstOrDefault(u => u.Id == id);
            if (user == null)
                throw new KeyNotFoundException($"Usuário com ID {id} não encontrado");
            return user;
        }

        public List<User> GetAll()
        {
            return _users;
        }
    }
}

namespace UserRegistration.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UsersController : ControllerBase
    {
        private readonly IUserService _userService;

        public UsersController(IUserService userService)
        {
            _userService = userService;
        }

        [HttpPost("register")]
        public ActionResult<User> Register([FromBody] User user)
        {
            try
            {
                var registeredUser = _userService.Register(user);
                return CreatedAtAction(nameof(GetById), new { id = registeredUser.Id }, registeredUser);
            }
            catch (InvalidOperationException ex)
            {
                return BadRequest(new { message = ex.Message });
            }
            catch (ValidationException ex)
            {
                return BadRequest(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { message = "Erro ao registrar usuário", error = ex.Message });
            }
        }

        [HttpGet("{id}")]
        public ActionResult<User> GetById(int id)
        {
            try
            {
                var user = _userService.GetById(id);
                return Ok(user);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(new { message = ex.Message });
            }
        }

        [HttpGet]
        public ActionResult<List<User>> GetAll()
        {
            var users = _userService.GetAll();
            return Ok(users);
        }
    }
}

namespace UserRegistration
{
    public class Startup
    {
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddScoped<IUserService, UserService>();
            services.AddControllers();
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseRouting();
            app.UseEndpoints(endpoints => endpoints.MapControllers());
        }
    }
}