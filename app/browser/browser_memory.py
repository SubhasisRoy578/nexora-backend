browser_memory = []

def save_browser_memory(
    action,
    result
):

    browser_memory.append({
        "action": action,
        "result": result
    })

def get_browser_memory():

    return browser_memory