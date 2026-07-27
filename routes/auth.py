from flask import Blueprint, request, g
from validators.auth_validator import validate_signup_data, validate_login_data
from services.auth_service import signup_user, login_user, get_user_by_id
from utils.auth_middleware import token_required
from utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    POST /api/auth/signup - User registration controller
    """
    data = request.get_json(silent=True) or {}
    validation_error = validate_signup_data(data)
    if validation_error:
        return error_response(validation_error, 400)

    result, err, status_code = signup_user(
        username=data["username"],
        email=data["email"],
        password=data["password"]
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["user"],
        message=result["message"],
        token=result["token"],
        status_code=status_code
    )

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login - User authentication controller
    """
    data = request.get_json(silent=True) or {}
    validation_error = validate_login_data(data)
    if validation_error:
        return error_response(validation_error, 400)

    identifier = data.get("email") or data.get("username")
    result, err, status_code = login_user(
        identifier=identifier,
        password=data["password"]
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["user"],
        message=result["message"],
        token=result["token"],
        status_code=status_code
    )

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me():
    """
    GET /api/auth/me - Authenticated user profile controller
    """
    user_data, err, status_code = get_user_by_id(g.user_id)
    if err:
        return error_response(err, status_code)

    return success_response(data=user_data, status_code=status_code)
