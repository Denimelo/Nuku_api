import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from dotenv import load_dotenv
load_dotenv()

# 📁 Configuration unique de l'environnement Jinja2
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

# Ajouter le filtre strftime pour les dates
env.filters['strftime'] = lambda dt, fmt: dt.strftime(fmt) if dt else ""

# 💌 Fonction d'envoi d'e-mail améliorée
def send_email(to_email: str, subject: str, html_content: str):
    """Envoie un email HTML via SMTP"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_email

        mime_text = MIMEText(html_content, "html", "utf-8")
        msg.attach(mime_text)

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            print(f"✅ Email envoyé à {to_email}")
            return True
    except Exception as e:
        print(f"❌ Échec de l'envoi à {to_email} : {str(e)}")
        return False

# 🎨 Fonction de rendu des templates
def render_template(template_name: str, **context):
    """Rend un template Jinja2 avec le contexte fourni"""
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        print(f"❌ Erreur de rendu du template {template_name}: {str(e)}")
        return None

# ------------------ TEMPLATES D'EMAIL ------------------

# 📧 Activation de compte
def send_account_activation_email(to_email: str, full_name: str, token: str):
    """Envoie un email d'activation de compte"""
    link = f"{settings.FRONTEND_URL}/activate?token={token}"
    subject = "Activez votre compte NUKU"
    html = render_template("activation_email.html", 
                          full_name=full_name, 
                          link=link,
                          frontend_url=settings.FRONTEND_URL)
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Réinitialisation de mot de passe
def send_password_reset_email(to_email: str, full_name: str, temp_password: str):
    """Envoie un email de réinitialisation de mot de passe"""
    subject = "Réinitialisation de votre mot de passe NUKU"
    html = render_template("password_reset.html", 
                          full_name=full_name, 
                          temp_password=temp_password,
                          frontend_url=settings.FRONTEND_URL)
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Bienvenue expert
def send_expert_welcome_email(to_email: str, full_name: str, temp_password: str):
    """Envoie un email de bienvenue aux experts"""
    subject = "Bienvenue dans l'équipe NUKU - Votre compte expert est prêt"
    html = render_template("expert_welcome.html", 
                          full_name=full_name, 
                          temp_password=temp_password,
                          frontend_url=settings.FRONTEND_URL)
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Confirmation d'inscription entrepreneur
def send_entrepreneur_registration_confirmation(to_email: str, full_name: str, company_name: str):
    """Envoie une confirmation d'inscription aux entrepreneurs"""
    subject = "Inscription reçue - Examen en cours (NUKU)"
    html = render_template(
        "entrepreneur_registration_confirmation.html", 
        full_name=full_name,
        company_name=company_name,
        frontend_url=settings.FRONTEND_URL,
        admin_email=settings.DEFAULT_ADMIN_EMAIL
    )
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Validation entrepreneur - APPROUVÉ
def send_entrepreneur_validation_email(to_email: str, full_name: str):
    """Envoie un email de validation positive aux entrepreneurs"""
    subject = "🎉 Votre candidature NUKU a été acceptée !"
    html = render_template("entrepreneur_approved.html", 
                          full_name=full_name,
                          frontend_url=settings.FRONTEND_URL)
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Rejet entrepreneur
def send_entrepreneur_rejection_email(to_email: str, full_name: str, reason: str = None):
    """Envoie un email de rejet aux entrepreneurs"""
    subject = "Candidature NUKU - Décision concernant votre dossier"
    html = render_template("entrepreneur_rejected.html", 
                          full_name=full_name,
                          reason=reason,
                          frontend_url=settings.FRONTEND_URL,
                          admin_email=settings.DEFAULT_ADMIN_EMAIL)
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Notification admin pour nouvelle candidature
def send_admin_entrepreneur_notification_email(entrepreneur, user):
    """Notifie l'admin d'une nouvelle candidature entrepreneur"""
    subject = f"📋 Nouvelle candidature entrepreneur : {user.first_name} {user.last_name}"
    html = render_template(
        "admin_notification.html",
        user=user,
        entrepreneur=entrepreneur,
        admin_url=settings.ADMIN_URL
    )
    if html:
        return send_email(settings.DEFAULT_ADMIN_EMAIL, subject, html)
    return False

# 📧 Envoi de code OTP
def send_otp_email(to_email: str, full_name: str, otp_code: str, otp_type: str):
    """Envoie un code OTP par email"""
    
    # Définir le sujet selon le type
    subjects = {
        "email_verification": "🔐 Code de vérification - Activation de compte NUKU",
        "password_reset": "🔑 Code de vérification - Réinitialisation mot de passe NUKU", 
        "login_verification": "🔒 Code de vérification - Connexion NUKU"
    }
    
    # Messages personnalisés selon le type
    messages = {
        "email_verification": "pour activer votre compte NUKU",
        "password_reset": "pour réinitialiser votre mot de passe", 
        "login_verification": "pour vous connecter à NUKU"
    }
    
    subject = subjects.get(otp_type, "Code de vérification NUKU")
    action_message = messages.get(otp_type, "pour votre demande")
    
    html = render_template(
        "otp_email.html", 
        full_name=full_name, 
        otp_code=otp_code,
        expiry_minutes=settings.OTP_EXPIRY_MINUTES,
        action_message=action_message,
        frontend_url=settings.FRONTEND_URL
    )
    
    if html:
        return send_email(to_email, subject, html)
    return False

# ------------------ NOUVEAUX EMAILS ------------------

# 📧 Email de rappel de session
def send_session_reminder_email(to_email: str, full_name: str, session_title: str, session_date: str, session_url: str):
    """Envoie un rappel de session/appel"""
    subject = f"🔔 Rappel : Session {session_title} dans 1 heure"
    html = render_template(
        "session_reminder.html",
        full_name=full_name,
        session_title=session_title,
        session_date=session_date,
        session_url=session_url,
        frontend_url=settings.FRONTEND_URL
    )
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Nouveau message reçu
def send_new_message_notification_email(to_email: str, full_name: str, sender_name: str, message_preview: str):
    """Notifie un nouveau message privé"""
    subject = f"💌 Nouveau message de {sender_name} - NUKU"
    html = render_template(
        "new_message_notification.html",
        full_name=full_name,
        sender_name=sender_name,
        message_preview=message_preview[:150] + "..." if len(message_preview) > 150 else message_preview,
        frontend_url=settings.FRONTEND_URL
    )
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Notification d'attribution à un programme
def send_program_assignment_email(to_email: str, full_name: str, program_title: str, expert_name: str):
    """Notifie l'attribution à un nouveau programme"""
    subject = f"🎓 Vous êtes inscrit au programme : {program_title}"
    html = render_template(
        "program_assignment.html",
        full_name=full_name,
        program_title=program_title,
        expert_name=expert_name,
        frontend_url=settings.FRONTEND_URL
    )
    if html:
        return send_email(to_email, subject, html)
    return False

# 📧 Rapport hebdomadaire de progression
def send_weekly_progress_report_email(to_email: str, full_name: str, completed_modules: int, pending_assignments: int, next_session: str = None):
    """Envoie un rapport hebdomadaire de progression"""
    subject = "📊 Votre rapport hebdomadaire NUKU"
    html = render_template(
        "weekly_progress_report.html",
        full_name=full_name,
        completed_modules=completed_modules,
        pending_assignments=pending_assignments,
        next_session=next_session,
        frontend_url=settings.FRONTEND_URL
    )
    if html:
        return send_email(to_email, subject, html)
    return False