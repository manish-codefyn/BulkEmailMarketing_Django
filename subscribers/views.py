from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView,DetailView
from django.urls import reverse_lazy
from .models import SubscriberList, Subscriber
from .forms import SubscriberListForm, SubscriberForm,SubscriberImportForm
from django.core.signing import Signer, BadSignature
from django.shortcuts import get_object_or_404, redirect,render
from django.contrib import messages
from django.views.generic import TemplateView
from .models import Subscriber
import uuid
import pandas as pd
from django.http import HttpResponse
from django.core.signing import TimestampSigner, BadSignature
from urllib.parse import  unquote


class SubscriberImportView(TemplateView):
    template_name = "subscribers/import_subscribers.html"



def export_subscriber_lists(request):
    # Retrieve all subscribers
    subscribers = Subscriber.objects.all()

    # Prepare data to export
    data = []
    for subscriber in subscribers:
        lists = [list.name for list in subscriber.lists.all()]  # Get names of all lists the subscriber is part of
        
        data.append({
            'email': subscriber.email,
            'first_name': subscriber.first_name or 'Not provided',
            'last_name': subscriber.last_name or 'Not provided',
            'subscribed_at': subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S') if subscriber.subscribed_at else '',
            'unsubscribed_at': subscriber.unsubscribed_at.strftime('%Y-%m-%d %H:%M:%S') if subscriber.unsubscribed_at else '',
            'is_active': subscriber.is_active,
            'subscriber_lists': ', '.join(lists),  # Join the list names into a single string
        })

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    # Create an HTTP response to download the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=subscriber_lists_export.xlsx'

    # Use Pandas ExcelWriter to write the DataFrame to the response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response



def import_subscriber_lists(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']

        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file)

            # Iterate over each row in the DataFrame
            for index, row in df.iterrows():
                email = row.get('email')
                first_name = row.get('first_name', '')
                last_name = row.get('last_name', '')
                is_active = row.get('is_active', True)
                list_names = row.get('lists', '').split(',')  # Assuming lists are comma-separated in the file

                if email:
                    # Create or update the subscriber
                    subscriber, created = Subscriber.objects.get_or_create(email=email, defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': is_active
                    })

                    if not created:
                        # Update existing subscriber if needed
                        subscriber.first_name = first_name
                        subscriber.last_name = last_name
                        subscriber.is_active = is_active
                        subscriber.save()

                    # Process the subscriber's lists
                    for list_name in list_names:
                        list_name = list_name.strip()  # Clean up any spaces around the names
                        if list_name:
                            # Get or create the SubscriberList object
                            subscriber_list, created = SubscriberList.objects.get_or_create(name=list_name)

                            # Add the subscriber to the list
                            subscriber.lists.add(subscriber_list)

            messages.success(request, "Subscribers imported successfully.")
        except Exception as e:
            messages.error(request, f"Error importing subscribers: {str(e)}")

    return redirect('subscriber:subscriber_list')  # Redirect to the subscriber list page



def export_subscribers(request):
    # Query all subscribers
    subscribers = Subscriber.objects.all()

    # Prepare data for Excel
    data = []
    for subscriber in subscribers:
        data.append({
            'email': subscriber.email,
            'first_name': subscriber.first_name,
            'last_name': subscriber.last_name,
            'is_active': subscriber.is_active,
            'subscribed_at': subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S') if subscriber.subscribed_at else '',
            'unsubscribed_at': subscriber.unsubscribed_at.strftime('%Y-%m-%d %H:%M:%S') if subscriber.unsubscribed_at else '',
            'lists': ', '.join(list.name for list in subscriber.lists.all()),  # many-to-many field
        })

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create the HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=subscribers_export.xlsx'

    # Write Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response



def subscriber_import_view(request, list_id):
    subscriber_list = get_object_or_404(SubscriberList, id=list_id)

    if request.method == 'POST':
        form = SubscriberImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                # Read the Excel file using pandas
                df = pd.read_excel(excel_file)

                # Expecting columns: email, first_name, last_name
                required_columns = ['email', 'first_name', 'last_name']
                if not all(column in df.columns for column in required_columns):
                    messages.error(request, f'Excel must have columns: {", ".join(required_columns)}')
                    return redirect('subscriber:subscriber_import', list_id=subscriber_list.id)

                imported_count = 0

                for _, row in df.iterrows():
                    email = row['email']
                    first_name = row.get('first_name', '')
                    last_name = row.get('last_name', '')

                    subscriber, created = Subscriber.objects.get_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'is_active': True,
                        }
                    )
                    # Add to list if not already added
                    subscriber.lists.add(subscriber_list)
                    imported_count += 1

                messages.success(request, f"Successfully imported {imported_count} subscribers.")
                return redirect('subscriber:subscriberlist_list')

            except Exception as e:
                messages.error(request, f"Error processing file: {e}")

    else:
        form = SubscriberImportForm()

    return render(request, 'subscribers/subscriber_import.html', {
        'form': form,
        'subscriber_list': subscriber_list,
    })


class UnsubscribeView(TemplateView):
    template_name = 'subscribers/unsubscribe.html'

    def get(self, request, signed_email):
        try:
            # Debugging: Print the received value
            print(f"Received signed email: {signed_email}")
            
            decoded_email = unquote(signed_email)
            print(f"After unquote: {decoded_email}")
            
            email = TimestampSigner().unsign(decoded_email, max_age=60*60*24*7)  # 7 days
            print(f"Successfully unsigned email: {email}")
            
            subscriber = get_object_or_404(Subscriber, email=email)
            subscriber.unsubscribe()
            messages.success(request, f'{email} has been unsubscribed.')
        except BadSignature as e:
            print(f"BadSignature error: {str(e)}")
            messages.error(request, 'Invalid or expired unsubscribe link. Please contact support.')
        return redirect('core:home')
    

class SubscriberListView(LoginRequiredMixin, ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html'
    context_object_name = 'subscribers'


class SubscriberCreateView(LoginRequiredMixin, CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/subscriber_form.html'
    success_url = reverse_lazy('subscriber:subscriber_list')


class SubscriberUpdateView(LoginRequiredMixin, UpdateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/subscriber_form.html'
    success_url = reverse_lazy('subscriber:subscriber_list')


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    model = Subscriber
    template_name = 'subscribers/subscriber_confirm_delete.html'
    success_url = reverse_lazy('subscriber:subscriber_list')


from subscribers.models import SubscriberList

class SubscriberListListView(LoginRequiredMixin, ListView):
    model = SubscriberList
    template_name = 'subscribers/subscriberlist_list.html'
    context_object_name = 'lists'

    def get_queryset(self):
        return SubscriberList.objects.filter(is_active=True)


class SubscriberListCreateView(LoginRequiredMixin, CreateView):
    model = SubscriberList
    form_class = SubscriberListForm
    template_name = 'subscribers/subscriberlist_form.html'
    success_url = reverse_lazy('subscriber:subscriberlist_list')


class SubscriberListUpdateView(LoginRequiredMixin, UpdateView):
    model = SubscriberList
    form_class = SubscriberListForm
    template_name = 'subscribers/subscriberlist_form.html'
    success_url = reverse_lazy('subscriber:subscriberlist_list')


class SubscriberListDetailView(LoginRequiredMixin, DetailView):
    model = SubscriberList
    template_name = 'subscribers/subscriberlist_detail.html'


class SubscriberListDeleteView(LoginRequiredMixin, DeleteView):
    model = SubscriberList
    template_name = 'subscribers/subscriberlist_confirm_delete.html'
    success_url = reverse_lazy('subscriber:subscriberlist_list')