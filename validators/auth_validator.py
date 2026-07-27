import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_signup_data(data):
    """
    Validates signup request body.
    Returns None if valid, or error string if invalid.
    """
    if not isinstance(data, dict):
        return "Invalid request body!"

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not username:
        return "Username is required!"
    if len(username) < 3:
        return "Username must be at least 3 characters long!"
    if len(username) > 50:
        return "Username cannot exceed 50 characters!"

    if not email:
        return "Email is required!"
    if len(email) > 100:
        return "Email cannot exceed 100 characters!"
    if not EMAIL_REGEX.match(email):
        return "Please provide a valid email address!"

    if not password:
        return "Password is required!"
    if len(password) < 6:
        return "Password must be at least 6 characters long!"
    if len(password) > 128:
        return "Password cannot exceed 128 characters!"

    return None

def validate_login_data(data):
    """
    Validates login request body.
    Returns None if valid, or error string if invalid.
    """
    if not isinstance(data, dict):
        return "Invalid request body!"

    identifier = str(data.get("email") or data.get("username") or "").strip()
    password = str(data.get("password", "")).strip()

    if not identifier:
        return "Email or username is required!"
    if not password:
        return "Password is required!"

    return None
