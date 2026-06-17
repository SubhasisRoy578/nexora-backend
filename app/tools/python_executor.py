# ==================================================
# NEXORA AI — PYTHON SANDBOX EXECUTOR
# Safe execution with:
# - Dangerous code blocking
# - Timeout protection (10 seconds)
# - Stdout/stderr capture
# - No file system or network access
# ==================================================

import sys
import io
import ast
import time
import signal
import traceback
from contextlib import redirect_stdout, redirect_stderr


# ==================================================
# BLOCKED PATTERNS
# These are dangerous — never allow execution
# ==================================================

BLOCKED_KEYWORDS = [
    "import os",
    "import sys",
    "import subprocess",
    "import socket",
    "import requests",
    "import httpx",
    "import urllib",
    "import shutil",
    "import pathlib",
    "import glob",
    "__import__",
    "open(",
    "eval(",
    "exec(",
    "compile(",
    "breakpoint(",
    "input(",
    "os.system",
    "os.popen",
    "os.remove",
    "os.rmdir",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "importlib",
    "builtins",
    "getattr(",
    "setattr(",
    "delattr(",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
]

EXECUTION_TIMEOUT = 10  # seconds
MAX_OUTPUT_LENGTH = 5000  # characters


# ==================================================
# SAFETY CHECK
# ==================================================

def is_safe_code(code: str) -> tuple:
    """
    Returns (is_safe: bool, reason: str)
    """

    code_lower = code.lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in code_lower:
            return False, f"Blocked: '{keyword}' is not allowed in sandbox."

    # AST parse check — catch syntax errors early
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    return True, "ok"


# ==================================================
# TIMEOUT HANDLER
# ==================================================

def _timeout_handler(signum, frame):
    raise TimeoutError(
        f"Code execution exceeded {EXECUTION_TIMEOUT} second limit."
    )


# ==================================================
# EXECUTE PYTHON CODE
# ==================================================

def execute_python(code: str) -> dict:
    """
    Safely executes Python code in a sandbox.
    Returns stdout, stderr, result, and execution time.
    """

    start_time = time.time()

    # --- Safety check ---
    is_safe, reason = is_safe_code(code)

    if not is_safe:
        return {
            "success": False,
            "output": "",
            "error": reason,
            "execution_time": 0,
            "code": code,
            "blocked": True
        }

    # --- Capture stdout and stderr ---
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # --- Restricted globals ---
    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "divmod": divmod,
            "isinstance": isinstance,
            "type": type,
            "repr": repr,
            "format": format,
            "chr": chr,
            "ord": ord,
            "hex": hex,
            "bin": bin,
            "oct": oct,
            "any": any,
            "all": all,
            "hash": hash,
            "id": id,
            "iter": iter,
            "next": next,
            "slice": slice,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "StopIteration": StopIteration,
            "True": True,
            "False": False,
            "None": None,
        }
    }

    # Safe math and data science imports allowed
    try:
        import math
        import random
        import json
        import datetime
        import itertools
        import functools
        import collections
        safe_globals["math"] = math
        safe_globals["random"] = random
        safe_globals["json"] = json
        safe_globals["datetime"] = datetime
        safe_globals["itertools"] = itertools
        safe_globals["functools"] = functools
        safe_globals["collections"] = collections
    except Exception:
        pass

    local_vars = {}

    # --- Set timeout (Unix only) ---
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(EXECUTION_TIMEOUT)
        use_signal = True
    except (AttributeError, OSError):
        # Windows doesn't support SIGALRM
        use_signal = False

    try:

        with redirect_stdout(stdout_capture), \
             redirect_stderr(stderr_capture):

            exec(code, safe_globals, local_vars)

        output = stdout_capture.getvalue()
        error = stderr_capture.getvalue()

        # Truncate if too long
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + "\n... [truncated]"

        execution_time = round(time.time() - start_time, 3)

        return {
            "success": True,
            "output": output,
            "error": error if error else None,
            "local_vars": {
                k: repr(v)
                for k, v in local_vars.items()
                if not k.startswith("_")
            },
            "execution_time": execution_time,
            "code": code,
            "blocked": False
        }

    except TimeoutError as e:

        return {
            "success": False,
            "output": "",
            "error": str(e),
            "execution_time": EXECUTION_TIMEOUT,
            "code": code,
            "blocked": False
        }

    except Exception as e:

        execution_time = round(time.time() - start_time, 3)

        return {
            "success": False,
            "output": stdout_capture.getvalue(),
            "error": traceback.format_exc(),
            "execution_time": execution_time,
            "code": code,
            "blocked": False
        }

    finally:

        if use_signal:
            signal.alarm(0)