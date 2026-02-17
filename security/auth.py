import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional

from database.db import create_person, create_user, get_user_by_username, update_user_password_hash


# Parámetros PBKDF2
_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16
_DKLEN = 32  # 32 bytes = 256 bits


def hash_password(password: str) -> str:
    """
    Devuelve un string con formato:
    pbkdf2_sha256$iterations$salt_hex$hash_hex
    """
    if not password or len(password) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")

    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
        dklen=_DKLEN,
    )
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Compara password vs hash guardado, de forma segura (constant-time).
    """
    try:
        algorithm, iterations_s, salt_hex, hash_hex = stored.split("$")
        if algorithm != _ALGORITHM:
            return False

        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def register_user(
    *,
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    date_of_birth: str,
    role: str = "doctor",
    dni: str | None = None,
    sex: str | None = None,
    nationality: str | None = None,
) -> int:
    """
    Crea una persona + usuario del sistema. Devuelve user_id.
    """
    person_id = create_person(
        dni=dni,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        sex=sex,
        nationality=nationality,
    )

    password_hash = hash_password(password)

    user_id = create_user(
        person_id=person_id,
        username=username,
        password_hash=password_hash,
        role=role,
    )

    return user_id


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve dict con datos del usuario si autentica, si no None.
    """
    user = get_user_by_username(username)
    if not user:
        return None

    if verify_password(password, user["password_hash"]):
        return user

    return None

def set_user_password(*, user_id: int, new_password: str) -> None:
    """
    Cambia la contraseña de un usuario existente (por id).
    """
    password_hash = hash_password(new_password)
    update_user_password_hash(int(user_id), password_hash)
