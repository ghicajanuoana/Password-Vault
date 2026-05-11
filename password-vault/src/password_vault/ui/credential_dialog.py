from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from password_vault.ui.styles import FONT_FAMILY, PALETTE


class CredentialDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        title: str,
        strength_provider: Callable[[str], str],
        password_generator: Callable[[], str],
        on_submit: Callable[[str, str, str, str], None],
        initial_values: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.configure(bg=PALETTE["bg"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._strength_provider = strength_provider
        self._password_generator = password_generator
        self._on_submit = on_submit
        self._build(initial_values or {})
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self, values: dict[str, str]) -> None:
        frame = tk.Frame(self, bg=PALETTE["panel"], padx=22, pady=20, bd=1, relief="solid")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            frame,
            text=self.title(),
            font=(FONT_FAMILY, 16, "bold"),
            bg=PALETTE["panel"],
            fg=PALETTE["accent"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self.site_var = tk.StringVar(value=values.get("site", ""))
        self.username_var = tk.StringVar(value=values.get("username", ""))
        self.password_var = tk.StringVar(value=values.get("password", ""))
        self.show_password_var = tk.BooleanVar(value=False)
        self.strength_var = tk.StringVar(value=self._strength_provider(self.password_var.get()))

        labels = ("Site", "Username", "Password", "Notes")
        for index, label in enumerate(labels, start=1):
            tk.Label(
                frame,
                text=label,
                font=(FONT_FAMILY, 10, "bold"),
                bg=PALETTE["panel"],
                fg=PALETTE["text"],
            ).grid(row=index, column=0, sticky="w", pady=6, padx=(0, 10))

        entry_style = {"font": (FONT_FAMILY, 10), "bg": "white", "fg": PALETTE["text"], "relief": "solid", "bd": 1}

        tk.Entry(frame, textvariable=self.site_var, width=38, **entry_style).grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
        tk.Entry(frame, textvariable=self.username_var, width=38, **entry_style).grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        self.password_entry = tk.Entry(frame, textvariable=self.password_var, show="*", width=30, **entry_style)
        self.password_entry.grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Button(frame, text="Generate", command=self._generate_password).grid(row=3, column=2, sticky="ew", padx=(8, 0))

        tk.Checkbutton(
            frame,
            text="Show password",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["panel_alt"],
            font=(FONT_FAMILY, 9),
        ).grid(row=4, column=1, sticky="w")

        tk.Label(
            frame,
            textvariable=self.strength_var,
            font=(FONT_FAMILY, 9, "italic"),
            bg=PALETTE["panel"],
            fg=PALETTE["accent_soft"],
        ).grid(row=4, column=2, sticky="e")

        self.notes_text = tk.Text(
            frame,
            width=40,
            height=6,
            font=(FONT_FAMILY, 10),
            bg="white",
            fg=PALETTE["text"],
            relief="solid",
            bd=1,
            wrap="word",
        )
        self.notes_text.grid(row=5, column=1, columnspan=2, sticky="ew", pady=6)
        self.notes_text.insert("1.0", values.get("notes", ""))

        actions = tk.Frame(frame, bg=PALETTE["panel"])
        actions.grid(row=6, column=0, columnspan=3, sticky="e", pady=(14, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Save", command=self._submit).pack(side="right")

        self.password_var.trace_add("write", self._update_strength)

    def _toggle_password_visibility(self) -> None:
        self.password_entry.configure(show="" if self.show_password_var.get() else "*")

    def _generate_password(self) -> None:
        password = self._password_generator()
        self.password_var.set(password)

    def _update_strength(self, *_args: object) -> None:
        self.strength_var.set(self._strength_provider(self.password_var.get()))

    def _submit(self) -> None:
        try:
            self._on_submit(
                self.site_var.get(),
                self.username_var.get(),
                self.password_var.get(),
                self.notes_text.get("1.0", "end").strip(),
            )
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return
        self.destroy()
