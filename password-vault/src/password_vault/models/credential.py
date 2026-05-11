from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Credential:
    site: str
    username: str
    encrypted_password: str
    notes: str
    created_at: str
    updated_at: str
    credential_id: Optional[int] = None

    @property
    def id(self) -> Optional[int]:
        return self.credential_id
