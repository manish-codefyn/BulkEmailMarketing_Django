from django.db import models
from django.utils import timezone
# Create your models here.
import uuid
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class SubscriberList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Subscriber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    lists = models.ManyToManyField(SubscriberList, related_name='subscribers')

    def __str__(self):
        return self.email

    def clean(self):
        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError({'email': 'Please enter a valid email address'})

    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()