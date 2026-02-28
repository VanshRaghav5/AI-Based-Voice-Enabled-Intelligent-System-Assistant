import webbrowser
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


def open_url(url: str) -> dict:
    """
    Opens a URL in default browser with error handling.
    """
    
    def _open():
        # Validate URL
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Add protocol if missing
        formatted_url = url
        if not url.startswith(('http://', 'https://', 'file://')):
            formatted_url = f'https://{url}'
        
        logger.info(f"Opening URL: {formatted_url}")
        
        try:
            success = webbrowser.open(formatted_url)
            
            if not success:
                raise AutomationError(
                    "Browser failed to open URL",
                    f"I couldn't open the URL {url}. Please check if you have a default browser set."
                )
            
            return {
                "status": "success",
                "message": f"Opening {url} in browser",
                "data": {"url": formatted_url}
            }
            
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            raise AutomationError(
                str(e),
                f"Failed to open {url} in your browser. Please try again."
            )
    
    return error_handler.wrap_automation(
        func=_open,
        operation_name="Open URL",
        context={"url": url}
    )


def search_google(query: str) -> dict:
    """
    Searches a query on Google with error handling.
    """
    
    def _search():
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        logger.info(f"Searching Google for: {query}")
        
        try:
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            success = webbrowser.open(search_url)
            
            if not success:
                raise AutomationError(
                    "Browser failed to open Google search",
                    "I couldn't open Google search. Please check your browser settings."
                )
            
            return {
                "status": "success",
                "message": f"Searching Google for '{query}'",
                "data": {"query": query, "url": search_url}
            }
            
        except Exception as e:
            logger.error(f"Failed to search Google for '{query}': {e}")
            raise AutomationError(
                str(e),
                f"Failed to search for '{query}' on Google. Please try again."
            )
    
    return error_handler.wrap_automation(
        func=_search,
        operation_name="Google Search",
        context={"query": query}
    )


def open_youtube() -> dict:
    """
    Opens YouTube homepage with error handling.
    """
    
    def _open():
        logger.info("Opening YouTube")
        
        try:
            success = webbrowser.open("https://www.youtube.com")
            
            if not success:
                raise AutomationError(
                    "Browser failed to open YouTube",
                    "I couldn't open YouTube. Please check your browser and internet connection."
                )
            
            return {
                "status": "success",
                "message": "Opening YouTube",
                "data": {"url": "https://www.youtube.com"}
            }
            
        except Exception as e:
            logger.error(f"Failed to open YouTube: {e}")
            raise AutomationError(
                str(e),
                "Failed to open YouTube. Please check your internet connection and try again."
            )
    
    return error_handler.wrap_automation(
        func=_open,
        operation_name="Open YouTube",
        context={"app": "Browser"}
    )
