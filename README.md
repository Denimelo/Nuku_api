# NUKU API - Plateforme d'Accélération de PME

NUKU est une API REST complète pour une plateforme d'accompagnement et d'accélération d'entrepreneurs. Elle propose un écosystème complet de gestion de programmes, formation, mentorat, et évaluation.

---

## 🌟 Vue d'ensemble

La plateforme NUKU connecte trois types d'utilisateurs :
- **Entrepreneurs** : Participants aux programmes d'accélération
- **Experts** : Mentors et formateurs accompagnant les entrepreneurs
- **Administrateurs** : Gestionnaires de la plateforme

---

## 🚀 Fonctionnalités principales

### 👥 **Gestion des utilisateurs**
- Inscription et validation des entrepreneurs
- Gestion des experts et administrateurs
- Système d'authentification JWT sécurisé
- Gestion des profils et préférences

### 📚 **Modules de formation**
- Création de contenus pédagogiques par les experts
- Modules avec contenus multimédias (vidéo, audio, documents, texte)
- Suivi de progression détaillé
- Système de prérequis et d'organisation

### 📝 **Système d'évaluations**
- Devoirs variés (quiz, essais, projets, présentations)
- Soumissions avec fichiers multiples
- Évaluation par les experts avec feedback détaillé
- Gestion des tentatives et échéances

### 💬 **Messaging avancé**
- Messages directs entre utilisateurs
- Conversations de groupe par programme
- Pièces jointes multiples
- Réactions et fils de discussion
- Recherche avancée dans l'historique

### 📞 **Système d'appels/visioconférences**
- Planification de sessions (1:1, groupe, webinaire, atelier)
- Gestion des participants et invitations
- Intégration avec plateformes externes (Zoom, Teams)
- Enregistrements et transcriptions
- Templates d'appels récurrents

### 🔔 **Notifications intelligentes**
- 25+ types de notifications contextuelles
- Canaux multiples (app, email, push, SMS)
- Préférences utilisateur granulaires
- Heures silencieuses et digest email
- Templates personnalisables

### 📊 **Programmes d'accélération**
- Création et gestion de programmes
- Attribution d'experts aux programmes
- Inscription et suivi des participants
- Durées flexibles et dates personnalisées

### 📄 **Gestion documentaire**
- Upload sécurisé via Supabase Storage
- Partage de documents par programme
- Gestion des permissions d'accès
- Versioning et historique

---

## 📁 Architecture du projet

```
Nuku_api/
│
├── app/
│   ├── auth/                    # Authentification et sécurité
│   │   ├── dependencies.py      # Dépendances auth (get_current_user, etc.)
│   │   └── security.py          # JWT, hashing, tokens
│   │
│   ├── crud/                    # Logique CRUD pour chaque entité
│   │   ├── assignment.py        # CRUD assignments/devoirs
│   │   ├── call.py              # CRUD appels/visioconférences
│   │   ├── document.py          # CRUD documents
│   │   ├── entrepreneur.py      # CRUD entrepreneurs
│   │   ├── expert.py            # CRUD experts
│   │   ├── message.py           # CRUD messages/conversations
│   │   ├── module.py            # CRUD modules de formation
│   │   ├── notification.py      # CRUD notifications
│   │   ├── program.py           # CRUD programmes
│   │   └── user.py              # CRUD utilisateurs
│   │
│   ├── models/                  # Modèles SQLAlchemy
│   │   ├── assignment.py        # Modèles devoirs et soumissions
│   │   ├── assignmentSubmission.py
│   │   ├── call.py              # Modèles appels
│   │   ├── callParticipant.py
│   │   ├── callRecording.py
│   │   ├── callTemplate.py
│   │   ├── conversation.py      # Modèles conversations
│   │   ├── document.py          # Modèles documents
│   │   ├── entrepreneur.py      # Modèle entrepreneur
│   │   ├── expert.py            # Modèle expert
│   │   ├── message.py           # Modèles messages
│   │   ├── messageAttachment.py
│   │   ├── messageReaction.py
│   │   ├── module.py            # Modèles modules formation
│   │   ├── moduleContent.py
│   │   ├── moduleProgress.py
│   │   ├── notification.py      # Modèles notifications
│   │   ├── notificationTemplate.py
│   │   ├── program.py           # Modèle programme
│   │   ├── user.py              # Modèle utilisateur de base
│   │   └── userNotificationPreferences.py
│   │
│   ├── routes/                  # Endpoints FastAPI organisés par domaine
│   │   ├── admin.py             # Routes administration
│   │   ├── assignment.py        # Routes devoirs/évaluations
│   │   ├── auth.py              # Routes authentification
│   │   ├── call.py              # Routes appels/visioconférences
│   │   ├── document.py          # Routes gestion documentaire
│   │   ├── entrepreneur.py      # Routes entrepreneurs
│   │   ├── expert.py            # Routes experts
│   │   ├── message.py           # Routes messaging
│   │   ├── module.py            # Routes modules formation
│   │   ├── notification.py      # Routes notifications
│   │   ├── program.py           # Routes programmes
│   │   ├── upload.py            # Routes upload fichiers
│   │   └── user.py              # Routes utilisateurs
│   │
│   ├── schemas/                 # Schémas Pydantic pour validation
│   │   ├── assignment.py        # Schémas devoirs
│   │   ├── auth.py              # Schémas authentification
│   │   ├── call.py              # Schémas appels
│   │   ├── document.py          # Schémas documents
│   │   ├── entrepreneur.py      # Schémas entrepreneur
│   │   ├── expert.py            # Schémas expert
│   │   ├── message.py           # Schémas messages
│   │   ├── module.py            # Schémas modules
│   │   ├── notification.py      # Schémas notifications
│   │   ├── program.py           # Schémas programmes
│   │   └── user.py              # Schémas utilisateurs
│   │
│   ├── services/                # Services métier
│   │   └── notification_service.py  # Service notifications centralisé
│   │
│   ├── utils/                   # Fonctions utilitaires
│   │   ├── email.py             # Envoi d'emails
│   │   ├── security.py          # Fonctions sécurité
│   │   └── supabase_storage.py  # Intégration Supabase Storage
│   │
│   ├── database.py              # Configuration base de données
│   ├── main.py                  # Point d'entrée FastAPI
│   └── __init__.py
│
├── tests/                       # Tests (à développer)
├── requirements.txt             # Dépendances Python
├── .env.example                 # Variables d'environnement exemple
└── README.md                    # Cette documentation
```

