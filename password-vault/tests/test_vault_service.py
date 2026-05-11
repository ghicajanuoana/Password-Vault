from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from password_vault.repositories.vault_repository import VaultRepository
from password_vault.security.crypto_manager import CryptoManager
from password_vault.services.vault_service import (
    VaultAuthenticationError,
    VaultService,
    VaultValidationError,
)


class VaultServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "vault.db"
        self.backup_path = Path(self.temp_dir.name) / "backup.txt"
        self.repository = VaultRepository(self.db_path)
        self.crypto = CryptoManager()
        self.service = VaultService(self.repository, self.crypto)
        self.service.prepare_storage()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_setup_and_unlock_flow(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        self.assertTrue(self.service.is_unlocked())
        self.service.lock()
        self.service.unlock("VaultMaster!2026")
        self.assertTrue(self.service.is_unlocked())

    def test_incorrect_master_password_is_rejected(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        self.service.lock()
        with self.assertRaises(VaultAuthenticationError):
            self.service.unlock("wrong-password")

    def test_add_update_delete_and_search_credentials(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        credential_id = self.service.add_credential("github.com", "alex", "Secret!2026", "notes")
        items = self.service.list_credentials("github")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, credential_id)
        self.assertEqual(self.service.reveal_password(credential_id), "Secret!2026")

        self.service.update_credential(credential_id, "github.com", "alex.dev", "NewSecret!2027", "updated")
        updated = self.service.get_credential(credential_id)
        self.assertEqual(updated.username, "alex.dev")
        self.assertEqual(self.service.reveal_password(credential_id), "NewSecret!2027")

        self.service.delete_credential(credential_id)
        self.assertEqual(self.service.list_credentials(), [])

    def test_duplicate_site_username_is_rejected(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        self.service.add_credential("github.com", "alex", "Secret!2026", "")
        with self.assertRaises(Exception):
            self.service.add_credential("github.com", "alex", "Another!2026", "")

    def test_plaintext_is_not_stored_in_database(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        self.service.add_credential("example.com", "user", "Plaintext!2026", "")
        with closing(sqlite3.connect(self.db_path)) as connection:
            stored = connection.execute("SELECT password_encrypted FROM credentials").fetchone()[0]
        self.assertNotIn("Plaintext!2026", stored)

    def test_export_backup_is_encrypted(self) -> None:
        self.service.setup_master_password("VaultMaster!2026", "VaultMaster!2026")
        self.service.add_credential("openai.com", "alex", "Export!2026", "demo")
        output = self.service.export_backup(self.backup_path)
        content = output.read_text(encoding="utf-8")
        self.assertNotIn("Export!2026", content)
        self.assertNotIn("openai.com", content)

    def test_password_generator_and_strength(self) -> None:
        password = self.service.generate_password()
        self.assertGreaterEqual(len(password), 12)
        self.assertIn("Strength:", self.service.password_strength(password))

    def test_master_password_validation(self) -> None:
        with self.assertRaises(VaultValidationError):
            self.service.setup_master_password("short", "short")


if __name__ == "__main__":
    unittest.main()
