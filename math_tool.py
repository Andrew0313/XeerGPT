from sympy import sympify, solve

def math_tool(message):
    try:
        expr = sympify(message)
        result = solve(expr)
        return f"The solution is: {result}"
    except:
        return "I couldn't parse that equation. Try something like: x^2 - 4"
