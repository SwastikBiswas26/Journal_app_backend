from functools import wraps
from flask import request, g
from bson import ObjectId
from db import get_users_collection
from utils.serializers import serialize_user
from utils.jwt_helper import extract_token_from_header, decode_token
from utils.response import error_response

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        token = extract_token_from_header(auth_header)

        if not token:
            return error_response("Authentication token is missing!", 401)

        payload, error = decode_token(token)
        if error or not payload:
            return error_response(error or "Authentication failed!", 401)

        user_id_str = payload.get("user_id")
        if not user_id_str or not ObjectId.is_valid(user_id_str):
            return error_response("Invalid token payload!", 401)

        users = get_users_collection()
        user = users.find_one({"_id": ObjectId(user_id_str)})
        
        if not user:
            return error_response("User no longer exists!", 401)

        g.current_user = serialize_user(user)
        g.user_id = str(user["_id"])

        return f(*args, **kwargs)

    return decorated
