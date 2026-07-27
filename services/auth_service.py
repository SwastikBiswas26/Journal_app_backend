from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from db import get_users_collection
from utils.serializers import serialize_user
from utils.jwt_helper import generate_token

def signup_user(username, email, password):
    """
    Registers a new user in MongoDB.
    Returns (result_dict, error_message, status_code)
    """
    users = get_users_collection()

    clean_email = str(email).strip().lower()
    clean_username = str(username).strip()
    username_lower = clean_username.lower()

    # Check existing email
    if users.find_one({"email": clean_email}):
        return None, "Email is already registered!", 400

    # Check existing username (case-insensitive check using username_lower or exact match)
    if users.find_one({"$or": [{"username_lower": username_lower}, {"username": clean_username}]}):
        return None, "Username is already taken!", 400

    hashed_password = generate_password_hash(str(password))
    user_doc = {
        "username": clean_username,
        "username_lower": username_lower,
        "email": clean_email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc)
    }

    result = users.insert_one(user_doc)
    user_id = result.inserted_id
    user_doc["_id"] = user_id

    token = generate_token(user_id)
    user_data = serialize_user(user_doc)

    return {
        "message": "User registered successfully",
        "token": token,
        "user": user_data
    }, None, 201

def login_user(identifier, password):
    """
    Authenticates a user via email or username.
    Returns (result_dict, error_message, status_code)
    """
    users = get_users_collection()
    clean_identifier = str(identifier).strip()
    identifier_lower = clean_identifier.lower()

    # Match by email (lowercase) OR username (case-insensitive via username_lower or username)
    user = users.find_one({
        "$or": [
            {"email": identifier_lower},
            {"username_lower": identifier_lower},
            {"username": clean_identifier}
        ]
    })

    if not user or not check_password_hash(user["password"], str(password)):
        return None, "Invalid email/username or password!", 401

    token = generate_token(user["_id"])
    user_data = serialize_user(user)

    return {
        "message": "Login successful",
        "token": token,
        "user": user_data
    }, None, 200

def get_user_by_id(user_id_str):
    """
    Fetches user profile by ObjectId string.
    """
    if not user_id_str or not isinstance(user_id_str, str) or not ObjectId.is_valid(user_id_str):
        return None, "Invalid user ID format!", 400

    users = get_users_collection()
    user = users.find_one({"_id": ObjectId(user_id_str)})

    if not user:
        return None, "User not found!", 404

    return serialize_user(user), None, 200
