"""
T10: Hassas finansal veriler için at-rest encryption.
Fernet symmetric encryption kullanır; anahtar .env üzerinden yönetilir.
"""
import base64
import os
from decimal import Decimal
from typing import Optional, Any

from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, Text


def _get_cipher() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        # Dev ortamında otomatik anahtar üret (production'da zorunlu)
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedType(TypeDecorator):
    """
    SQLAlchemy column type: veritabanına yazarken şifreler, okurken çözer.
    Numeric değerleri (finansal rakamlar) string olarak şifreler.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        cipher = _get_cipher()
        return cipher.encrypt(str(value).encode()).decode()

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            cipher = _get_cipher()
            decrypted = cipher.decrypt(value.encode()).decode()
            return Decimal(decrypted)
        except Exception:
            return None
