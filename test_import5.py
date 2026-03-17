import sys
import os

print("Testing bcrypt")
try:
    import bcrypt
    print("bcrypt imported successfully!")
except Exception as e:
    print(f"Error: {e}")

print("Testing jwt")
try:
    import jwt
    print("jwt imported successfully!")
except Exception as e:
    print(f"Error: {e}")

print("Testing sqlalchemy")
try:
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    print("sqlalchemy imported successfully!")
except Exception as e:
    print(f"Error: {e}")
