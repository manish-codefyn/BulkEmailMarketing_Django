

from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView,UpdateView,CreateView,View,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from campaigns.models import Campaign
from subscribers.models import Subscriber, SubscriberList
from .models import SiteSetting, SMTPSetting,SiteLegal
from .forms import SiteSettingForm, SMTPSettingForm,SiteLegalForm
import smtplib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages

class SiteLegalUpdateView(LoginRequiredMixin,UpdateView):
    form_class = SiteLegalForm
    template_name = 'core/sitelegal_form.html'
    success_url = reverse_lazy('core:site_legal_detail')


    def get_object(self):
        return SiteLegal.objects.first() or SiteLegal.objects.create()
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Legal content updated successfully!")
        return super().form_valid(form)


class SiteLegalDetailView(DetailView):
    model = SiteLegal
    template_name = 'core/sitelegal_detail.html'
    context_object_name = 'legal_content'

    def get_object(self, queryset=None):
        """Get the single SiteLegal instance or return 404"""
        obj = SiteLegal.objects.first()
        if not obj:
            # You might want to redirect to create view instead
            from django.http import Http404
            raise Http404("No legal content exists yet")
        return obj

class SiteLegalCreateView(LoginRequiredMixin, CreateView):
    model = SiteLegal
    form_class = SiteLegalForm
    template_name = 'core/sitelegal_form.html'
    success_url = reverse_lazy('core:site_legal_detail')  # Change to your detail view name

    def test_func(self):
        """Only allow staff users to create legal content"""
        return self.request.user.is_staff

    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Legal content created successfully!',
            extra_tags='alert-success'
        )
        return response

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            'Please correct the errors below.',
            extra_tags='alert-danger'
        )
        return super().form_invalid(form)


class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legal = SiteLegal.objects.first()
        context['privacy_policy'] = legal.privacy_policy if legal else ''
        return context

class TermsOfServiceView(TemplateView):
    template_name = 'core/terms_of_service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legal = SiteLegal.objects.first()
        context['terms_of_service'] = legal.terms_of_service if legal else ''
        return context

@csrf_exempt
def test_smtp_connection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get SMTP settings from request
            email_host = data.get('email_host')
            email_port = int(data.get('email_port', 587))
            email_use_tls = data.get('email_use_tls', True)
            email_host_user = data.get('email_host_user')
            email_host_password = data.get('email_host_password')
            
            # Test connection
            server = smtplib.SMTP(email_host, email_port, timeout=10)
            if email_use_tls:
                server.starttls()
            server.login(email_host_user, email_host_password)
            server.quit()
            
            return JsonResponse({
                'success': True,
                'message': 'SMTP connection successful!'
            })
        except smtplib.SMTPAuthenticationError as e:
            return JsonResponse({
                'success': False,
                'message': f'Authentication failed: {str(e)}'
            })
        except smtplib.SMTPException as e:
            return JsonResponse({
                'success': False,
                'message': f'SMTP error: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Connection error: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


class SiteSettingUpdateView(LoginRequiredMixin, UpdateView):
    model = SiteSetting
    form_class = SiteSettingForm
    template_name = 'core/site_setting_form.html'
    success_url = reverse_lazy('core:site_settings')
    
    def get_object(self):
        return SiteSetting.objects.first() or SiteSetting.objects.create()


class SMTPSettingUpdateView(LoginRequiredMixin, UpdateView):
    model = SMTPSetting
    form_class = SMTPSettingForm
    template_name = 'core/smtp_setting_form.html'
    success_url = reverse_lazy('core:smtp_settings')
    
    def get_object(self):
        return SMTPSetting.objects.first() or SMTPSetting.objects.create()


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Optimized queries with aggregation
            campaigns = Campaign.objects.filter(owner=self.request.user)
            context.update({
                'total_campaigns': campaigns.count(),
                'active_campaigns': campaigns.filter(is_active=True).count(),
                'sent_campaigns': campaigns.exclude(sent_at=None).count(),
                'total_subscribers': Subscriber.objects.count(),
                'active_subscribers': Subscriber.objects.filter(is_active=True).count(),
                'recent_subscribers': Subscriber.objects.order_by('-subscribed_at')[:5],
                'total_lists': SubscriberList.objects.count(),
                # Add engagement metrics
                'average_open_rate': self.get_average_open_rate(),
                'average_click_rate': self.get_average_click_rate()
            })
        return context
    
    def get_average_open_rate(self):
        """Calculate average open rate across all campaigns"""
        if not self.request.user.is_authenticated:
            return 0
        sent_count = Campaign.objects.filter(owner=self.request.user).exclude(sent_at=None).count()
        if sent_count == 0:
            return 0
        # Replace with your actual analytics model query
        return round((500 / sent_count) * 100, 1)  # Example calculation

    def get_average_click_rate(self):
        """Calculate average click rate across all campaigns"""
        if not self.request.user.is_authenticated:
            return 0
        sent_count = Campaign.objects.filter(owner=self.request.user).exclude(sent_at=None).count()
        if sent_count == 0:
            return 0
        # Replace with your actual analytics model query
        return round((150 / sent_count) * 100, 1)  # Example calculation


class DashboardView(LoginRequiredMixin, HomeView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'campaigns': Campaign.objects.filter(owner=self.request.user)
                              .order_by('-created_at')[:5],
            'top_performing_campaign': self.get_top_performing_campaign(),
            'subscriber_growth': self.get_subscriber_growth()
        })
        return context
    
    def get_top_performing_campaign(self):
        """Get the campaign with highest open rate"""
        # Replace with your actual analytics model query
        return Campaign.objects.filter(owner=self.request.user, sent_at__isnull=False)\
                       .order_by('-created_at').first()
    
    def get_subscriber_growth(self):
        """Calculate subscriber growth over last 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_month = now - timedelta(days=30)
        
        current_count = Subscriber.objects.count()
        previous_count = Subscriber.objects.filter(
            subscribed_at__lt=last_month
        ).count()
        
        if previous_count == 0:
            return 0
        
        return round(((current_count - previous_count) / previous_count) * 100, 1)

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)