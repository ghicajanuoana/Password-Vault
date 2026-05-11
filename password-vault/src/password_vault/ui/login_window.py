from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from password_vault.config import PASSWORD_MIN_LENGTH
from password_vault.ui.styles import FONT_FAMILY, PALETTE


class LoginWindow(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        vault_exists: bool,
        on_setup: Callable[[str, str], None],
        on_unlock: Callable[[str], None],
    ) -> None:
        super().__init__(master, bg=PALETTE["bg"])
        self._vault_exists = vault_exists
        self._on_setup = on_setup
        self._on_unlock = on_unlock
        self._build()

    def _build(self) -> None:
        panel = tk.Frame(self, bg=PALETTE["panel"], padx=32, pady=28, bd=1, relief="solid")
        panel.place(relx=0.5, rely=0.5, anchor="center")

        title = "Unlock Your Vault" if self._vault_exists else "Create Your Vault"
        subtitle = (
            "Enter your master password."
            if self._vault_exists
            else f"Choose a master password with at least {PASSWORD_MIN_LENGTH} characters."
        )

        tk.Label(panel, text=title, font=(FONT_FAMILY, 20, "bold"), bg=PALETTE["panel"], fg=PALETTE["accent"]).pack(anchor="w")
        tk.Label(
            panel,
            text=subtitle,
            font=(FONT_FAMILY, 10),
            bg=PALETTE["panel"],
            fg=PALETTE["muted"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(8, 18))

        tk.Label(panel, text="Master Password", font=(FONT_FAMILY, 10, "bold"), bg=PALETTE["panel"], fg=PALETTE["text"]).pack(anchor="w")
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(panel, textvariable=self.password_var, show="*", width=34, font=(FONT_FAMILY, 11), relief="solid", bd=1)
        self.password_entry.pack(fill="x", pady=(6, 14))

        self.confirm_var = tk.StringVar()
        if not self._vault_exists:
            tk.Label(panel, text="Confirm Password", font=(FONT_FAMILY, 10, "bold"), bg=PALETTE["panel"], fg=PALETTE["text"]).pack(anchor="w")
            tk.Entry(panel, textvariable=self.confirm_var, show="*", width=34, font=(FONT_FAMILY, 11), relief="solid", bd=1).pack(fill="x", pady=(6, 16))

        action_text = "Unlock Vault" if self._vault_exists else "Create Vault"
        ttk.Button(panel, text=action_text, command=self._submit).pack(anchor="e")
        self.password_entry.focus_set()

    def _submit(self) -> None:
        try:
            if self._vault_exists:
                self._on_unlock(self.password_var.get())
            else:
                self._on_setup(self.password_var.get(), self.confirm_var.get())
        except Exception as exc:
            messagebox.showerror("Vault error", str(exc), parent=self)
