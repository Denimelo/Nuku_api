# Fichier: app/schemas/__init__.py
from .user import UserBase, UserCreate, UserUpdate, UserOut  # Liste complète
from .entrepreneur import EntrepreneurCreate, EntrepreneurOut
from .expert import ExpertCreate, ExpertOut

__all__ = [
    'UserBase', 'UserCreate', 'UserUpdate', 'UserOut',
    'EntrepreneurCreate', 'EntrepreneurOut',
    'ExpertCreate', 'ExpertOut'
]