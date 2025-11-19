"""
Database Helper Functions

MongoDB helper functions ready to use in your backend code.
Import and use these functions in your API endpoints for database operations.
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from typing import Union, Optional, Dict, Any, List
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

_client = None
db = None

database_url = os.getenv("DATABASE_URL")
database_name = os.getenv("DATABASE_NAME")

if database_url and database_name:
    _client = MongoClient(database_url)
    db = _client[database_name]

# Helper functions for common database operations
def _ensure_db():
    if db is None:
        raise Exception("Database not available. Check DATABASE_URL and DATABASE_NAME environment variables.")


def _model_to_dict(data: Union[BaseModel, dict]) -> dict:
    if isinstance(data, BaseModel):
        return data.model_dump()
    return data.copy()


def create_document(collection_name: str, data: Union[BaseModel, dict]) -> str:
    """Insert a single document with timestamp"""
    _ensure_db()
    data_dict = _model_to_dict(data)
    now = datetime.now(timezone.utc)
    data_dict['created_at'] = now
    data_dict['updated_at'] = now
    result = db[collection_name].insert_one(data_dict)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: Optional[dict] = None, limit: Optional[int] = None) -> List[dict]:
    """Get documents from collection"""
    _ensure_db()
    cursor = db[collection_name].find(filter_dict or {})
    if limit:
        cursor = cursor.limit(limit)
    docs = []
    for d in cursor:
        d["_id"] = str(d["_id"])  # stringify
        docs.append(d)
    return docs


def get_document_by_id(collection_name: str, doc_id: str) -> Optional[dict]:
    _ensure_db()
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return None
    d = db[collection_name].find_one({"_id": obj_id})
    if d:
        d["_id"] = str(d["_id"])
    return d


def find_one(collection_name: str, filter_dict: Dict[str, Any]) -> Optional[dict]:
    _ensure_db()
    d = db[collection_name].find_one(filter_dict)
    if d:
        d["_id"] = str(d["_id"])
    return d


def update_document(collection_name: str, doc_id: str, update_data: Dict[str, Any]) -> bool:
    _ensure_db()
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return False
    update_data = _model_to_dict(update_data)
    update_data['updated_at'] = datetime.now(timezone.utc)
    res = db[collection_name].update_one({"_id": obj_id}, {"$set": update_data})
    return res.modified_count > 0


def push_to_array(collection_name: str, doc_id: str, array_field: str, value: Any) -> bool:
    _ensure_db()
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        return False
    res = db[collection_name].update_one({"_id": obj_id}, {"$push": {array_field: value}, "$set": {"updated_at": datetime.now(timezone.utc)}})
    return res.modified_count > 0


def upsert_one(collection_name: str, filter_dict: Dict[str, Any], data: Dict[str, Any]) -> dict:
    _ensure_db()
    now = datetime.now(timezone.utc)
    data = _model_to_dict(data)
    data['updated_at'] = now
    update_doc = {"$set": data, "$setOnInsert": {"created_at": now}}
    res = db[collection_name].find_one_and_update(filter_dict, update_doc, upsert=True, return_document=True)
    # find_one_and_update with return_document=True requires ReturnDocument; to keep it simple, do two-step
    d = db[collection_name].find_one(filter_dict)
    if d:
        d["_id"] = str(d["_id"])
    return d or {}
