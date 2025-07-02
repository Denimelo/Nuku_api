from sqlalchemy import Column, String, Date, Integer, Boolean, Enum, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
import enum

class ValidationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Entrepreneur(Base):
    __tablename__ = "entrepreneurs"

    entrepreneur_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 🔐 Clé étrangère vers la table des utilisateurs
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)

    # 📛 Informations générales sur l’entreprise
    company_name = Column(String, nullable=False)  # Nom de l’entreprise (ou future entreprise)
    company_registration_number = Column(String, nullable=True)  # Numéro d’enregistrement (si entreprise créée)
    company_description = Column(String, nullable=True)  # Brève description de l’entreprise
    industry_sector = Column(String, nullable=True)  # Secteur d'activité
    founding_date = Column(Date, nullable=True)  # Date de création de l’entreprise (si applicable)

    # 📈 Données économiques
    number_of_employees = Column(Integer, nullable=True)  # Nombre d’employés (pour entreprise établie)
    annual_revenue = Column(Float, nullable=True)  # Chiffre d'affaires annuel

    # 💰 Données sur le financement
    has_raised_funds = Column(Boolean, default=False)  # A-t-il déjà levé des fonds ?
    amount_raised = Column(Float, nullable=True)  # Montant déjà levé
    wants_to_raise_funds = Column(Boolean, default=False)  # Souhaite-t-il lever des fonds ?
    desired_funding_amount = Column(Float, nullable=True)  # Montant recherché

    # 🧾 Documents et pièces justificatives
    identity_card_url = Column(String, nullable=True)  # Carte d’identité de l’entrepreneur
    company_logo_url = Column(String, nullable=True)  # Logo de l’entreprise
    registration_document_url = Column(String, nullable=True)  # Document d’enregistrement de l’entreprise
    professional_card_url = Column(String, nullable=True)  # Carte professionnelle

    # ✅ Niveau de maturité de l’entreprise (un seul des 3 doit être vrai)
    company_not_created = Column(Boolean, default=False)  # L’entreprise n’existe pas encore
    company_recently_created = Column(Boolean, default=False)  # L’entreprise a été créée récemment
    company_established = Column(Boolean, default=False)  # L’entreprise est déjà bien établie

    # 🕵️ Statut de validation par l’admin
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.pending)
    validation_date = Column(DateTime, nullable=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    # 🔁 Relation avec l’utilisateur propriétaire du profil
    __table_args__ = (
        {"comment": "Table des entrepreneurs, qui sont des utilisateurs avec un profil d'entreprise."}
    )
    user = relationship("User", back_populates="entrepreneur_profile", foreign_keys=[user_id])
    program_participations = relationship("ProgramParticipant", back_populates="entrepreneur")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="entrepreneur")
    call_participations = relationship("CallParticipant", back_populates="entrepreneur")
