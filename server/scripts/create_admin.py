#!/usr/bin/env python3
"""
Bootstrap script to create an initial admin user for Carepoint Hospital Management.
Usage:
  python -m scripts.create_admin
  or
  python scripts/create_admin.py
"""
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Add parent directory to sys.path so app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth_utils import hash_password

def create_admin():
    """Create initial admin user."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_file)

    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/carepoint")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not set in .env")
        return

    # Extract db name
    db_name = "carepoint"
    clean_uri = mongodb_uri.split("?")[0].rstrip("/")
    if "/" in clean_uri:
        candidate = clean_uri.split("/")[-1]
        if candidate and not candidate.startswith("mongodb") and ":" not in candidate:
            db_name = candidate

    kwargs = {"appName": "carepoint-hospital"}
    if "mongodb+srv" in mongodb_uri:
        kwargs["server_api"] = ServerApi("1")

    client = MongoClient(mongodb_uri, **kwargs)
    db = client[db_name]

    try:
        users_collection = db["users"]

        # Ensure indexes
        users_collection.create_index([("email", 1)], unique=True)
        users_collection.create_index(
            [("role", 1)],
            unique=True,
            partialFilterExpression={"role": "admin"}
        )

        existing_admin = users_collection.find_one({"role": "admin"})
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.get('email')}")
            return

        admin_name = os.getenv("ADMIN_NAME", "Clinic Administrator").strip()
        admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.local").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "AdminPassword123456").strip()

        if len(admin_password) < 12:
            print("ERROR: ADMIN_PASSWORD must be at least 12 characters.")
            return

        password_hash = hash_password(admin_password)
        now_iso = datetime.now(timezone.utc).isoformat()

        admin_user = {
            "name": admin_name,
            "email": admin_email,
            "passwordHash": password_hash,
            "role": "admin",
            "tokenVersion": 0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }

        result = users_collection.insert_one(admin_user)
        print(f"Initial administrator created successfully!")
        print(f"  Name:  {admin_name}")
        print(f"  Email: {admin_email}")
        print(f"  ID:    {result.inserted_id}")

    except Exception as error:
        print(f"Error creating admin: {error}")
    finally:
        client.close()

if __name__ == "__main__":
    create_admin()
