"""
API Key Generation, Hashing, and Constant-Time Verification.
Step 37: Public API, Developer Platform & SDK Layer.
"""
import hashlib
import hmac
import secrets
from typing import Tuple


PREFIX_DEV = "awl_dev_"
PREFIX_STG = "awl_stg_"
PREFIX_PROD = "awl_prod_"


class APIKeyManager:
    """Manages secure generation and hashing of API keys."""

    @staticmethod
    def get_prefix_for_environment(environment: str) -> str:
        env = (environment or "").lower()
        if env == "production":
            return PREFIX_PROD
        elif env == "staging":
            return PREFIX_STG
        return PREFIX_DEV

    @classmethod
    def generate_key(cls, environment: str) -> Tuple[str, str, str]:
        """
        Generates a cryptographically random API key.
        Returns (plaintext_key, key_prefix, key_hash).
        The plaintext_key is only ever returned here and must never be stored.
        """
        prefix = cls.get_prefix_for_environment(environment)
        # Generate 32 bytes of cryptographic randomness (64 hex characters)
        raw_secret = secrets.token_hex(32)
        plaintext_key = f"{prefix}{raw_secret}"

        # Prefix for fast lookup in DB (e.g., first 16 characters including prefix)
        key_prefix = plaintext_key[:16]

        # Secure SHA-256 hash of the entire plaintext key
        key_hash = cls.hash_key(plaintext_key)

        return plaintext_key, key_prefix, key_hash

    @staticmethod
    def hash_key(plaintext_key: str) -> str:
        """Computes deterministic SHA-256 hash of the key."""
        return hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()

    @classmethod
    def verify_key(cls, plaintext_key: str, stored_hash: str) -> bool:
        """Constant-time verification of API key against stored hash."""
        computed_hash = cls.hash_key(plaintext_key)
        return hmac.compare_digest(computed_hash, stored_hash)

    @classmethod
    def extract_prefix(cls, plaintext_key: str) -> str:
        """Extracts recognizable prefix from a key."""
        if not plaintext_key or len(plaintext_key) < 16:
            return ""
        return plaintext_key[:16]
