from jose import JWTError, jwt  # type: ignore[import]
from datetime import datetime, timedelta
from app.core.config import settings
from app.schemas.user_schema import TokenData

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise JWTError()
        token_data = TokenData(email=email, role=role)
    except JWTError:
        return None
    return token_data
