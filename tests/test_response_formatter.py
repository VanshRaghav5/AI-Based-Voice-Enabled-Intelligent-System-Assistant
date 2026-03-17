import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


from backend.core.response_formatter import ResponseFormatter


def test_response_formatter_rewrites_generic_success_messages():
    formatter = ResponseFormatter()

    result = formatter.format({
        "status": "success",
        "message": "Opening YouTube",
        "data": {"url": "https://www.youtube.com"},
    })

    assert result["message"] == "I am opening YouTube."


def test_response_formatter_adds_confirmation_instruction():
    formatter = ResponseFormatter()

    result = formatter.format({
        "status": "confirmation_required",
        "message": "Delete: C:/temp/test.txt (THIS CANNOT BE UNDONE)",
        "data": {},
    })

    assert "Say yes to proceed or no to cancel." in result["message"]


def test_response_formatter_makes_errors_clearer():
    formatter = ResponseFormatter()

    result = formatter.format({
        "status": "error",
        "message": "I did not understand that command.",
        "data": {},
    })

    assert "Please try again" in result["message"]


def test_response_formatter_summarizes_youtube_results_url_cleanly():
    formatter = ResponseFormatter()

    result = formatter.format({
        "status": "success",
        "message": "Opening YouTube search results for mr beast",
        "data": {
            "query": "mr beast",
            "url": "https://www.youtube.com/results?search_query=mr+beast"
        },
    })

    assert result["message"] == "I opened YouTube results for mr beast."


def test_response_formatter_summarizes_youtube_watch_url_cleanly():
    formatter = ResponseFormatter()

    result = formatter.format({
        "status": "success",
        "message": "Opening latest video for mr beast on YouTube",
        "data": {
            "query": "mr beast",
            "url": "https://www.youtube.com/watch?v=abc123def45&vq=small"
        },
    })

    assert result["message"] == "I opened the latest YouTube video."