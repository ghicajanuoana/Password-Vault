from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from password_vault.config import PBKDF2_ITERATIONS


class CryptoError(Exception):
    pass


class CryptoManager:
    def __init__(self) -> None:
        self._session_key: Optional[bytes] = None

    @staticmethod
    def generate_salt() -> bytes:
        return secrets.token_bytes(16)

    def derive_encryption_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        key = kdf.derive(master_password.encode("utf-8"))
        return base64.urlsafe_b64encode(key)

    def derive_verification_hash(self, master_password: str, verify_salt: bytes) -> str:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=verify_salt,
            iterations=PBKDF2_ITERATIONS,
        )
        digest = kdf.derive(master_password.encode("utf-8"))
        return base64.urlsafe_b64encode(digest).decode("utf-8")

    @staticmethod
    def fingerprint_key(session_key: bytes) -> str:
        return hashlib.sha256(session_key).hexdigest()

    @staticmethod
    def verify_hash(master_password: str, verify_salt: bytes, expected_hash: str) -> bool:
        candidate = CryptoManager().derive_verification_hash(master_password, verify_salt)
        return hmac.compare_digest(candidate, expected_hash)

    def start_session(self, master_password: str, encryption_salt: bytes) -> None:
        self._session_key = self.derive_encryption_key(master_password, encryption_salt)

    def clear_session(self) -> None:
        self._session_key = None

    def has_session(self) -> bool:
        return self._session_key is not None

    def export_key_fingerprint(self) -> str:
        if self._session_key is None:
            raise CryptoError("Vault is locked.")
        return self.fingerprint_key(self._session_key)

    def encrypt(self, plaintext: str) -> str:
        if self._session_key is None:
            raise CryptoError("Vault is locked.")
        token = Fernet(self._session_key).encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        if self._session_key is None:
            raise CryptoError("Vault is locked.")
        try:
            decrypted = Fernet(self._session_key).decrypt(ciphertext.encode("utf-8"))
        except InvalidToken as exc:
            raise CryptoError("Failed to decrypt secret.") from exc
        return decrypted.decode("utf-8")
