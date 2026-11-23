from app.services.tokens import create_token_secret, hash_token, verify_token


def test_hash_token_is_not_the_original_secret() -> None:
    token = "rb_example-token"

    token_hash = hash_token(token)

    assert token_hash != token
    assert len(token_hash) == 64
    assert verify_token(token, token_hash) is True
    assert verify_token("rb_other-token", token_hash) is False


def test_create_token_secret_uses_runback_prefix() -> None:
    token = create_token_secret()

    assert token.startswith("rb_")
    assert len(token) > 32
