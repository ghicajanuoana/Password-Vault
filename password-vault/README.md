# Password Vault

A simple desktop password manager built with Python, Tkinter, SQLite, and Fernet.

## Features

- Master password setup and unlock flow
- Local SQLite storage with encrypted passwords
- Add, edit, delete, list, and search credentials
- Reveal and copy passwords
- Password generator with strength feedback
- Encrypted backup export to `.txt`
- Input validation
- Tests and screenshots

## Architecture

- `app.py`: application bootstrap and screen switching
- `security/crypto_manager.py`: key derivation, session handling, encryption, decryption
- `repositories/vault_repository.py`: SQLite schema and persistence
- `services/vault_service.py`: validation, CRUD, export, and app logic
- `ui/`: login/setup window, main dashboard, and credential dialog

## Data Model

- `vault_meta`: encryption salt, verification salt, verification hash, created timestamp, app version
- `credentials`: site, username, encrypted password, notes, created timestamp, updated timestamp

## Tech Stack

- Python 3.13+
- Tkinter
- SQLite
- `cryptography`
- Pillow

## Project Structure

```text
password-vault/
|-- README.md
|-- requirements.txt
|-- data/
|-- docs/
|   `-- screenshots/
|-- exports/
|-- scripts/
|-- src/
|   |-- main.py
|   `-- password_vault/
|       |-- app.py
|       |-- config.py
|       |-- models/
|       |-- repositories/
|       |-- security/
|       |-- services/
|       `-- ui/
`-- tests/
```

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python src/main.py
```

## Test

```powershell
python -m unittest discover -s tests -v
```

## Demo Data and Screenshots

Generate demo data and screenshots:

```powershell
python scripts/run_demo.py
```

Screenshots are stored in `docs/screenshots/`:

- `01_setup_window.png`
- `02_main_window.png`
- `03_add_dialog.png`
- `04_reveal_export.png`

The demo script also:

- resets the local vault files
- seeds mock credentials
- exports an encrypted backup to `exports/vault_backup.txt`
- verifies that plaintext passwords are not stored in SQLite

## Typical Usage

1. Launch the application.
2. Create the vault with a master password on first run.
3. Add credentials and optionally generate strong passwords.
4. Search, reveal, copy, edit, or delete saved entries.
5. Export an encrypted backup when needed.

## Security Notes

- The master password is never stored in plaintext.
- Vault unlock uses a derived hash and per-vault salts.
- Stored passwords are encrypted before writing to SQLite.
- The backup export is encrypted with the same master-password-derived key used for the active vault session.
