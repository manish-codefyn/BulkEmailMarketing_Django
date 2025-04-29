from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_order_confirmation_email(order, context):
    """
    Send order confirmation email to customer
    """
    if not order.user or not order.user.email:
        return False
    
    try:
        subject = f"Order Confirmation - #{order.orders_id}"
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [order.user.email]

        send_mail(
            subject,
            plain_message,
            from_email,
            recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        # You might want to log this error
        print(f"Failed to send confirmation email: {e}")
        return False