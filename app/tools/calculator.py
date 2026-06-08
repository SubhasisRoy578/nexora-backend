def calculate(expression: str):

    try:

        result = eval(
            expression,
            {"__builtins__": {}},
            {}
        )

        return str(result)

    except Exception as e:

        return f"Calculation Error: {e}"