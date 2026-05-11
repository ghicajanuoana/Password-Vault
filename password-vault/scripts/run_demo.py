from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
from pathlib import Path
import time

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from password_vault.app import PasswordVaultApp
from password_vault.config import BACKUP_PATH, DB_PATH, SCREENSHOT_DIR, ensure_runtime_directories
from password_vault.ui.credential_dialog import CredentialDialog


MASTER_PASSWORD = "VaultMaster!2026"


def reset_demo_files() -> None:
    ensure_runtime_directories()
    for path in (DB_PATH, BACKUP_PATH):
        if path.exists():
            path.unlink()


def capture_widget(widget, output_name: str) -> None:
    topmost_supported = hasattr(widget, "attributes")
    previous_topmost = None
    if topmost_supported:
        try:
            previous_topmost = widget.attributes("-topmost")
            widget.attributes("-topmost", True)
        except Exception:
            previous_topmost = None
    widget.update_idletasks()
    widget.lift()
    try:
        widget.focus_force()
    except Exception:
        pass
    time.sleep(0.15)
    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    width = widget.winfo_width()
    height = widget.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    image.save(SCREENSHOT_DIR / output_name)
    if topmost_supported and previous_topmost is not None:
        try:
            widget.attributes("-topmost", previous_topmost)
        except Exception:
            pass


def seed_and_capture() -> None:
    app = PasswordVaultApp()
    app.root.update()
    capture_widget(app.root, "01_setup_window.png")

    app.service.setup_master_password(MASTER_PASSWORD, MASTER_PASSWORD)
    app.show_main()
    app.root.update()

    app.service.add_credential(
        "github.com",
        "alex.dev",
        "Gh!DemoPass2026",
        "Primary source control account with PAT rotation every 90 days.",
    )
    app.service.add_credential(
        "banking-demo.local",
        "alex.b",
        "B@nkSafe!77Vault",
        "Mock finance credential for coursework screenshots only.",
    )
    app.service.add_credential(
        "openai.com",
        "alex.research",
        "OpenAI!Secure88",
        "Used for API dashboard and documentation access.",
    )

    main_view = app._current_view
    assert main_view is not None
    main_view.refresh_table()
    app.root.update()
    capture_widget(app.root, "02_main_window.png")

    dialog = CredentialDialog(
        app.root,
        title="Add Credential",
        strength_provider=app.service.password_strength,
        password_generator=lambda: app.service.generate_password(),
        on_submit=lambda *_args: None,
        initial_values={
            "site": "example.org",
            "username": "demo.user",
            "password": "Demo!Password123",
            "notes": "New credential draft with generator support and strength feedback.",
        },
    )
    dialog.update()
    dialog.focus_set()
    capture_widget(dialog, "03_add_dialog.png")
    dialog.destroy()
    app.root.update()

    main_view.search_var.set("openai")
    main_view.refresh_table()
    app.root.update()
    selected = main_view.tree.get_children()[0]
    main_view.tree.selection_set(selected)
    main_view._show_selected_details()
    main_view._reveal_selected_password()
    main_view.tree.focus(selected)
    main_view.tree.focus_set()
    app.service.export_backup(BACKUP_PATH)
    app.root.update()
    main_view.password_value.set("")
    app.root.update_idletasks()
    main_view.password_value.set(app.service.reveal_password(int(selected)))
    main_view.feedback_var.set("Encrypted backup exported successfully")
    app.root.update_idletasks()
    capture_widget(app.root, "04_reveal_export.png")

    app.root.destroy()


def verify_plaintext_not_stored() -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        values = connection.execute("SELECT password_encrypted FROM credentials").fetchall()
    content = " ".join(value[0] for value in values)
    assert "Gh!DemoPass2026" not in content
    assert "B@nkSafe!77Vault" not in content


if __name__ == "__main__":
    reset_demo_files()
    seed_and_capture()
    verify_plaintext_not_stored()
    print("Demo data prepared and screenshots captured.")
