def open_website(url: str):
    
    return {
        "status": "success",
        "action": "open_website",
        "url": url
    }


def search_google(query: str):

    return {
        "status": "success",
        "action": "google_search",
        "query": query
    }


def fill_form(data: dict):

    return {
        "status": "success",
        "action": "form_fill",
        "data": data
    }