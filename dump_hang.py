import faulthandler
import threading
import time
import sys

# output to file directly
log_file = open("hang_trace.log", "w", encoding="utf-8")
faulthandler.enable(file=log_file)

def timeout_check():
    time.sleep(3)
    print("Dumping traceback to file...")
    faulthandler.dump_traceback(file=log_file)
    log_file.flush()
    # Force exit without waiting for hanging thread
    import os
    os._exit(1)

threading.Thread(target=timeout_check, daemon=True).start()

print("Starting import...")
sys.stdout.flush()

try:
    import sqlalchemy
    print("Import successful!")
except Exception as e:
    print(f"Error: {e}")
