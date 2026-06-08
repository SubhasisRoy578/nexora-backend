def execute_python(code: str):
    local_scope = {}

    try:
        exec(code, {}, local_scope)

        return {
            "success": True,
            "output": local_scope
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }