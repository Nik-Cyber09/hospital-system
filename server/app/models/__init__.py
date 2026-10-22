from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo import ReturnDocument

class User:
    """User model for MongoDB."""

    def __init__(self, db):
        self.collection = db["users"]

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.collection.create_index([("email", 1)], unique=True)
        await self.collection.create_index(
            [("role", 1)],
            unique=True,
            partialFilterExpression={"role": "admin"}
        )

    async def create(self, name: str, email: str, password_hash: str, role: str) -> Dict[str, Any]:
        """Create a new user."""
        now_iso = datetime.now(timezone.utc).isoformat()
        user = {
            "name": name,
            "email": email.lower(),
            "passwordHash": password_hash,
            "role": role,
            "tokenVersion": 0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
        result = await self.collection.insert_one(user)
        user["_id"] = result.inserted_id
        return user

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email."""
        return await self.collection.find_one({"email": email.lower()})

    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a user by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    async def find_all(self) -> List[Dict[str, Any]]:
        """Get all users (for admin staff list)."""
        cursor = self.collection.find({}).sort("createdAt", -1)
        return await cursor.to_list(length=None)

    async def update_password(self, user_id: str, password_hash: str, token_version: int):
        """Update password hash and increment token version."""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "passwordHash": password_hash,
                    "tokenVersion": token_version,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                }
            }
        )

    async def exists_by_role(self, role: str) -> bool:
        """Check if a user with role exists."""
        return await self.collection.find_one({"role": role}) is not None


class HospitalRecord:
    """HospitalRecord model for MongoDB."""

    def __init__(self, db):
        self.collection = db["hospitalrecords"]

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.collection.create_index([("type", 1), ("id", 1)], unique=True)

    async def create(self, record_type: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        now_iso = datetime.now(timezone.utc).isoformat()
        record = {
            "type": record_type,
            "id": record_id,
            "data": data,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
        result = await self.collection.insert_one(record)
        record["_id"] = result.inserted_id
        return record

    async def find_by_type(self, record_type: str) -> List[Dict[str, Any]]:
        """Find all records of a type."""
        cursor = self.collection.find({"type": record_type}).sort("createdAt", -1)
        return await cursor.to_list(length=None)

    async def find_one(self, record_type: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Find a single record."""
        return await self.collection.find_one({"type": record_type, "id": record_id})

    async def update_one(self, record_type: str, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record."""
        result = await self.collection.find_one_and_update(
            {"type": record_type, "id": record_id},
            {
                "$set": {
                    "data": data,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                }
            },
            return_document=ReturnDocument.AFTER
        )
        return result

    async def delete_one(self, record_type: str, record_id: str):
        """Delete a record."""
        await self.collection.delete_one({"type": record_type, "id": record_id})

    async def find_dependents(self, filter_query: Dict) -> bool:
        """Check if dependent records exist."""
        return await self.collection.find_one(filter_query) is not None
