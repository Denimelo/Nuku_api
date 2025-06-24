import asyncio
from app.utils.email import email_service
from app.config import settings

async def test_email():
    await email_service.send_email(
        email_to="votre_autre_email@test.com",  # Un email où vous voulez recevoir le test
        subject="Test SMTP Gmail",
        template_name="expert_invitation",
        template_data={
            "first_name": "Test",
            "email": "test@test.com",
            "temporary_password": "12345678",
            "login_url": "http://localhost:8000/test"
        }
    )
    print("Email envoyé avec succès (vérifiez vos spams)")

if __name__ == "__main__":
    asyncio.run(test_email())