---

## ⚙️ Installation & Configuration

### Prérequis

- **Python 3.10+**
- **PostgreSQL 14+** (base de données principale)
- **Supabase** (stockage de fichiers)
- **Redis** (optionnel, pour le cache)

### Installation

```bash
# Cloner le repository
git clone <repository_url>
cd Nuku_api

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration

1. **Variables d'environnement** - Créer le fichier `.env` :

```env
# Base de données
DATABASE_URL=postgresql://username:password@localhost:5432/nuku_db

# Sécurité
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase (stockage fichiers)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Email (optionnel)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Environnement
ENVIRONMENT=development
```

2. **Base de données** - Créer la base PostgreSQL :

```sql
CREATE DATABASE nuku_db;
CREATE USER nuku_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nuku_db TO nuku_user;
```

### Lancement

```bash
# Démarrer le serveur de développement
uvicorn app.main:app --reload --port 8000

# Ou avec hot reload avancé
python -m app.main
```

L'API sera accessible sur : **http://localhost:8000**

---

## 📚 Documentation API

### Accès à la documentation

- **Swagger UI (interactif)** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (documentation)** : [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON** : [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Authentification

L'API utilise l'authentification JWT Bearer Token :

```bash
# Connexion
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Utilisation du token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer your-jwt-token"
```

---

## 🔗 Endpoints principaux

### 🔐 **Authentification** (`/api/v1/auth`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/login` | Connexion utilisateur |
| POST | `/register` | Inscription entrepreneur |
| POST | `/logout` | Déconnexion |
| GET | `/me` | Profil utilisateur actuel |
| POST | `/refresh` | Renouveler le token |

### 👥 **Utilisateurs** (`/api/v1/users`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/me` | Mon profil |
| PUT | `/me` | Modifier mon profil |
| GET | `/` | Lister utilisateurs (admin) |
| GET | `/{user_id}` | Détails utilisateur |
| PUT | `/{user_id}` | Modifier utilisateur |

### 📚 **Modules** (`/api/v1/modules`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/` | Créer module (expert) |
| GET | `/{module_id}` | Détails module |
| PUT | `/{module_id}` | Modifier module |
| DELETE | `/{module_id}` | Supprimer module |
| GET | `/program/{program_id}` | Modules d'un programme |
| POST | `/{module_id}/contents` | Ajouter contenu |
| GET | `/{module_id}/contents` | Contenus d'un module |
| POST | `/{module_id}/progress/start` | Commencer module |
| POST | `/{module_id}/progress/content/{content_id}` | Marquer contenu terminé |

