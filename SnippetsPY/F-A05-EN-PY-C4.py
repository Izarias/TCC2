import math

def calculator():
    while True:
        try:
            expression = input("Enter a mathematical expression (or 'quit' to exit): ")
            
            if expression.lower() == 'quit':
                print("Calculator closed.")
                break
            
            safe_dict = {
                'abs': abs,
                'round': round,
                'pow': pow,
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'e': math.e
            }
            
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            print(f"Result: {result}\n")
        
        except ZeroDivisionError:
            print("Error: Cannot divide by zero.\n")
        except NameError:
            print("Error: Invalid function or variable.\n")
        except SyntaxError:
            print("Error: Invalid expression syntax.\n")
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    calculator()