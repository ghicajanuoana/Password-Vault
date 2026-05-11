from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from password_vault.config import BACKUP_PATH
from password_vault.models.credential import Credential
from password_vault.ui.credential_dialog import CredentialDialog
from password_vault.ui.styles import FONT_FAMILY, PALETTE


class MainWindow(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_add: Callable[[str, str, str, str], None],
        on_update: Callable[[int, str, str, str, str], None],
        on_delete: Callable[[int], None],
        on_list: Callable[[str], list[Credential]],
        on_get_plaintext: Callable[[int], str],
        on_generate_password: Callable[[], str],
        password_strength: Callable[[str], str],
        on_export: Callable[[], str],
    ) -> None:
        super().__init__(master, bg=PALETTE["bg"])
        self._on_add = on_add
        self._on_update = on_update
        self._on_delete = on_delete
        self._on_list = on_list
        self._on_get_plaintext = on_get_plaintext
        self._on_generate_password = on_generate_password
        self._password_strength = password_strength
        self._on_export = on_export
        self._copy_reset_job: Optional[str] = None
        self._build()
        self.refresh_table()

    def _build(self) -> None:
        hero = tk.Frame(self, bg=PALETTE["accent"], padx=26, pady=22)
        hero.pack(fill="x")
        tk.Label(hero, text="Password Vault", font=(FONT_FAMILY, 23, "bold"), fg="white", bg=PALETTE["accent"]).pack(anchor="w")
        tk.Label(
            hero,
            text="Store logins, search them quickly, and export a backup.",
            font=(FONT_FAMILY, 10),
            fg="#e8f1f7",
            bg=PALETTE["accent"],
        ).pack(anchor="w", pady=(6, 0))

        body = tk.Frame(self, bg=PALETTE["bg"], padx=24, pady=20)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left_panel = tk.Frame(body, bg=PALETTE["panel"], bd=1, relief="solid")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right_panel = tk.Frame(body, bg=PALETTE["panel"], bd=1, relief="solid", padx=18, pady=18)
        right_panel.grid(row=0, column=1, sticky="nsew")

        toolbar = tk.Frame(left_panel, bg=PALETTE["panel"], padx=18, pady=16)
        toolbar.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self.refresh_table())
        tk.Label(toolbar, text="Search", font=(FONT_FAMILY, 10, "bold"), bg=PALETTE["panel"], fg=PALETTE["text"]).pack(side="left")
        tk.Entry(toolbar, textvariable=self.search_var, width=28, font=(FONT_FAMILY, 10), relief="solid", bd=1).pack(side="left", padx=(8, 18))
        ttk.Button(toolbar, text="Add Credential", command=self._open_add_dialog).pack(side="left")
        ttk.Button(toolbar, text="Export Backup", command=self._export_backup).pack(side="left", padx=(8, 0))

        self.tree = ttk.Treeview(left_panel, columns=("site", "username", "updated"), show="headings", height=18)
        self.tree.heading("site", text="Site")
        self.tree.heading("username", text="Username")
        self.tree.heading("updated", text="Updated")
        self.tree.column("site", width=220)
        self.tree.column("username", width=180)
        self.tree.column("updated", width=150)
        self.tree.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected_details())

        tk.Label(right_panel, text="Credential Details", font=(FONT_FAMILY, 16, "bold"), bg=PALETTE["panel"], fg=PALETTE["accent"]).pack(anchor="w")
        tk.Label(right_panel, text="Select a record to reveal or edit it.", font=(FONT_FAMILY, 10), bg=PALETTE["panel"], fg=PALETTE["muted"]).pack(anchor="w", pady=(6, 14))

        self.site_value = self._detail_row(right_panel, "Site")
        self.username_value = self._detail_row(right_panel, "Username")
        self.password_value = tk.StringVar(value="—")
        self._detail_entry(right_panel, "Password", self.password_value)
        self.notes_box = tk.Text(right_panel, height=8, width=34, font=(FONT_FAMILY, 10), bg=PALETTE["panel_alt"], fg=PALETTE["text"], relief="flat", wrap="word")
        self.notes_box.pack(fill="x", pady=(12, 8))
        self.notes_box.configure(state="disabled")

        self.feedback_var = tk.StringVar(value="Ready")
        tk.Label(right_panel, textvariable=self.feedback_var, font=(FONT_FAMILY, 9, "italic"), bg=PALETTE["panel"], fg=PALETTE["success"]).pack(anchor="w", pady=(4, 10))

        actions = tk.Frame(right_panel, bg=PALETTE["panel"])
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Reveal Password", command=self._reveal_selected_password).pack(fill="x", pady=3)
        ttk.Button(actions, text="Copy Password", command=self._copy_selected_password).pack(fill="x", pady=3)
        ttk.Button(actions, text="Edit Selected", command=self._open_edit_dialog).pack(fill="x", pady=3)
        ttk.Button(actions, text="Delete Selected", command=self._delete_selected).pack(fill="x", pady=3)

        backup_hint = f"Default backup path: {BACKUP_PATH.name}"
        tk.Label(right_panel, text=backup_hint, font=(FONT_FAMILY, 9), bg=PALETTE["panel"], fg=PALETTE["muted"]).pack(anchor="w", pady=(12, 0))

    def _detail_row(self, master: tk.Misc, label: str) -> tk.StringVar:
        var = tk.StringVar(value="—")
        tk.Label(master, text=label, font=(FONT_FAMILY, 10, "bold"), bg=PALETTE["panel"], fg=PALETTE["text"]).pack(anchor="w")
        tk.Label(master, textvariable=var, font=(FONT_FAMILY, 10), bg=PALETTE["panel"], fg=PALETTE["text"], wraplength=320, justify="left").pack(anchor="w", pady=(2, 10))
        return var

    def _detail_entry(self, master: tk.Misc, label: str, variable: tk.StringVar) -> None:
        tk.Label(master, text=label, font=(FONT_FAMILY, 10, "bold"), bg=PALETTE["panel"], fg=PALETTE["text"]).pack(anchor="w")
        entry = tk.Entry(
            master,
            textvariable=variable,
            font=(FONT_FAMILY, 10),
            relief="solid",
            bd=1,
            readonlybackground=PALETTE["panel_alt"],
            fg=PALETTE["text"],
        )
        entry.configure(state="readonly")
        entry.pack(fill="x", pady=(2, 10))

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for credential in self._on_list(self.search_var.get()):
            self.tree.insert(
                "",
                "end",
                iid=str(credential.id),
                values=(credential.site, credential.username, credential.updated_at),
            )
        self._clear_details()

    def _selected_id(self) -> Optional[int]:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _show_selected_details(self) -> None:
        credential_id = self._selected_id()
        if credential_id is None:
            self._clear_details()
            return

        item = self.tree.item(str(credential_id))
        values = item.get("values", ["", "", ""])
        self.site_value.set(values[0])
        self.username_value.set(values[1])
        self.password_value.set("Hidden until revealed")
        notes = self._on_list(self.search_var.get())
        selected = next((credential for credential in notes if credential.id == credential_id), None)
        note_text = selected.notes if selected else ""
        self._set_notes(note_text)
        self.feedback_var.set("Credential selected")

    def _set_notes(self, value: str) -> None:
        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", value or "No notes saved.")
        self.notes_box.configure(state="disabled")

    def _clear_details(self) -> None:
        self.site_value.set("—")
        self.username_value.set("—")
        self.password_value.set("—")
        self._set_notes("")
        self.feedback_var.set("Ready")

    def _open_add_dialog(self) -> None:
        CredentialDialog(
            self,
            title="Add Credential",
            strength_provider=self._password_strength,
            password_generator=self._on_generate_password,
            on_submit=self._save_new_credential,
        )

    def _save_new_credential(self, site: str, username: str, password: str, notes: str) -> None:
        self._on_add(site, username, password, notes)
        self.refresh_table()
        self.feedback_var.set("Credential added successfully")

    def _open_edit_dialog(self) -> None:
        credential_id = self._selected_id()
        if credential_id is None:
            messagebox.showinfo("Select a credential", "Choose a credential to edit.", parent=self)
            return
        plaintext = self._on_get_plaintext(credential_id)
        matches = self._on_list(self.search_var.get())
        selected = next((credential for credential in matches if credential.id == credential_id), None)
        if selected is None:
            messagebox.showerror("Missing credential", "The selected credential could not be loaded.", parent=self)
            return
        CredentialDialog(
            self,
            title="Edit Credential",
            strength_provider=self._password_strength,
            password_generator=self._on_generate_password,
            on_submit=lambda site, username, password, notes: self._save_updated_credential(
                credential_id, site, username, password, notes
            ),
            initial_values={
                "site": selected.site,
                "username": selected.username,
                "password": plaintext,
                "notes": selected.notes,
            },
        )

    def _save_updated_credential(self, credential_id: int, site: str, username: str, password: str, notes: str) -> None:
        self._on_update(credential_id, site, username, password, notes)
        self.refresh_table()
        if str(credential_id) in self.tree.get_children():
            self.tree.selection_set(str(credential_id))
            self._show_selected_details()
        self.feedback_var.set("Credential updated successfully")

    def _delete_selected(self) -> None:
        credential_id = self._selected_id()
        if credential_id is None:
            messagebox.showinfo("Select a credential", "Choose a credential to delete.", parent=self)
            return
        if not messagebox.askyesno("Delete credential", "Delete the selected credential?", parent=self):
            return
        self._on_delete(credential_id)
        self.refresh_table()
        self.feedback_var.set("Credential deleted")

    def _reveal_selected_password(self) -> None:
        credential_id = self._selected_id()
        if credential_id is None:
            messagebox.showinfo("Select a credential", "Choose a credential to reveal.", parent=self)
            return
        self.password_value.set(self._on_get_plaintext(credential_id))
        self.feedback_var.set("Password revealed")

    def _copy_selected_password(self) -> None:
        credential_id = self._selected_id()
        if credential_id is None:
            messagebox.showinfo("Select a credential", "Choose a credential to copy.", parent=self)
            return

        password = self._on_get_plaintext(credential_id)
        self.clipboard_clear()
        self.clipboard_append(password)
        self.feedback_var.set("Password copied to clipboard")

        if self._copy_reset_job is not None:
            self.after_cancel(self._copy_reset_job)
        self._copy_reset_job = self.after(2000, lambda: self.feedback_var.set("Ready"))

    def _export_backup(self) -> None:
        backup_path = self._on_export()
        self.feedback_var.set(f"Encrypted backup saved to {backup_path}")
        messagebox.showinfo("Backup created", f"Encrypted backup saved to:\n{backup_path}", parent=self)
