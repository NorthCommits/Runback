from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe


def create_token_secret() -> str:
    return f"rb_{token_urlsafe(32)}"


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    return compare_digest(hash_token(token), token_hash)
