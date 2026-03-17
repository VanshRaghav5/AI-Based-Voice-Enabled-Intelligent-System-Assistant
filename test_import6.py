import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

try:
    log("Importing bcrypt")
    import bcrypt

    log("Importing jwt")
    import jwt

    log("Importing hashlib")
    import hashlib

    log("Importing secrets")
    import secrets

    log("Importing os")
    import os

    log("Importing smtplib")
    import smtplib

    log("Importing datetime")
    from datetime import datetime, timedelta

    log("Importing functools")
    from functools import lru_cache

    log("Importing email.message")
    from email.message import EmailMessage

    log("Importing Session from sqlalchemy")
    from sqlalchemy.orm import Session

    log("Importing backend.database.models")
    from backend.database.models import User

    log("All done")
except Exception as e:
    log(f"Error: {e}")
