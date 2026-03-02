from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Serviço centralizado de envio de email.

    Estratégia:
    1) Se SENDGRID_API_KEY + SENDGRID_FROM estiverem configurados -> usa SendGrid
    2) Caso contrário -> tenta SMTP
    3) Nunca quebra fluxo de recuperação de senha (retorna True/False e loga erro)

    Observação:
    - body é enviado como plain text (suficiente para reset de senha)
    """

    config = current_app.config
    to_email = (to_email or "").strip()
    subject = (subject or "").strip()

    if not to_email or not subject:
        current_app.logger.warning("Email not sent: missing recipient or subject.")
        return False

    # -----------------------
    # SendGrid
    # -----------------------
    if config.get("SENDGRID_API_KEY") and config.get("SENDGRID_FROM"):
        try:
            message = Mail(
                from_email=Email(config["SENDGRID_FROM"]),
                to_emails=to_email,
                subject=subject,
                plain_text_content=body or "",
            )

            reply_to = config.get("SENDGRID_REPLY_TO")
            if reply_to:
                message.reply_to = Email(reply_to)

            if config.get("SENDGRID_SANDBOX_MODE"):
                message.mail_settings = {
                    "sandbox_mode": {"enable": True}
                }

            sg = SendGridAPIClient(config["SENDGRID_API_KEY"])
            sg.send(message)

            return True

        except Exception as e:
            current_app.logger.error(f"SendGrid error: {e}")


    # -----------------------
    # SMTP fallback
    # -----------------------
    if config.get("SMTP_HOST"):
        try:
            msg = EmailMessage()
            msg["From"] = config.get("SMTP_FROM") or config.get("SMTP_USERNAME") or ""
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body or "")

            with smtplib.SMTP(
                config["SMTP_HOST"],
                config.get("SMTP_PORT", 587)
            ) as server:

                if config.get("SMTP_USE_TLS", True):
                    server.starttls()

                if config.get("SMTP_USERNAME"):
                    server.login(
                        config["SMTP_USERNAME"],
                        config["SMTP_PASSWORD"]
                    )

                server.send_message(msg)

            return True

        except Exception as e:
            current_app.logger.error(f"SMTP error: {e}")
            return False

    current_app.logger.warning("Email not sent: no SENDGRID or SMTP configured.")
    return False
