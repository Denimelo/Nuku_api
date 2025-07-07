# NUKU - Plateforme d’Accélération de PME

NUKU est une plateforme web d’accompagnement et d’accélération pour entrepreneurs, experts et administrateurs. Elle permet la gestion de programmes, la diffusion de contenus pédagogiques, la messagerie interne, le suivi des progrès et la certification.

---

## 🚀 Fonctionnalités principales

- **Gestion des utilisateurs** : inscription entrepreneurs, validation admin, gestion experts/admins.
- **Programmes d’accélération** : création, gestion, assignation d’experts, modules, contenus.
- **Messagerie interne** : échanges entre entrepreneurs, experts et admins.
- **Gestion documentaire** : upload et partage de ressources par programme.
- **Suivi & reporting** : feedback, notes, progression, génération de certificats.
- **Sécurité** : rôles, permissions, accès restreint aux ressources.

---

## 📁 Structure du projet

```
Nuku_api/
│
├── app/
│   ├── crud/         # Logique CRUD pour chaque entité
│   ├── models/       # Modèles SQLAlchemy
│   ├── routes/       # Endpoints FastAPI
│   ├── schemas/      # Schémas Pydantic
│   ├── utils/        # Fonctions utilitaires (sécurité, email, etc.)
│   ├── main.py       # Point d’entrée FastAPI
│   └── database.py   # Connexion à la base de données
│
├── tests/            # Tests unitaires et d’intégration
├── requirements.txt  # Dépendances Python
└── README.md         # Ce fichier
```

---

## ⚙️ Installation & Lancement

### Prérequis

- Python 3.10+
- PostgreSQL (ou autre SGBD compatible SQLAlchemy)
- (Optionnel) [Poetry](https://python-poetry.org/) ou pipenv

### Installation

```bash
git clone <repo_url>
cd Nuku_api
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### Configuration

- Copie le fichier `.env.example` en `.env` et configure tes variables (DB, SECRET_KEY, etc.).
- Crée la base de données PostgreSQL.

### Migration de la base

```bash
alembic upgrade head
```

### Lancement du serveur

```bash
uvicorn app.main:app --reload
```

---

## 📚 Documentation API

- Accès à la documentation interactive :  
  [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- Documentation OpenAPI :  
  [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧑‍💻 Tests

```bash
pytest
```

---

## 👤 Rôles & Permissions

- **Administrateur** : gestion des comptes, programmes, rapports, arbitrage.
- **Expert** : création de contenus, accompagnement, feedback, animation de calls.
- **Entrepreneur** : inscription, accès aux modules, soumission d’exercices, messagerie.

---

## 📦 Entités principales

- Utilisateur (User)
- Programme (Program)
- Module
- Document
- Message
- Assignment
- Call
- ProgramExpert
- ProgramParticipant
- Expert
- Entrepreneur
- Admin
- Participation
- Feedback

---

## 🔒 Sécurité

- Authentification JWT
- Permissions par rôle
- Accès restreint aux ressources selon le programme et le rôle
- CORS configurable

---

## ✨ Contribution

1. Fork le repo
2. Crée une branche (`git checkout -b feature/ma-feature`)
3. Commit tes changements (`git commit -am 'feat: nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/ma-feature`)
5. Ouvre une Pull Request

---

## 📧 Contact

Pour toute question ou suggestion, contacte l’équipe à :  
**contact@nuku-platform.com**

---

## 📝 Licence

Projet sous licence MIT.
