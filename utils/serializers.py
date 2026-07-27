from bson import ObjectId
from datetime import datetime

def serialize_doc(doc):
    """
    Converts a MongoDB document into a JSON-friendly dictionary.
    Replaces '_id' with 'id' as a string and converts datetime/ObjectId fields.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if not isinstance(doc, dict):
        return doc

    serialized = {}
    for key, value in doc.items():
        if key == "_id":
            serialized["id"] = str(value)
        elif isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_doc(item) for item in value]
        else:
            serialized[key] = value
    return serialized

def serialize_user(user_doc):
    """
    Serializes user document and removes sensitive data like password hash and lowercased helper fields.
    """
    if not user_doc or not isinstance(user_doc, dict):
        return None
    data = serialize_doc(user_doc)
    data.pop("password", None)
    data.pop("username_lower", None)
    return data