### 📝 **Devoirs/Assignments** (`/api/v1/assignments`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/` | Créer devoir (expert) |
| GET | `/{assignment_id}` | Détails devoir |
| PUT | `/{assignment_id}` | Modifier devoir |
| POST | `/{assignment_id}/submit` | Soumettre devoir |
| GET | `/entrepreneur/available` | Mes devoirs disponibles |
| GET | `/entrepreneur/submissions` | Mes soumissions |
| GET | `/expert/my-assignments` | Mes devoirs créés |
| GET | `/grading/pending` | Soumissions à évaluer |
| POST | `/submissions/{submission_id}/grade` | Évaluer soumission |

### 💬 **Messages** (`/api/v1/messages`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/` | Envoyer message |
| GET | `/conversations/` | Mes conversations |
| GET | `/conversations/{conversation_id}` | Messages d'une conversation |
| POST | `/with-attachment` | Message avec fichiers |
| PUT | `/conversations/{conversation_id}/read` | Marquer comme lu |
| POST | `/{message_id}/reactions` | Ajouter réaction |
| DELETE | `/{message_id}/reactions` | Supprimer réaction |

### 📞 **Appels** (`/api/v1/calls`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/` | Créer appel |
| GET | `/{call_id}` | Détails appel |
| PUT | `/{call_id}` | Modifier appel |
| DELETE | `/{call_id}` | Annuler appel |
| POST | `/{call_id}/start` | Démarrer appel |
| POST | `/{call_id}/end` | Terminer appel |
| POST | `/{call_id}/join` | Rejoindre appel |
| POST | `/{call_id}/leave` | Quitter appel |
| POST | `/{call_id}/invite` | Inviter participants |
| GET | `/upcoming` | Appels à venir |

### 🔔 **Notifications** (`/api/v1/notifications`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Mes notifications |
| GET | `/summary` | Résumé notifications |
| POST | `/{notification_id}/read` | Marquer comme lue |
| POST | `/read-all` | Marquer toutes comme lues |
| GET | `/preferences` | Mes préférences |
| PUT | `/preferences` | Modifier préférences |

### 📄 **Documents** (`/api/v1/documents`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/upload` | Upload document |
| GET | `/program/{program_id}` | Documents d'un programme |
| GET | `/{document_id}` | Détails document |
| DELETE | `/{document_id}` | Supprimer document |

---

## 🏗️ Modèles de données

### 👤 **User (Utilisateur de base)**
```python
{
  "user_id": "uuid",
  "email": "string",
  "first_name": "string", 
  "last_name": "string",
  "user_type": "entrepreneur|expert|admin",
  "status": "pending|active|inactive",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 🚀 **Entrepreneur**
```python
{
  "entrepreneur_id": "uuid",
  "user_id": "uuid",
  "company_name": "string",
  "company_description": "text",
  "industry": "string",
  "website_url": "string",
  "validation_status": "pending|approved|rejected",
  "validation_date": "datetime"
}
```

### 🎓 **Expert**
```python
{
  "expert_id": "uuid",
  "user_id": "uuid", 
  "specialization": "string",
  "bio": "text",
  "experience_years": "integer",
  "linkedin_url": "string",
  "hourly_rate": "decimal"
}
```

### 📚 **Module**
```python
{
  "module_id": "uuid",
  "title": "string",
  "description": "text",
  "module_type": "lesson|workshop|assessment",
  "difficulty_level": "beginner|intermediate|advanced",
  "estimated_duration_minutes": "integer",
  "status": "draft|published",
  "created_by": "uuid",
  "program_id": "uuid"
}
```

### 📝 **Assignment**
```python
{
  "assignment_id": "uuid",
  "title": "string",
  "description": "text",
  "assignment_type": "quiz|essay|project|presentation",
  "max_score": "decimal",
  "due_date": "datetime",
  "module_id": "uuid",
  "created_by": "uuid"
}
```

### 💬 **Message**
```python
{
  "message_id": "uuid",
  "sender_id": "uuid",
  "receiver_id": "uuid",
  "subject": "string",
  "message_text": "text",
  "sent_at": "datetime",
  "is_read": "boolean",
  "attachments": ["MessageAttachment"],
  "reactions": ["MessageReaction"]
}
```

### 📞 **Call**
```python
{
  "call_id": "uuid",
  "title": "string",
  "call_type": "one_on_one|group_session|webinar",
  "scheduled_start": "datetime",
  "scheduled_end": "datetime",
  "meeting_url": "string",
  "status": "scheduled|in_progress|completed",
  "expert_id": "uuid",
  "participants": ["CallParticipant"]
}
```

---

## 🔒 Sécurité & Permissions

### Rôles utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Admin** | Accès complet, gestion utilisateurs, programmes, modération |
| **Expert** | Création contenus, évaluation, mentorat, gestion appels |
| **Entrepreneur** | Consultation contenus, soumission devoirs, participation appels |

### Authentification

- **JWT Bearer Tokens** avec expiration configurable
- **Refresh tokens** pour renouvellement automatique
- **Hash bcrypt** pour les mots de passe
- **Validation email** pour les nouveaux comptes

### Autorisations

```python
# Exemples de vérifications d'autorisation
@require_admin          # Réservé aux admins
@require_expert         # Réservé aux experts  
@require_entrepreneur   # Réservé aux entrepreneurs
@get_current_user       # Utilisateur connecté requis
```

---

## 🧪 Tests

### Lancement des tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app

# Tests spécifiques
pytest tests/test_auth.py
pytest tests/test_modules.py
```

