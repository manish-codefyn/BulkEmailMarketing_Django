import re
from .models import Subscriber, EmailListSubscriber

def parse_subscriber_data(data):
    """
    Parse subscriber data from text input (one per line or comma-separated)
    Returns a list of dictionaries with email, first_name, last_name
    """
    subscribers = []
    
    # Split by lines first
    lines = re.split(r'[\n\r]+', data.strip())
    
    for line in lines:
        # Split by comma if present
        parts = [part.strip() for part in line.split(',') if part.strip()]
        
        if not parts:
            continue
            
        email = parts[0]
        first_name = parts[1] if len(parts) > 1 else ''
        last_name = parts[2] if len(parts) > 2 else ''
        
        subscribers.append({
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })
    
    return subscribers

def add_subscribers_to_list(email_list, subscribers):
    """
    Add multiple subscribers to an email list
    Returns tuple of (added_count, duplicate_count)
    """
    added = 0
    duplicates = 0
    
    for sub_data in subscribers:
        subscriber, created = Subscriber.objects.get_or_create(
            email=sub_data['email'],
            defaults={
                'first_name': sub_data.get('first_name', ''),
                'last_name': sub_data.get('last_name', '')
            }
        )
        
        if created:
            added += 1
        else:
            duplicates += 1
            
        EmailListSubscriber.objects.get_or_create(
            email_list=email_list,
            subscriber=subscriber
        )
    
    return (added, duplicates)