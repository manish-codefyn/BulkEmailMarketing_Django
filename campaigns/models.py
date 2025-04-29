import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()
from django.core.mail import EmailMultiAlternatives,get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading
import logging
import threading
from django.core.signing import Signer
from django.core.signing import TimestampSigner
from subscribers.models import Subscriber,SubscriberList
from django.template import TemplateDoesNotExist
logger = logging.getLogger(__name__)
from celery.result import AsyncResult
from django.utils import timezone
from django.core.mail import send_mail
import time
import math
from urllib.parse import quote
import base64
from django.core.signing import TimestampSigner

SENDING_STATUS = (
    ('pending', 'Pending'),
    ('sending', 'Sending'),
    ('sent', 'Sent'),
    ('failed', 'Failed')
)

from django_quill.fields import QuillField


class Campaign(models.Model):
    """
    Email campaign model with bulk sending capabilities
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    preview_text = models.TextField(help_text="Short text preview for email clients")
    content = QuillField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=SENDING_STATUS,
        default='pending'
    )
    sent_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    bounce_count = models.PositiveIntegerField(default=0)
    unsubscribe_count = models.PositiveIntegerField(default=0)
    template = models.ForeignKey(
        'EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text="Optional: Select a saved template to use for the email content."
    )
    list = models.ForeignKey(
        SubscriberList,   # or whatever model your lists are
        on_delete=models.CASCADE,
        related_name='campaigns'
    )


    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email Campaign"
        verbose_name_plural = "Email Campaigns"

    def __str__(self):
        return f"{self.name} ({self.subject})"

    def get_absolute_url(self):
        return reverse('campaign_detail', kwargs={'pk': self.pk})

    def _get_active_subscribers(self):
        """Return active subscribers from the list."""
        return self.list.subscribers.filter(is_active=True)

    def send_test_email(self, to_email):
        try:
     
            email = self._prepare_single_email(
                email=to_email,
                is_test=True
            )
            email.send()
            logger.info(f"Test email sent for campaign {self.id} to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Test email failed for campaign {self.id}: {str(e)}")
            raise

    def send_campaign(self):
        if self.sent_at:
            logger.warning(f"Campaign {self.id} already sent")
            return False

        active_subscribers = self._get_active_subscribers()
        if not active_subscribers.exists():
            logger.warning(f"No active subscribers for campaign {self.id}.")
            return False

        try:
            from .tasks import send_bulk_emails

            subscriber_ids = list(active_subscribers.values_list('id', flat=True))
            task = send_bulk_emails.delay(self.id, subscriber_ids)

            self.task_id = task.id
            self.sent_count = active_subscribers.count()
            self.status = 'sending'
            self.save()

            logger.info(f"Started sending campaign {self.id} with task {task.id}")
            return True

        except Exception as e:
            self.status = 'failed'
            self.save()
            logger.error(f"Failed to start sending: {str(e)}")
            return False

    def _send_live(self, batch_size=50):
        if self.sent_at:
            logger.warning(f"Campaign {self.id} already sent")
            return False

        active_subscribers = self._get_active_subscribers()
        if not active_subscribers.exists():
            logger.warning(f"No active subscribers for {self.id}")
            return False

        try:
            total = active_subscribers.count()
            sent_count = 0
            logger.info(f"Starting live send for campaign {self.id} to {total} subscribers.")

            subscriber_list = list(active_subscribers.values_list('id', flat=True))

            for i in range(0, total, batch_size):
                batch_ids = subscriber_list[i:i + batch_size]
                try:
                    self._process_batch(batch_ids)
                    sent_count += len(batch_ids)
                    logger.info(f"Batch {i // batch_size + 1} sent ({len(batch_ids)} emails).")
                except Exception as e:
                    logger.error(f"Batch {i // batch_size + 1} failed: {str(e)}")
                    continue

                time.sleep(2)

            self.status = 'sent'
            self.sent_at = timezone.now()
            self.sent_count = sent_count
            self.save()

            logger.info(f"Campaign {self.id} live send completed successfully. Total sent: {sent_count}")
            return True

        except Exception as e:
            self.status = 'failed'
            logger.error(f"Failed to send campaign live: {str(e)}")
            self.save()
            return False

    def _process_batch(self, subscriber_ids):
        try:
            logger.info(f"Processing batch of {len(subscriber_ids)} subscribers for campaign {self.id}")

            with get_connection() as connection:
                subscribers = self.list.subscribers.filter(
                    id__in=subscriber_ids,
                    is_active=True
                )

                if not subscribers.exists():
                    logger.warning(f"No active subscribers found in batch for {self.id}")
                    return

                for idx, subscriber in enumerate(subscribers, start=1):
                    email = self._prepare_single_email(
                        email=subscriber.email,
                        context={'subscriber': subscriber}
                    )
                    if email:
                        connection.send_messages([email])

                self.sent_count += subscribers.count()
                self.save(update_fields=['sent_count', 'updated_at'])

                logger.info(f"Batch complete: Sent {subscribers.count()} emails for campaign {self.id}")

        except Exception as e:
            logger.error(f"Error processing batch for campaign {self.id}: {str(e)}", exc_info=True)
            raise

    def _prepare_single_email(self, email, context=None, is_test=False):
        context = context or {}
        # Ensure Quill content is properly serialized
        content = self.content
        if hasattr(content, 'json'):  # If it's a FieldQuill object
            content = content.json
        
        context.update({
            'campaign': self,
           'campaign_content_html': self.content.html,
            'unsubscribe_url': self._get_unsubscribe_url(email),
            'is_test': is_test
        })
    
        subject = f"[TEST] {self.subject}" if is_test else self.subject
        html_content = render_to_string('campaigns/email_template.html', context)
        text_content = strip_tags(html_content)

        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            headers={
                'List-Unsubscribe': f'<{context["unsubscribe_url"]}>',
                'X-Campaign-ID': str(self.id),
                'Precedence': 'bulk'
            }
        )
        email_msg.attach_alternative(html_content, "text/html")
        return email_msg

    def _get_unsubscribe_url(self, email):
        signer = TimestampSigner()
        signed_email = signer.sign(email)
        
        # METHOD 1: Standard URL encoding (try this first)
        encoded_email = quote(signed_email)
        
        # METHOD 2: Base64 fallback (if above fails)
        # encoded_email = base64.urlsafe_b64encode(signed_email.encode()).decode()
        
        url = reverse('subscriber:unsubscribe', args=[encoded_email])
        return f"{settings.SITE_URL}{url}"
    
    def verify_email_backend(self):
        try:
            connection = get_connection(fail_silently=False)
            connection.open()
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Email backend verification failed: {str(e)}")
            return False

    def cancel_sending(self):
        self._sending_complete = True
        self.save()
        logger.warning(f"Campaign {self.id} sending cancelled")



    def get_recent_activity(self):
        return [
            {
                'message': f"Sent to {self.sent_count} of {self.get_recipient_count()} emails",
                'timestamp': timezone.now().strftime('%H:%M:%S')
            }
        ]

    def get_recipient_count(self):
        return self._get_active_subscribers().count()

    def get_sending_rate(self):
        if self.status != 'sending' or self.sent_count == 0:
            return None

        time_elapsed = (timezone.now() - self.updated_at).total_seconds() / 60
        if time_elapsed < 0.1:
            return None

        return self.sent_count / time_elapsed

    def get_progress_percentage(self):
        total = self.get_recipient_count()
        if total == 0:
            return 0

        sent = self.sent_count
        percentage = (sent / total) * 100

        if self.status == 'sent':
            return 100

        return min(99, int(percentage))
    

        
    def get_progress_data(self):
        """Safe method to get all progress data with proper error handling"""
        try:
            time_remaining = self.calculate_time_remaining()
            
            # Ensure time_remaining is always a string or None
            if time_remaining is None:
                time_remaining = "Not started"
            elif not isinstance(time_remaining, str):
                time_remaining = str(time_remaining)
                
            metrics = {
                'open_count': 'Open count',
                'click_count': 'Click count',
                'bounce_count': 'Bounce count',
                'unsubscribe_count': 'Unsubscribes'
            }

            return {
                'status': self.status,
                'progress_percentage': self.get_progress_percentage(),
                'sent_emails': self.sent_count,
                'total_emails': self.get_recipient_count(),
                'time_remaining': time_remaining,
                'recent_activity': self.get_recent_activity(),
                'timestamp': timezone.now().isoformat(),
                'sent_count': self.sent_count,  # Sent count
                'open_count': self.open_count,  # Open count
                'click_count': self.click_count,  # Click count
                'bounce_count': self.bounce_count,  # Bounce count
                'unsubscribe_count': self.unsubscribe_count,  # Unsubscribe count
                'metrics': metrics  # Pass the metrics dictionary to the template
            }
        except Exception as e:
            logger.error(f"Error in get_progress_data: {str(e)}")
            return {
                'status': 'error',
                'progress_percentage': 0,
                'sent_emails': 0,
                'total_emails': 0,
                'time_remaining': "Error calculating",
                'recent_activity': [],
                'timestamp': timezone.now().isoformat()
            }

    def calculate_time_remaining(self):
        """Accurate time remaining calculation"""
        if self.status != 'sending':
            return "Not currently sending" if self.status != 'sent' else "Completed"

        total = self.get_recipient_count()
        if total == 0:
            return "No recipients"

        sent = self.sent_count
        if sent == 0:
            return "Starting..."

        time_elapsed = (timezone.now() - self.updated_at).total_seconds()
        if time_elapsed < 5:  # Need at least 5 seconds of data
            return "Calculating..."

        sending_rate = sent / time_elapsed  # emails per second
        if sending_rate < 0.01:  # Minimum viable rate
            return "Processing..."

        remaining = total - sent
        seconds_left = remaining / sending_rate

        # Human-readable format
        if seconds_left < 60:
            return "Less than a minute"
        elif seconds_left < 3600:
            minutes = int(seconds_left / 60)
            return f"About {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            hours = round(seconds_left / 3600, 1)
            return f"About {hours} hour{'s' if hours > 1 else ''}"

    def save(self, *args, **kwargs):
        if self.template and not self.content:
            self.content = self.template.content
        super().save(*args, **kwargs)

    def get_rates(self):
        """Calculate all engagement rates"""
        total_sent = self.sent_count
        if total_sent == 0:
            return {
                'open_rate': 0,
                'click_rate': 0,
                'bounce_rate': 0,
                'unsubscribe_rate': 0
            }

        return {
            'open_rate': round((self.open_count / total_sent) * 100, 1),
            'click_rate': round((self.click_count / total_sent) * 100, 1),
            'bounce_rate': round((self.bounce_count / total_sent) * 100, 1),
            'unsubscribe_rate': round((self.unsubscribe_count / total_sent) * 100, 1)
        }

class ActivityLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='activity_logs')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class CampaignAnalytics(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='analytics')
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed')
    ])
    event_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    clicked_url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Campaign Analytics"
        indexes = [
            models.Index(fields=['campaign', 'event_type']),
            models.Index(fields=['subscriber', 'campaign']),
        ]

    def __str__(self):
        return f"{self.campaign} - {self.subscriber} - {self.event_type}"


class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    content =  QuillField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description =  QuillField()
    code = models.TextField(help_text="HTML/JS/CSS code for the plugin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name