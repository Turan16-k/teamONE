"""T10: At-rest encryption birim testleri"""
import os
from decimal import Decimal
from cryptography.fernet import Fernet

os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from app.utils.encryption import EncryptedType


def test_encrypt_decrypt_roundtrip():
    enc = EncryptedType()
    value = Decimal("1234567.89")
    encrypted = enc.process_bind_param(value, None)

    assert encrypted is not None
    assert encrypted != str(value)  # gerçekten şifrelenmiş olmalı

    decrypted = enc.process_result_value(encrypted, None)
    assert decrypted == value


def test_encrypt_none_returns_none():
    enc = EncryptedType()
    assert enc.process_bind_param(None, None) is None
    assert enc.process_result_value(None, None) is None


def test_encrypted_value_is_opaque():
    enc = EncryptedType()
    value = Decimal("999999.00")
    encrypted = enc.process_bind_param(value, None)
    assert "999999" not in encrypted  # ham değer şifreli içinde görünmemeli
