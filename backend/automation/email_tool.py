from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger
import os
import smtplib
from email.message import EmailMessage


class EmailSendTool(BaseTool):
    name = "email.send"
    description = "Send an email to a recipient"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, recipient: str, subject: str = "", body: str = ""):
        """Send an email using SMTP with comprehensive error handling.

        Expects the following environment variables to be set if using real SMTP:
        - SMTP_HOST
        - SMTP_PORT
        - SMTP_USER
        - SMTP_PASSWORD

        If those are not set, the tool will return an error explaining what's needed.
        """
        
        def _send():
            # Validate recipient
            if not recipient or not recipient.strip():
                raise ValueError("Recipient email cannot be empty")
            
            # Basic email validation
            if '@' not in recipient:
                raise ValueError("Invalid email address format")
            
            # Get SMTP configuration
            smtp_host = os.environ.get("SMTP_HOST")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER")
            smtp_password = os.environ.get("SMTP_PASSWORD")

            if not smtp_host or not smtp_user or not smtp_password:
                logger.warning("SMTP configuration missing")
                raise AutomationError(
                    "SMTP configuration missing (SMTP_HOST/SMTP_USER/SMTP_PASSWORD)",
                    "📧 Email is not configured yet.\n\n" +
                    "To send emails, please set these environment variables:\n" +
                    "• SMTP_HOST (e.g., smtp.gmail.com)\n" +
                    "• SMTP_PORT (e.g., 587)\n" +
                    "• SMTP_USER (your email address)\n" +
                    "• SMTP_PASSWORD (your app password)\n\n" +
                    "For Gmail, use an App Password: https://support.google.com/accounts/answer/185833",
                    {"config": "email settings"}
                )
            
            logger.info(f"Sending email to {recipient}")
            
            try:
                # Create message
                msg = EmailMessage()
                msg["From"] = smtp_user
                msg["To"] = recipient
                msg["Subject"] = subject or "(No Subject)"
                msg.set_content(body or "")

                # Send email
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)

                logger.info(f"Email sent successfully to {recipient}")
                
                return {
                    "status": "success",
                    "message": f"Email sent to {recipient}",
                    "data": {
                        "recipient": recipient,
                        "subject": subject,
                        "body_length": len(body)
                    }
                }
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Email authentication failed: {e}")
                raise AutomationError(
                    str(e),
                    "Email authentication failed. Please check your email credentials."
                )
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to send email. Please check your email server settings."
                )
            except Exception as e:
                logger.error(f"Email send error: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't send the email. Please check your internet connection and email settings."
                )
        
        return error_handler.wrap_automation(
            func=_send,
            operation_name="Send Email",
            context={"recipient": recipient, "config": "email settings"}
        )
