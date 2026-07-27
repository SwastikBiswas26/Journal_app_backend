from flask import Blueprint, request, g
from validators.journal_validator import (
    validate_object_id,
    validate_create_journal_data,
    validate_privacy_data,
    validate_reaction_data
)
from services.journal_service import (
    fetch_public_feed,
    create_journal_entry,
    fetch_user_journals,
    get_journal_detail,
    update_journal_privacy,
    update_journal_entry,
    delete_journal_entry,
    add_or_toggle_reaction,
    remove_reaction,
    get_post_reactions_detail
)
from utils.auth_middleware import token_required
from utils.response import success_response, error_response

journal_bp = Blueprint("journal", __name__, url_prefix="/api/journals")

@journal_bp.route("/feed", methods=["GET"])
def get_feed():
    """
    GET /api/journals/feed - Community Public Journal Feed controller
    """
    try:
        limit = int(request.args.get("limit", 20))
        skip = int(request.args.get("skip", 0))
    except ValueError:
        return error_response("Limit and skip parameters must be integers!", 400)

    auth_header = request.headers.get("Authorization")
    result, err, status_code = fetch_public_feed(limit=limit, skip=skip, auth_header=auth_header)
    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["posts"],
        total=result["total"],
        limit=result["limit"],
        skip=result["skip"],
        status_code=status_code
    )

@journal_bp.route("", methods=["POST"])
@token_required
def create():
    """
    POST /api/journals - Create Journal Entry (Public or Private)
    """
    data = request.get_json(silent=True) or {}
    validation_error = validate_create_journal_data(data)
    if validation_error:
        return error_response(validation_error, 400)

    result, err, status_code = create_journal_entry(
        user_id=g.user_id,
        author_username=g.current_user.get("username"),
        title=data["title"],
        content=data["content"],
        tags=data.get("tags"),
        is_public=data.get("is_public", False)
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["post"],
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/my", methods=["GET"])
@token_required
def get_my_posts():
    """
    GET /api/journals/my - User's My Journals List controller
    Supports filtering by ?is_public=true/false or ?status=public/private
    """
    is_public_param = request.args.get("is_public")
    status_param = request.args.get("status")

    is_public_filter = None
    if is_public_param is not None:
        is_public_filter = is_public_param.lower() in ["true", "1", "yes"]
    elif status_param is not None:
        if status_param.lower() == "public":
            is_public_filter = True
        elif status_param.lower() == "private":
            is_public_filter = False

    result, err, status_code = fetch_user_journals(
        user_id=g.user_id,
        is_public_filter=is_public_filter
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["posts"],
        count=result["count"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>", methods=["GET"])
def get_detail(post_id):
    """
    GET /api/journals/<post_id> - Single Journal Detail controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    auth_header = request.headers.get("Authorization")
    result, err, status_code = get_journal_detail(post_id=post_id, auth_header=auth_header)
    if err:
        return error_response(err, status_code)

    return success_response(data=result["post"], status_code=status_code)

@journal_bp.route("/<post_id>/privacy", methods=["PATCH"])
@token_required
def patch_privacy(post_id):
    """
    PATCH /api/journals/<post_id>/privacy - Change Privacy Status controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    data = request.get_json(silent=True) or {}
    validation_error = validate_privacy_data(data)
    if validation_error:
        return error_response(validation_error, 400)

    result, err, status_code = update_journal_privacy(
        post_id=post_id,
        user_id=g.user_id,
        is_public=data["is_public"]
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["post"],
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>", methods=["PUT"])
@token_required
def update(post_id):
    """
    PUT /api/journals/<post_id> - Update Journal Entry controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    data = request.get_json(silent=True) or {}

    result, err, status_code = update_journal_entry(
        post_id=post_id,
        user_id=g.user_id,
        data=data
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["post"],
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>", methods=["DELETE"])
@token_required
def delete(post_id):
    """
    DELETE /api/journals/<post_id> - Delete Journal Entry controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    result, err, status_code = delete_journal_entry(
        post_id=post_id,
        user_id=g.user_id
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>/react", methods=["POST"])
@token_required
def react(post_id):
    """
    POST /api/journals/<post_id>/react - Add, update, or toggle reaction on a post controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    data = request.get_json(silent=True)
    val_err = validate_reaction_data(data)
    if val_err:
        return error_response(val_err, 400)

    reaction_type = "like"
    if data and isinstance(data, dict):
        reaction_type = data.get("type") or data.get("reaction_type") or "like"

    result, err, status_code = add_or_toggle_reaction(
        post_id=post_id,
        user_id=g.user_id,
        username=g.current_user.get("username"),
        reaction_type=reaction_type
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["data"],
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>/react", methods=["DELETE"])
@token_required
def delete_reaction(post_id):
    """
    DELETE /api/journals/<post_id>/react - Remove reaction from a post controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    result, err, status_code = remove_reaction(
        post_id=post_id,
        user_id=g.user_id
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["data"],
        message=result["message"],
        status_code=status_code
    )

@journal_bp.route("/<post_id>/reactions", methods=["GET"])
def get_reactions(post_id):
    """
    GET /api/journals/<post_id>/reactions - Detailed list of reactions on a post controller
    """
    id_error = validate_object_id(post_id)
    if id_error:
        return error_response(id_error, 400)

    auth_header = request.headers.get("Authorization")
    result, err, status_code = get_post_reactions_detail(
        post_id=post_id,
        auth_header=auth_header
    )

    if err:
        return error_response(err, status_code)

    return success_response(
        data=result["data"],
        status_code=status_code
    )

