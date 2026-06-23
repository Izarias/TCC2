def calculator():
    while True:
        try:
            expression = input("Enter a mathematical expression (or 'quit' to exit): ")
            
            if expression.lower() == 'quit':
                print("Goodbye!")
                break
            
            result = eval(expression)
            print(f"Result: {result}")
        except ZeroDivisionError:
            print("Error: Division by zero")
        except SyntaxError:
            print("Error: Invalid expression")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    calculator()