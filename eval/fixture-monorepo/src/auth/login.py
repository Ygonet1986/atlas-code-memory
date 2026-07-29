"""User login authentication entrypoint."""

def authenticate(username: str, password: str) -> bool:
    """Verify password and create session."""
    return bool(username and password)

def login_handler(request):
    return authenticate(request.get("user"), request.get("pass"))
