import logging
import os
import sys
import io


def log(message: str):
    print(f"[OmniAssist] {message}")

LOG_DIR = os.path.join("backend", "data")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "assistant.log")

# Stream handler with UTF-8 encoding to prevent UnicodeEncodeError on Windows
try:
    stdout_fileno = sys.stdout.fileno()
    stream = open(stdout_fileno, mode='w', encoding='utf-8', buffering=1, closefd=False)
except (io.UnsupportedOperation, AttributeError, OSError):
    # Fallback to using sys.stdout directly if fileno() is not available or cannot be reopened
    stream = sys.stdout

stream_handler = logging.StreamHandler(stream=stream)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        stream_handler
    ]
)

logger = logging.getLogger("Assistant")
