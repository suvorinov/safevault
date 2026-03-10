"""Вспомогательные утилиты для работы с данными."""
from bson import Binary

def to_binary(data: bytes) -> Binary:
    """Преобразует байты в BSON Binary для хранения в MongoDB."""
    return Binary(data, subtype=0)
