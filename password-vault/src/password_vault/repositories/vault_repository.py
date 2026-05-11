from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from password_vault.models.credential import Credential


class VaultRepositoryError(Exception):
    pass


class VaultRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def initialize_database(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vault_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    encryption_salt TEXT NOT NULL,
                    verification_salt TEXT NOT NULL,
                    verification_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    app_version TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password_encrypted TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(site, username)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_credentials_site ON credentials(site)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_credentials_username ON credentials(username)"
            )
            connection.commit()

    def has_master_password(self) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT 1 FROM vault_meta WHERE id = 1").fetchone()
        return row is not None

    def create_vault_meta(
        self,
        encryption_salt: str,
        verification_salt: str,
        verification_hash: str,
        created_at: str,
        app_version: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO vault_meta
                (id, encryption_salt, verification_salt, verification_hash, created_at, app_version)
                VALUES (1, ?, ?, ?, ?, ?)
                """,
                (encryption_salt, verification_salt, verification_hash, created_at, app_version),
            )
            connection.commit()

    def fetch_vault_meta(self) -> Optional[dict[str, str]]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT encryption_salt, verification_salt, verification_hash, created_at, app_version
                FROM vault_meta
                WHERE id = 1
                """
            ).fetchone()

        if row is None:
            return None

        return {
            "encryption_salt": row["encryption_salt"],
            "verification_salt": row["verification_salt"],
            "verification_hash": row["verification_hash"],
            "created_at": row["created_at"],
            "app_version": row["app_version"],
        }

    def add_credential(self, credential: Credential) -> int:
        try:
            with closing(self._connect()) as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO credentials
                    (site, username, password_encrypted, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        credential.site,
                        credential.username,
                        credential.encrypted_password,
                        credential.notes,
                        credential.created_at,
                        credential.updated_at,
                    ),
                )
                connection.commit()
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise VaultRepositoryError("A credential for that site and username already exists.") from exc

    def update_credential(self, credential: Credential) -> None:
        if credential.id is None:
            raise VaultRepositoryError("Credential ID is required for updates.")

        try:
            with closing(self._connect()) as connection:
                cursor = connection.execute(
                    """
                    UPDATE credentials
                    SET site = ?, username = ?, password_encrypted = ?, notes = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        credential.site,
                        credential.username,
                        credential.encrypted_password,
                        credential.notes,
                        credential.updated_at,
                        credential.id,
                    ),
                )
                connection.commit()
                if cursor.rowcount == 0:
                    raise VaultRepositoryError("Credential not found.")
        except sqlite3.IntegrityError as exc:
            raise VaultRepositoryError("A credential for that site and username already exists.") from exc

    def delete_credential(self, credential_id: int) -> None:
        with closing(self._connect()) as connection:
            cursor = connection.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
            connection.commit()
            if cursor.rowcount == 0:
                raise VaultRepositoryError("Credential not found.")

    def get_credential(self, credential_id: int) -> Optional[Credential]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, site, username, password_encrypted, notes, created_at, updated_at
                FROM credentials
                WHERE id = ?
                """,
                (credential_id,),
            ).fetchone()
        return self._row_to_credential(row) if row else None

    def search_credentials(self, query: str = "") -> list[Credential]:
        search_value = f"%{query.strip().lower()}%"
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, site, username, password_encrypted, notes, created_at, updated_at
                FROM credentials
                WHERE lower(site) LIKE ? OR lower(username) LIKE ?
                ORDER BY lower(site), lower(username)
                """,
                (search_value, search_value),
            ).fetchall()
        return [self._row_to_credential(row) for row in rows]

    def export_payload(self) -> dict[str, Any]:
        meta = self.fetch_vault_meta()
        if meta is None:
            raise VaultRepositoryError("Vault metadata is missing.")

        credentials = []
        for credential in self.search_credentials():
            credentials.append(
                {
                    "id": credential.id,
                    "site": credential.site,
                    "username": credential.username,
                    "encrypted_password": credential.encrypted_password,
                    "notes": credential.notes,
                    "created_at": credential.created_at,
                    "updated_at": credential.updated_at,
                }
            )

        return {"vault_meta": meta, "credentials": credentials}

    def export_payload_json(self) -> str:
        return json.dumps(self.export_payload(), indent=2)

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self._db_path)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as exc:
            raise VaultRepositoryError("Failed to open the vault database.") from exc

    @staticmethod
    def _row_to_credential(row: sqlite3.Row) -> Credential:
        return Credential(
            credential_id=int(row["id"]),
            site=str(row["site"]),
            username=str(row["username"]),
            encrypted_password=str(row["password_encrypted"]),
            notes=str(row["notes"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
