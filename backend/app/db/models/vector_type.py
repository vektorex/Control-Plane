import json
from typing import Any, List, Optional
from sqlalchemy.types import TypeDecorator, JSON

try:
    from pgvector.sqlalchemy import Vector as PGVector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class VectorType(TypeDecorator):
    """
    Platform-independent embedding vector column type.
    Uses native pgvector Vector on PostgreSQL, and JSON (array of floats) on SQLite.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 1536, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(PGVector(self.dim))
        return dialect.type_descriptor(JSON)

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            if dialect.name == "postgresql" and HAS_PGVECTOR:
                return [float(x) for x in value]
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return [float(x) for x in parsed]
            except Exception:
                return value
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return [float(x) for x in parsed]
            except Exception:
                return None
        return value
