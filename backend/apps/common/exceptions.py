from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Uniform error envelope: {"error": {"code": ..., "message": ..., "fields": {...}}}."""
    response = exception_handler(exc, context)
    if response is None:
        return None  # unhandled -> 500, logged by Django, generic body, no stack trace
    code = getattr(exc, "default_code", "error")
    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        body = {"code": code, "message": str(data["detail"])}
    else:
        body = {"code": code, "message": "Invalid request.", "fields": data}
    response.data = {"error": body}
    return response
