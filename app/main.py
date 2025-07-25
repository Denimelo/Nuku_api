from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine 
from app.startup import create_default_admin
from app.routes import (
  admin, 
  notification,
  assignment,
  assignmentSubmission,
  auth, 
  call,
  callParticipant,
  document, 
  entrepreneur, 
  expert,
  message, 
  module, 
  moduleContent, 
  program, 
  user,
  otp,
  upload,
)

# 🔌 Vérification de la connexion à la base de données
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("✅ Connexion à la base Supabase réussie.")
    except Exception as e:
        print("❌ Erreur de connexion à la base Supabase :", e)

# 🧱 Création automatique des tables
Base.metadata.create_all(bind=engine)

# 🚀 Création de l'administrateur par défaut
create_default_admin()

# 🌐 Initialisation de l'application FastAPI
app = FastAPI(
    title="NUKU API",
    description="API pour la plateforme d'accélération des MPME",
    version="1.0.0"
)

# 🔌 Vérification de la base au démarrage
test_db_connection()

# 🔐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚩 Route par défaut
@app.get("/")
def root():
    return {"message": "Lancement de l'API réussi"}

# 📦 Inclusion des routes
app.include_router(auth.router, tags=["auth"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(user.router, tags=["User"])
app.include_router(entrepreneur.router, tags=["Entrepreneur"])
app.include_router(expert.router, tags=["Expert"])
app.include_router(program.router, tags=["Program"])
app.include_router(module.router, tags=["Module"])
app.include_router(moduleContent.router, tags=["ModuleContent"])
app.include_router(message.router, tags=["Messages"])
app.include_router(callParticipant.router, tags=["CallParticipant"])
app.include_router(assignment.router, tags=["Assignment"])
app.include_router(assignmentSubmission.router, tags=["AssignmentSubmission"])
app.include_router(call.router, tags=["Call"])
app.include_router(document.router, tags=["Document"])
app.include_router(notification.router, tags=["Notification"])
app.include_router(otp.router, tags=["OTP"])
app.include_router(upload.router, tags=["Upload"])

