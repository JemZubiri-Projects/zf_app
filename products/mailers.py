import json
from django.core.mail import EmailMessage
from django.conf import settings


def send_sales_quote_created_email(transaction):
    """
    Sends a finance notification email with quote.json attached.
    """

    customer = transaction.customer

    # ---------- Subject ----------
    subject = f"{transaction.id}:{transaction.iteration}:{transaction.request_type}:{customer.name}"

    # ---------- Body ----------
    body = "Please find the attached quote and product details."

    # ---------- Build email ----------
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.FINANCE_EMAIL],
    )

    # ---------- Attach JSON ----------
    json_content = json.dumps(
        transaction.json_file or {},
        indent=2,
        ensure_ascii=False
    )

    email.attach(
        filename="quote.json",
        content=json_content,
        mimetype="application/json",
    )

    # ---------- Send ----------
    email.send(fail_silently=False)
