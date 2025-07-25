from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
import time
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import Base, engine 
from app.startup import create_default_admin
from app.routes import (
  admin, 
  notification,
  assignment,
  auth, 
  call,
  callParticipant,
  document, 
  entrepreneur, 
  expert,
  message, 
  module, 
  program, 
  user,
  otp,
  upload,
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔌 Vérification de la connexion à la base de données
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("✅ Connexion à la base Supabase réussie.")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la base Supabase : {e}")
        return False

# 🚀 Gestionnaire de cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    logger.info("🚀 Démarrage de l'API NUKU...")
    
    # 🧱 Création automatique des tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables créées avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur création tables : {e}")
    
    # 🔌 Vérification de la base au démarrage
    if not test_db_connection():
        logger.warning("⚠️ Problème de connexion à la base de données")
    
    # 🚀 Création de l'administrateur par défaut
    try:
        create_default_admin()
    except Exception as e:
        logger.error(f"❌ Erreur création admin : {e}")
    
    logger.info("🎉 API NUKU démarrée avec succès !")
    
    yield
    
    # Arrêt
    logger.info("🛑 Arrêt de l'API NUKU...")

# 🌐 Initialisation de l'application FastAPI
app = FastAPI(
    title="NUKU API",
    description="API pour la plateforme d'accélération des MPME",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.PROJECT_NAME != "production" else None,  # Disable docs in production
    redoc_url="/redoc" if settings.PROJECT_NAME != "production" else None
)

# 🕒 Middleware de timing des requêtes
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}")
    return response

# 🔐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.PROJECT_NAME != "production" else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# 🚨 Gestionnaire d'erreurs global
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Erreur de validation des données",
            "errors": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"Erreur serveur : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur"}
    )

# 🚩 Route par défaut avec health check
@app.get("/")
def root():
    return {
        "message": "API NUKU - Plateforme d'accélération des MPME",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    db_status = test_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": time.time()
    }

# 📦 Inclusion des routes avec préfixes organisés
app.include_router(auth.router, prefix="/api/v1")
app.include_router(otp.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")

app.include_router(admin.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(entrepreneur.router, prefix="/api/v1")
app.include_router(expert.router, prefix="/api/v1")

app.include_router(program.router, prefix="/api/v1")
app.include_router(module.router, prefix="/api/v1")
app.include_router(assignment.router, prefix="/api/v1")

app.include_router(call.router, prefix="/api/v1")
app.include_router(callParticipant.router, prefix="/api/v1")
app.include_router(message.router, prefix="/api/v1")
app.include_router(notification.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")

# 📋 Route d'information sur l'API
@app.get("/api/v1/info")
def api_info():
    return {
        "api_name": "NUKU API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "upload": "/api/v1/upload", 
            "admin": "/api/v1/admin",
            "programs": "/api/v1/program"
        }
    }