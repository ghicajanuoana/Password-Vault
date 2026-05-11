from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from password_vault.config import APP_VERSION, PASSWORD_MIN_LENGTH
from password_vault.models.credential import Credential
from password_vault.repositories.vault_repository import VaultRepository, VaultRepositoryError
from password_vault.security.crypto_manager import CryptoError, CryptoManager
from password_vault.services.password_generator import PasswordGenerator


class VaultValidationError(Exception):
    pass


class VaultAuthenticationError(Exception):
    pass


class VaultService:
    def __init__(self, repository: VaultRepository, crypto_manager: CryptoManager) -> None:
        self._repository = repository
        self._crypto = crypto_manager
        self._generator = PasswordGenerator()

    def prepare_storage(self) -> None:
        self._repository.initialize_database()

    def vault_exists(self) -> bool:
        return self._repository.has_master_password()

    def setup_master_password(self, master_password: str, confirm_password: str) -> None:
        self._validate_master_password(master_password, confirm_password)
        if self._repository.has_master_password():
            raise VaultValidationError("Vault is already initialized.")

        encryption_salt = self._crypto.generate_salt()
        verification_salt = self._crypto.generate_salt()
        verification_hash = self._crypto.derive_verification_hash(master_password, verification_salt)
        self._repository.create_vault_meta(
            encryption_salt=base64.urlsafe_b64encode(encryption_salt).decode("utf-8"),
            verification_salt=base64.urlsafe_b64encode(verification_salt).decode("utf-8"),
            verification_hash=verification_hash,
            created_at=self._now(),
            app_version=APP_VERSION,
        )
        self._crypto.start_session(master_password, encryption_salt)

    def unlock(self, master_password: str) -> None:
        if not master_password.strip():
            raise VaultAuthenticationError("Master password is required.")

        meta = self._repository.fetch_vault_meta()
        if meta is None:
            raise VaultAuthenticationError("Vault is not initialized.")

        verification_salt = base64.urlsafe_b64decode(meta["verification_salt"].encode("utf-8"))
        if not self._crypto.verify_hash(master_password, verification_salt, meta["verification_hash"]):
            raise VaultAuthenticationError("Incorrect master password.")

        encryption_salt = base64.urlsafe_b64decode(meta["encryption_salt"].encode("utf-8"))
        self._crypto.start_session(master_password, encryption_salt)

    def lock(self) -> None:
        self._crypto.clear_session()

    def is_unlocked(self) -> bool:
        return self._crypto.has_session()

    def list_credentials(self, query: str = "") -> list[Credential]:
        return self._repository.search_credentials(query)

    def get_credential(self, credential_id: int) -> Credential:
        credential = self._repository.get_credential(credential_id)
        if credential is None:
            raise VaultValidationError("Credential not found.")
        return credential

    def add_credential(self, site: str, username: str, password: str, notes: str) -> int:
        self._ensure_unlocked()
        self._validate_credential_fields(site, username, password)
        encrypted_password = self._crypto.encrypt(password)
        now = self._now()
        credential = Credential(
            site=site.strip(),
            username=username.strip(),
            encrypted_password=encrypted_password,
            notes=notes.strip(),
            created_at=now,
            updated_at=now,
        )
        return self._repository.add_credential(credential)

    def update_credential(self, credential_id: int, site: str, username: str, password: str, notes: str) -> None:
        self._ensure_unlocked()
        existing = self.get_credential(credential_id)
        self._validate_credential_fields(site, username, password)
        encrypted_password = self._crypto.encrypt(password)
        updated = Credential(
            credential_id=credential_id,
            site=site.strip(),
            username=username.strip(),
            encrypted_password=encrypted_password,
            notes=notes.strip(),
            created_at=existing.created_at,
            updated_at=self._now(),
        )
        self._repository.update_credential(updated)

    def delete_credential(self, credential_id: int) -> None:
        self._ensure_unlocked()
        self._repository.delete_credential(credential_id)

    def reveal_password(self, credential_id: int) -> str:
        self._ensure_unlocked()
        credential = self.get_credential(credential_id)
        return self._crypto.decrypt(credential.encrypted_password)

    def export_backup(self, output_path: Path) -> Path:
        self._ensure_unlocked()
        payload = self._repository.export_payload_json()
        encrypted_backup = self._crypto.encrypt(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encrypted_backup, encoding="utf-8")
        return output_path

    def generate_password(self, length: int = 18) -> str:
        return self._generator.generate(length)

    def password_strength(self, password: str) -> str:
        return self._generator.strength_label(password)

    def export_key_fingerprint(self) -> str:
        return self._crypto.export_key_fingerprint()

    def _ensure_unlocked(self) -> None:
        if not self._crypto.has_session():
            raise VaultAuthenticationError("Vault is locked.")

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validate_master_password(master_password: str, confirm_password: str) -> None:
        if len(master_password) < PASSWORD_MIN_LENGTH:
            raise VaultValidationError(
                f"Master password must be at least {PASSWORD_MIN_LENGTH} characters."
            )
        if master_password != confirm_password:
            raise VaultValidationError("Master password confirmation does not match.")

    @staticmethod
    def _validate_credential_fields(site: str, username: str, password: str) -> None:
        if not site.strip():
            raise VaultValidationError("Site is required.")
        if not username.strip():
            raise VaultValidationError("Username is required.")
        if not password:
            raise VaultValidationError("Password is required.")


ServiceError = VaultRepositoryError | VaultValidationError | VaultAuthenticationError | CryptoError
