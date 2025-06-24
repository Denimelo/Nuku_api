# app/utils/uuid.py

import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column

def uuid_column():
    """
    Utilitaire pour générer une colonne UUID avec valeur par défaut.
    """
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True, nullable=False)
