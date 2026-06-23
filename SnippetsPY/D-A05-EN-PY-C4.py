def calculator():
    while True:
        try:
            expression = input("Enter expression (or 'quit' to exit): ").strip()
            
            if expression.lower() == 'quit':
                break
            
            if not expression:
                print("Error: Empty input")
                continue
            
            allowed_chars = set('0123456789+-*/().() ')
            if not all(c in allowed_chars for c in expression):
                print("Error: Invalid characters")
                continue
            
            result = eval(expression)
            print(f"Result: {result}\n")
            
        except ZeroDivisionError:
            print("Error: Division by zero\n")
        except SyntaxError:
            print("Error: Invalid expression\n")
        except Exception as e:
            print(f"Error: {type(e).__name__}\n")

if __name__ == "__main__":
    calculator()