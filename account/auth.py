import jwt
from datetime import datetime, timedelta

# --- Configuration ---
# Keep this secret! In a real app, load from environment variables.
SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # The 'jwt.encode' function is now 'jwt.encode' in the latest pyjwt
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except TypeError:
        # Fallback for older pyjwt versions
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# We don't need token decoding in this service, but you would add it
# in services that need to *validate* a token.
