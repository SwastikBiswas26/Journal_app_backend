from bson import ObjectId

def validate_object_id(id_str):
    """
    Validates whether id_str is a valid 24-character hex MongoDB ObjectId.
    """
    if not id_str or not isinstance(id_str, str) or not ObjectId.is_valid(id_str):
        return "Invalid ID format!"
    return None

def validate_create_journal_data(data):
    """
    Validates journal creation request body.
    """
    if not isinstance(data, dict):
        return "Invalid request payload!"

    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()

    if not title:
        return "Journal title is required!"
    if len(title) > 300:
        return "Journal title cannot exceed 300 characters!"

    if not content:
        return "Journal content is required!"
    if len(content) > 100000:
        return "Journal content cannot exceed 100,000 characters!"

    return None

def validate_privacy_data(data):
    """
    Validates privacy update request body.
    """
    if not isinstance(data, dict) or "is_public" not in data:
        return "'is_public' boolean parameter is required!"
    if not isinstance(data["is_public"], bool):
        return "'is_public' must be a boolean value (true or false)!"
    return None

def validate_reaction_data(data):
    """
    Validates reaction request body (optional 'type' or 'reaction_type' field).
    """
    if data is not None and not isinstance(data, dict):
        return "Invalid reaction payload!"
    
    if data:
        reaction_type = data.get("type") or data.get("reaction_type")
        if reaction_type is not None:
            if not isinstance(reaction_type, str):
                return "Reaction type must be a string!"
            s_type = reaction_type.strip()
            if not s_type:
                return "Reaction type cannot be empty!"
            if len(s_type) > 30:
                return "Reaction type cannot exceed 30 characters!"
    return None

