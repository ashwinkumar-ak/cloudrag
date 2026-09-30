from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials


PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_BYTES = 32

PASSWORD_SCRYPT_N = 2**14
PASSWORD_SCRYPT_R = 8
PASSWORD_SCRYPT_P = 1


class AuthenticationError(Exception):
    pass


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError(
            "Password must be at least 8 characters long."
        )

    salt = os.urandom(PASSWORD_SALT_BYTES)

    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=PASSWORD_SCRYPT_N,
        r=PASSWORD_SCRYPT_R,
        p=PASSWORD_SCRYPT_P,
        dklen=PASSWORD_HASH_BYTES,
    )

    return (
        f"scrypt${PASSWORD_SCRYPT_N}$"
        f"{PASSWORD_SCRYPT_R}$"
        f"{PASSWORD_SCRYPT_P}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(derived_key).decode()}"
    )


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    try:
        (
            algorithm,
            n,
            r,
            p,
            salt_encoded,
            hash_encoded,
        ) = stored_hash.split("$")

        if algorithm != "scrypt":
            return False

        salt = base64.urlsafe_b64decode(
            salt_encoded.encode("ascii")
        )

        expected_hash = base64.urlsafe_b64decode(
            hash_encoded.encode("ascii")
        )

        actual_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected_hash),
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash,
        )

    except (ValueError, TypeError):
        return False


def create_access_token(
    user_id: int,
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    now = datetime.now(timezone.utc)

    expires_at = (
        now
        + timedelta(minutes=expires_minutes)
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm,
    )


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str,
) -> int:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
        )

        subject = payload.get("sub")

        if subject is None:
            raise AuthenticationError()

        return int(subject)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise AuthenticationError() from exc


def require_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
    secret_key: str,
    algorithm: str,
) -> int:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:
        return decode_access_token(
            credentials.credentials,
            secret_key,
            algorithm,
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )