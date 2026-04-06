import webbrowser
import re
from urllib.parse import quote_plus
import requests
from backend.tools.base_tool import BaseTool
from backend.tools.error_handler import error_handler, AutomationError
from backend.utils.logger import logger


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


def open_youtube_latest_video(query: str) -> dict:
    """Open the best/latest matching YouTube video for a query."""

    def _open_latest():
        cleaned_query = str(query or "").strip()
        if not cleaned_query:
            raise ValueError("YouTube query cannot be empty")

        search_query = f"{cleaned_query} latest video"
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

        logger.info(f"Opening latest YouTube video for query: {cleaned_query}")

        try:
            response = requests.get(search_url, headers=headers, timeout=8)
            html = response.text if response.status_code == 200 else ""

            # YouTube HTML contains repeated videoId entries; first one is usually top result.
            matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            seen = set()
            video_ids = []
            for match in matches:
                if match not in seen:
                    seen.add(match)
                    video_ids.append(match)

            if video_ids:
                selected_video_id = _select_best_video_id(video_ids, headers)
                video_url = f"https://www.youtube.com/watch?v={selected_video_id}&vq=small"
                success = webbrowser.open(video_url)
                if not success:
                    raise AutomationError(
                        "Browser failed to open YouTube video",
                        "I found the video but could not open it in your browser."
                    )

                return {
                    "status": "success",
                    "message": f"Opening latest video for {cleaned_query} on YouTube",
                    "data": {"query": cleaned_query, "url": video_url}
                }

            # Fallback: open search results if direct video resolution is unavailable.
            success = webbrowser.open(search_url)
            if not success:
                raise AutomationError(
                    "Browser failed to open YouTube search",
                    "I could not open YouTube search results in your browser."
                )

            return {
                "status": "success",
                "message": f"Opening YouTube search results for {cleaned_query}",
                "data": {"query": cleaned_query, "url": search_url}
            }

        except Exception as e:
            logger.error(f"Failed to open latest YouTube video for '{cleaned_query}': {e}")
            raise AutomationError(
                str(e),
                "I could not open the latest YouTube video right now. Please try again."
            )

    return error_handler.wrap_automation(
        func=_open_latest,
        operation_name="Open Latest YouTube Video",
        context={"query": query}
    )


def _select_best_video_id(video_ids, headers):
    """Pick a non-live candidate when possible to avoid buffering on live streams."""
    if not video_ids:
        raise ValueError("No video candidates available")

    for video_id in video_ids[:5]:
        try:
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(watch_url, headers=headers, timeout=6)
            html = response.text if response.status_code == 200 else ""
            if '"isLiveContent":true' in html or '"isLiveNow":true' in html:
                logger.info(f"Skipping live YouTube candidate: {video_id}")
                continue
            return video_id
        except Exception as exc:
            logger.debug(f"Could not validate YouTube candidate {video_id}: {exc}")

    # Fallback to first candidate if validation is inconclusive.
    return video_ids[0]


# =====================================================
# Tool Classes for Registry Integration
# =====================================================

class BrowserOpenURLTool(BaseTool):
    name = "browser.open_url"
    description = "Open a URL in default browser"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, url: str):
        """Open URL in browser"""
        return open_url(url)


class BrowserSearchGoogleTool(BaseTool):
    name = "browser.search_google"
    description = "Search Google for a query"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, query: str):
        """Search Google"""
        return search_google(query)


class BrowserOpenYouTubeTool(BaseTool):
    name = "browser.open_youtube"
    description = "Open YouTube homepage"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open YouTube"""
        return open_youtube()


class BrowserOpenYouTubeLatestVideoTool(BaseTool):
    name = "browser.open_youtube_latest_video"
    description = "Open latest matching YouTube video for a query"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, query: str):
        """Open latest YouTube video for query"""
        return open_youtube_latest_video(query)
