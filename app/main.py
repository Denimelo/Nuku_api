from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.startup import create_default_admin
from app.routes import auth, admin, user

# 🧱 Création automatique des tables au lancement
Base.metadata.create_all(bind=engine)

# 🚀 Création de l'administrateur par défaut si inexistant
create_default_admin()

# 🌐 Initialisation de l'application FastAPI
# Initialisation de l'application FastAPI
app = FastAPI(
    title="NUKU API",
    description="API pour la plateforme d'accélération des MPME",
    version="1.0.0"
)

# 🔐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Inclusion des routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(user.router, prefix="/user", tags=["User"])
