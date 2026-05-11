from pathlib import Path


APP_NAME = "Password Vault"
APP_VERSION = "1.0.0"
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
EXPORT_DIR = ROOT_DIR / "exports"
DOCS_DIR = ROOT_DIR / "docs"
SCREENSHOT_DIR = DOCS_DIR / "screenshots"
DB_PATH = DATA_DIR / "vault.db"
BACKUP_PATH = EXPORT_DIR / "vault_backup.txt"
WINDOW_MIN_SIZE = (1080, 680)
PBKDF2_ITERATIONS = 390_000
PASSWORD_MIN_LENGTH = 10


def ensure_runtime_directories() -> None:
    for path in (DATA_DIR, EXPORT_DIR, DOCS_DIR, SCREENSHOT_DIR):
        path.mkdir(parents=True, exist_ok=True)
