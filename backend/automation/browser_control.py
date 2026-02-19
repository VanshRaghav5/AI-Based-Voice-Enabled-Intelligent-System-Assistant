import webbrowser


def open_url(url: str) -> dict:
    """
    Opens a URL in default browser.
    """
    try:
        webbrowser.open(url)

        return {
            "status": "success",
            "message": f"Opening {url}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def search_google(query: str) -> dict:
    """
    Searches a query on Google.
    """
    try:
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)

        return {
            "status": "success",
            "message": f"Searching for {query}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def open_youtube() -> dict:
    """
    Opens YouTube homepage.
    """
    try:
        webbrowser.open("https://www.youtube.com")

        return {
            "status": "success",
            "message": "Opening YouTube"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