### Structure des tests

```
tests/
├── conftest.py              # Configuration pytest
├── test_auth.py             # Tests authentification
├── test_users.py            # Tests utilisateurs
├── test_modules.py          # Tests modules
├── test_assignments.py      # Tests devoirs
├── test_messages.py         # Tests messaging
├── test_calls.py            # Tests appels
└── test_notifications.py   # Tests notifications
```

---

## 🚀 Déploiement

### Déploiement sur Render

L'API est actuellement déployée sur : **https://nuku-api.onrender.com**

#### Configuration Render

1. **Variables d'environnement** configurées dans le dashboard Render
2. **Build Command** : `pip install -r requirements.txt`
3. **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Déploiement local avec Docker

```dockerfile
# Dockerfile
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build et run
docker build -t nuku-api .
docker run -p 8000:8000 nuku-api
```

---

## 📊 Monitoring & Logs

### Logs

L'API génère des logs structurés pour :
- Authentification (connexions, échecs)
- Opérations CRUD importantes  
- Erreurs et exceptions
- Performance des requêtes

### Health Check

- **Endpoint** : `GET /health`
- **Statut base de données** : Vérification connexion
- **Statut Supabase** : Vérification stockage
- **Métriques système** : Usage mémoire, CPU

---

## 🔄 Évolutions futures

### Fonctionnalités prévues

- [ ] **Système de gamification** (badges, points, classements)
- [ ] **Analytics avancées** (tableaux de bord, métriques)
- [ ] **Intégrations** (Slack, Discord, Zapier)
- [ ] **API GraphQL** (alternative REST)
- [ ] **Webhooks** (notifications externes)
- [ ] **Cache Redis** (performances)
- [ ] **Rate limiting** (protection DDOS)
- [ ] **Audit logs** (traçabilité complète)

### Optimisations techniques

- [ ] **Mise en cache** des requêtes fréquentes
- [ ] **Pagination automatique** pour grandes listes
- [ ] **Compression** des réponses API
- [ ] **CDN** pour les assets statiques
- [ ] **Monitoring** avec Prometheus/Grafana

---

## 🛠️ Développement

### Prérequis développeur

```bash
# Outils de développement
pip install black isort flake8 mypy pytest-cov

# Pre-commit hooks
pre-commit install
```

### Standards de code

- **Formatage** : Black (88 caractères max)
- **Import sorting** : isort
- **Linting** : flake8
- **Type checking** : mypy
- **Documentation** : Docstrings Google style

### Workflow de développement

1. **Créer une branche** : `git checkout -b feature/nouvelle-fonctionnalite`
2. **Développer** avec tests
3. **Formater le code** : `black . && isort .`
4. **Tester** : `pytest`
5. **Commit** : Messages conventionnels (`feat:`, `fix:`, `docs:`)
6. **Pull Request** avec review

---

## 📞 Support & Contact

### Équipe de développement

- **Lead Developer** : [Nom]
- **Backend Team** : [Équipe]
- **API Documentation** : Cette documentation

### Support technique

- **Issues GitHub** : Pour bugs et demandes de fonctionnalités
- **Email support** : support@nuku-platform.com
- **Documentation** : Swagger UI intégrée

### Liens utiles

- **Déploiement production** : https://nuku-api.onrender.com
- **Documentation API** : https://nuku-api.onrender.com/docs
- **Status page** : https://status.nuku-platform.com (à créer)

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier `LICENSE` pour plus de détails.

---

## 🙏 Remerciements

Merci à tous les contributeurs qui ont participé au développement de cette API robuste et complète.

---

**NUKU API v1.0** - *Accélérons ensemble l'entrepreneuriat* 🚀