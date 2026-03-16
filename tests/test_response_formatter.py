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