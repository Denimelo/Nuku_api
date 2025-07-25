import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from dotenv import load_dotenv
load_dotenv()

# Configurez l'environnement Jinja2 avec le filtre personnalisé
def setup_jinja_env():
    env = Environment(
        loader=FileSystemLoader("app/utils/email_templates"),
        autoescape=select_autoescape(['html', 'xml'])
    )
    # Ajoutez le filtre strftime
    env.filters['strftime'] = lambda dt, fmt: dt.strftime(fmt)
    return env

env = setup_jinja_env()


# 📁 Chargement des templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

# 💌 Fonction d'envoi d'e-mail
def send_email(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to_email

    mime_text = MIMEText(html_content, "html")
    msg.attach(mime_text)

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            print(f"✅ Email envoyé à {to_email}")
    except Exception as e:
        print(f"❌ Échec de l'envoi à {to_email} : {str(e)}")


# ------------------ TEMPLATES ------------------

def render_template(template_name: str, **context):
    template = env.get_template(template_name)
    return template.render(**context)


# 📧 Activation de compte
def send_account_activation_email(to_email: str, full_name: str, token: str):
    link = f"{settings.FRONTEND_URL}/activate?token={token}"
    subject = "Activez votre compte NUKU"
    html = render_template("activation_email.html", full_name=full_name, link=link)
    send_email(to_email, subject, html)

# Sauvegardez le template HTML ci-dessus dans un fichier nommé "password_reset.html"
# dans votre dossier de templates

# 📧 Réinitialisation de mot de passe
def send_password_reset_email(to_email: str, full_name: str, temp_password: str):
    subject = "Réinitialisation de votre mot de passe NUKU"
    html = render_template("password_reset.html", full_name=full_name, temp_password=temp_password)
    send_email(to_email, subject, html)


# 📧 Bienvenue expert
def send_expert_welcome_email(to_email: str, full_name: str, temp_password: str):
    subject = "Votre compte NUKU est prêt"
    html = render_template("expert_welcome.html", full_name=full_name, temp_password=temp_password)
    send_email(to_email, subject, html)

# 📧 Confirmation d'inscription entrepreneur
def send_entrepreneur_registration_confirmation(to_email: str, full_name: str, company_name: str):
    subject = "Inscription reçue - Examen en cours (NUKU)"
    html = render_template(
        "entrepreneur_registration_confirmation.html", 
        full_name=full_name,
        company_name=company_name,
        frontend_url=settings.FRONTEND_URL,
        admin_email=settings.DEFAULT_ADMIN_EMAIL
    )
    send_email(to_email, subject, html)

# 📧 Validation entrepreneur
def send_entrepreneur_validation_email(to_email: str, full_name: str):
    subject = "Votre candidature NUKU a été validée"
    html = render_template("entrepreneur_approved.html", full_name=full_name)
    send_email(to_email, subject, html)


# 📧 Rejet entrepreneur
def send_entrepreneur_rejection_email(to_email: str, full_name: str):
    subject = "Candidature refusée - NUKU"
    html = render_template("entrepreneur_rejected.html", full_name=full_name)
    send_email(to_email, subject, html)


# 📧 Notification admin pour nouvelle candidature
def send_admin_entrepreneur_notification_email(entrepreneur, user):
    subject = "Nouvelle candidature entrepreneur – NUKU"
    html = render_template(
        "admin_notification.html",
        user=user,
        entrepreneur=entrepreneur
    )
    send_email(settings.DEFAULT_ADMIN_EMAIL, subject, html)

# 📧 Envoi de code OTP
def send_otp_email(to_email: str, full_name: str, otp_code: str, otp_type: str):
    """Envoyer un code OTP par email"""
    
    # Définir le sujet selon le type
    subjects = {
        "email_verification": "Code de vérification - Activation de compte NUKU",
        "password_reset": "Code de vérification - Réinitialisation mot de passe NUKU", 
        "login_verification": "Code de vérification - Connexion NUKU"
    }
    
    subject = subjects.get(otp_type, "Code de vérification NUKU")
    
    html = render_template(
        "otp_email.html", 
        full_name=full_name, 
        otp_code=otp_code,
        expiry_minutes=settings.OTP_EXPIRY_MINUTES
    )
    
    send_email(to_email, subject, html)