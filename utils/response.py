from flask import jsonify

def success_response(data=None, message=None, status_code=200, **kwargs):
    """
    Standardized success JSON response format.
    """
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    
    # Merge additional top-level metadata if provided (e.g. token, pagination stats)
    for key, value in kwargs.items():
        payload[key] = value

    return jsonify(payload), status_code

def error_response(message, status_code=400, **kwargs):
    """
    Standardized error JSON response format.
    """
    payload = {
        "success": False,
        "error": message
    }
    for key, value in kwargs.items():
        payload[key] = value

    return jsonify(payload), status_code
