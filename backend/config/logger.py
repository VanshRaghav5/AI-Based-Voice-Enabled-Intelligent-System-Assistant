import logging
import os
import sys


LOG_DIR = os.path.join("backend", "data")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "assistant.log")

# Stream handler with UTF-8 encoding to prevent UnicodeEncodeError on Windows
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        stream_handler
    ]
)

logger = logging.getLogger("Assistant")
