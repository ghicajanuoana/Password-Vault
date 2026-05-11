from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from password_vault.config import APP_NAME, BACKUP_PATH, DB_PATH, WINDOW_MIN_SIZE, ensure_runtime_directories
from password_vault.repositories.vault_repository import VaultRepository
from password_vault.security.crypto_manager import CryptoManager
from password_vault.services.vault_service import VaultService
from password_vault.ui.login_window import LoginWindow
from password_vault.ui.main_window import MainWindow
from password_vault.ui.styles import PALETTE


class PasswordVaultApp:
    def __init__(self) -> None:
        ensure_runtime_directories()
        self._repository = VaultRepository(DB_PATH)
        self._crypto = CryptoManager()
        self._service = VaultService(self._repository, self._crypto)
        self._service.prepare_storage()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.geometry("1180x740")
        self.root.configure(bg=PALETTE["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._configure_styles()
        self._current_view: tk.Widget | None = None
        self.show_login()

    @property
    def service(self) -> VaultService:
        return self._service

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def show_login(self) -> None:
        self._set_view(
            LoginWindow(
                self.root,
                vault_exists=self._service.vault_exists(),
                on_setup=self._handle_setup,
                on_unlock=self._handle_unlock,
            )
        )

    def show_main(self) -> None:
        self._set_view(
            MainWindow(
                self.root,
                on_add=self._service.add_credential,
                on_update=self._service.update_credential,
                on_delete=self._service.delete_credential,
                on_list=self._service.list_credentials,
                on_get_plaintext=self._service.reveal_password,
                on_generate_password=lambda: self._service.generate_password(),
                password_strength=self._service.password_strength,
                on_export=lambda: str(self._service.export_backup(BACKUP_PATH)),
            )
        )

    def _set_view(self, widget: tk.Widget) -> None:
        if self._current_view is not None:
            self._current_view.destroy()
        self._current_view = widget
        self._current_view.pack(fill="both", expand=True)

    def _handle_setup(self, master_password: str, confirm_password: str) -> None:
        self._service.setup_master_password(master_password, confirm_password)
        messagebox.showinfo("Vault ready", "Your vault is ready to use.", parent=self.root)
        self.show_main()

    def _handle_unlock(self, master_password: str) -> None:
        self._service.unlock(master_password)
        self.show_main()

    def _on_close(self) -> None:
        self._service.lock()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
