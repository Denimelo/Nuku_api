from sqlalchemy.orm import Session
from app.models.entrepreneur import Entrepreneur, ValidationStatus
from app.schemas.entrepreneur import EntrepreneurCreate
from app.crud.user import create_user

def create_entrepreneur(db: Session, data: EntrepreneurCreate) -> Entrepreneur:
    user = create_user(db, data.user)

    entrepreneur = Entrepreneur(
        user_id=user.user_id,
        company_name=data.company_name,
        company_registration_number=data.company_registration_number,
        company_description=data.company_description,
        industry_sector=data.industry_sector,
        founding_date=data.founding_date,
        number_of_employees=data.number_of_employees,
        annual_revenue=data.annual_revenue,
        has_raised_funds=data.has_raised_funds,
        amount_raised=data.amount_raised,
        wants_to_raise_funds=data.wants_to_raise_funds,
        desired_funding_amount=data.desired_funding_amount,
        
        # Ajout des documents
        identity_card_url=str(data.identity_card_url) if data.identity_card_url else None,
        company_logo_url=str(data.company_logo_url) if data.company_logo_url else None,
        registration_document_url=str(data.registration_document_url) if data.registration_document_url else None,
        professional_card_url=str(data.professional_card_url) if data.professional_card_url else None,

        # Niveau d’entreprise
        company_not_created=data.company_not_created,
        company_recently_created=data.company_recently_created,
        company_established=data.company_established,

        validation_status=ValidationStatus.pending,
    )
    db.add(entrepreneur)
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur



def get_entrepreneur_by_user_id(db: Session, user_id) -> Entrepreneur:
    return db.query(Entrepreneur).filter(Entrepreneur.user_id == user_id).first()

def get_entrepreneur_by_id(db: Session, entrepreneur_id: str) -> Entrepreneur:
    return db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
