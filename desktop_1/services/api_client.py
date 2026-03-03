import requests

BASE_URL = "http://127.0.0.1:5000"

def process_command(command: str):
    return requests.post(
        f"{BASE_URL}/api/process_command",
        json={"command": command}
    )

def start_listening():
    return requests.post(f"{BASE_URL}/api/start_listening")

def stop_listening():
    return requests.post(f"{BASE_URL}/api/stop_listening")

def send_confirmation(approved: bool):
    return requests.post(
        f"{BASE_URL}/api/confirm",
        json={"approved": approved}
    )