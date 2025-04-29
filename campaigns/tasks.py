from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import get_connection
from .models import Campaign
from subscribers.models import Subscriber
from django.utils import timezone
logger = get_task_logger(__name__)
from django.db import transaction
from django.conf import settings


@shared_task(bind=True, acks_late=True)
def send_bulk_emails(self, campaign_id, subscriber_ids):
    from django.db import connection

    try:
        connection.close()

        campaign = Campaign.objects.get(id=campaign_id)
        campaign.task_id = self.request.id
        campaign.status = 'sending'
        campaign.save()

        logger.info(f"[{campaign_id}] Start sending emails")

        batch_size = settings.EMAIL_BATCH_SIZE
        sent_count = 0
        error_count = 0

        for i in range(0, len(subscriber_ids), batch_size):
            batch_ids = subscriber_ids[i:i + batch_size]
            logger.info(f"[{campaign_id}] Processing batch {i//batch_size + 1} with {len(batch_ids)} IDs")

            try:
                with transaction.atomic():
                    campaign._process_batch(batch_ids)
                    sent_count += len(batch_ids)

                    campaign.sent_count = sent_count
                    campaign.error_count = error_count
                    campaign.save(update_fields=['sent_count', 'error_count'])

                    logger.debug(f"[{campaign_id}] Batch {i//batch_size + 1} success")

            except Exception as e:
                error_count += len(batch_ids)
                logger.error(f"[{campaign_id}] Batch {i//batch_size + 1} failed: {str(e)}", exc_info=True)
                connection.close()

            self.update_state(
                state='PROGRESS',
                meta={'sent': sent_count, 'errors': error_count}
            )

        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()

        logger.info(f"[{campaign_id}] Email sending completed successfully")
        return {'sent': sent_count, 'errors': error_count}

    except Exception as e:
        logger.critical(f"[{campaign_id}] Failed completely: {str(e)}", exc_info=True)
        if 'campaign' in locals():
            campaign.status = 'failed'
            campaign.save(update_fields=['status'])
        raise self.retry(exc=e, countdown=60)
