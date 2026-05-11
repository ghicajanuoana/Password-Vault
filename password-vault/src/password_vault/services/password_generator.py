from __future__ import annotations

import secrets
import string


class PasswordGenerator:
    SYMBOLS = "!@#$%^&*()-_=+[]{}?"

    def generate(self, length: int = 18) -> str:
        if length < 12:
            length = 12

        alphabet = string.ascii_letters + string.digits + self.SYMBOLS
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(length))
            if self._is_strong(password):
                return password

    def strength_label(self, password: str) -> str:
        if not password:
            return "Strength: Empty"

        score = 0
        if len(password) >= 12:
            score += 1
        if any(ch.islower() for ch in password):
            score += 1
        if any(ch.isupper() for ch in password):
            score += 1
        if any(ch.isdigit() for ch in password):
            score += 1
        if any(ch in self.SYMBOLS for ch in password):
            score += 1

        if score <= 2:
            return "Strength: Weak"
        if score == 3:
            return "Strength: Fair"
        if score == 4:
            return "Strength: Strong"
        return "Strength: Excellent"

    def _is_strong(self, password: str) -> bool:
        return (
            len(password) >= 12
            and any(ch.islower() for ch in password)
            and any(ch.isupper() for ch in password)
            and any(ch.isdigit() for ch in password)
            and any(ch in self.SYMBOLS for ch in password)
        )
