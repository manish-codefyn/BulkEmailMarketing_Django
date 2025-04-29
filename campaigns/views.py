from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Campaign, EmailTemplate, Plugin,CampaignAnalytics
from .forms import CampaignForm, EmailTemplateForm, PluginForm
import logging
from django.utils import timezone
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)

from django.db.models import Count, Q
import time
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from datetime import datetime


@xframe_options_exempt
def track_open(request, campaign_id, subscriber_id):
    CampaignAnalytics.objects.create(
        campaign_id=campaign_id,
        subscriber_id=subscriber_id,
        event_type='opened',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    # Return transparent 1x1 pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return HttpResponse(pixel, content_type='image/gif')

def track_click(request, campaign_id, subscriber_id, url):
    CampaignAnalytics.objects.create(
        campaign_id=campaign_id,
        subscriber_id=subscriber_id,
        event_type='clicked',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        clicked_url=url
    )
    return HttpResponseRedirect(url)

class CampaignAnalyticsView(LoginRequiredMixin, DetailView):
    model = Campaign
    template_name = 'campaigns/campaign_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.object
        
        # Basic counts
        total_sent = campaign.analytics.filter(event_type='sent').count()
        total_subscribers = campaign.subscribers.count()
        
        # Engagement metrics
        opened_count = campaign.analytics.filter(event_type='opened').count()
        clicked_count = campaign.analytics.filter(event_type='clicked').count()
        
        # Calculate rates
        open_rate = (opened_count / total_sent * 100) if total_sent else 0
        click_rate = (clicked_count / total_sent * 100) if total_sent else 0
        ctr = (clicked_count / opened_count * 100) if opened_count else 0
        
        # Timeline data (last 7 days)
        timeline_data = []
        for i in range(7):
            date = timezone.now() - timedelta(days=6-i)
            day_data = {
                'date': date.date(),
                'sent': campaign.analytics.filter(
                    event_type='sent',
                    event_time__date=date.date()
                ).count(),
                'opened': campaign.analytics.filter(
                    event_type='opened',
                    event_time__date=date.date()
                ).count(),
                'clicked': campaign.analytics.filter(
                    event_type='clicked',
                    event_time__date=date.date()
                ).count()
            }
            timeline_data.append(day_data)
        
        # Top links clicked
        top_links = campaign.analytics.filter(
            event_type='clicked'
        ).exclude(
            clicked_url__isnull=True
        ).values(
            'clicked_url'
        ).annotate(
            clicks=Count('id')
        ).order_by('-clicks')[:5]
        
        context.update({
            'total_sent': total_sent,
            'total_subscribers': total_subscribers,
            'opened_count': opened_count,
            'clicked_count': clicked_count,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
            'ctr': round(ctr, 1),
            'bounce_count': campaign.analytics.filter(event_type='bounced').count(),
            'unsubscribe_count': campaign.analytics.filter(event_type='unsubscribed').count(),
            'timeline_data': timeline_data,
            'top_links': top_links,
            'devices': self.get_device_breakdown(campaign),
            'locations': self.get_location_data(campaign)
        })
        return context
    
    def get_device_breakdown(self, campaign):
        return campaign.analytics.filter(
            event_type='opened'
        ).exclude(
            user_agent__isnull=True
        ).values(
            'user_agent'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    
    def get_location_data(self, campaign):
        return campaign.analytics.filter(
            event_type='opened'
        ).exclude(
            ip_address__isnull=True
        ).values(
            'ip_address'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]

# ======================
# Campaign Views
# ======================
class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'campaigns/campaign_list.html'
    context_object_name = 'campaigns'

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user)


class CampaignCreateView(LoginRequiredMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'campaigns/campaign_form.html'
    success_url = reverse_lazy('campaign:campaign_list')

    def form_valid(self, form):
        try:
            form.instance.owner = self.request.user

            if form.instance.template and not form.instance.content:
                form.instance.content = form.instance.template.content or ''

            response = super().form_valid(form)
            messages.success(
                self.request,
                f"Campaign '{self.object.name}' was created successfully!",
                extra_tags='alert-success'
            )
            return response

        except Exception as e:
            # Log the exception
            logger.exception(f"Error occurred while creating campaign: {e}")

            # Optionally show a user-friendly message
            messages.error(
                self.request,
                "An error occurred while creating the campaign. Please try again later.",
                extra_tags='alert-danger'
            )

            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            "Please correct the errors below.",
            extra_tags='alert-danger'
        )
        return super().form_invalid(form)



class CampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'campaigns/campaign_form.html'
    success_url = reverse_lazy('campaign:campaign_list')


class CampaignDetailView(LoginRequiredMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'campaigns/campaign_detail.html'
    success_url = reverse_lazy('campaign:campaign_list')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Corrected line
        context['subscriber_count'] = self.object.list.subscribers.count()
        return context
    
# class CampaignDetailView(LoginRequiredMixin, DetailView):
#     model = Campaign
#     template_name = 'campaigns/campaign_detail.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Corrected line
#         context['subscriber_count'] = self.object.list.subscribers.count()
#         return context


class CampaignDeleteView(LoginRequiredMixin, DeleteView):
    model = Campaign
    template_name = 'campaigns/campaign_confirm_delete.html'
    success_url = reverse_lazy('campaign:campaign_list')

# ======================
# Email Sending Views
# ======================
@require_POST
def send_test_email(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)
    email = request.POST.get('email', request.user.email)
    
    try:
        campaign.send_test_email(email)
        messages.success(request, f'Test email sent to {email}')
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        messages.error(request, f'Failed to send test email: {str(e)}')
    
    return redirect('campaign:campaign_detail', pk=pk)


@require_POST
def send_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)

    try:
        if campaign.send_campaign():
            recipient_count = campaign.get_recipient_count() or 1
            sent_count = campaign.sent_count or 0

            # You can set a success message if you want
            messages.success(request, 'Campaign started successfully.')

            # Redirect to the new Analysis Dashboard view
            return redirect('campaign:campaign_analysis', pk=campaign.pk)

        messages.warning(request, 'Campaign already sent or no active subscribers.')

    except Exception as e:
        logger.error(f"Failed to send campaign {pk}: {e}")
        messages.error(request, f'Failed to start campaign: {e}')

    return redirect('campaign:campaign_detail', pk=pk)


@login_required
def campaign_analysis(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)

    recipient_count = campaign.get_recipient_count() or 1
    sent_count = campaign.sent_count or 0

    progress_data = campaign.get_progress_data()
    progress_data['recent_activity'] = [
              {
                'message': 'Batch processed',
                'timestamp': timezone.now().strftime('%H:%M:%S')
            } ]
    return render(request, 'campaigns/campaign_progress.html', progress_data )



@require_POST
def send_campaign_live(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)
    
    if campaign.status == 'sending':
        messages.info(request, 'Campaign is already being sent')
        return redirect('campaign_detail', pk=pk)
    
    try:
        if campaign._send_live():  # <<< Call send_live() here!
            messages.success(request, 'Campaign sent successfully!')
        else:
            messages.warning(request, 'No active subscribers to send to or sending failed.')
    except Exception as e:
        messages.error(request, f'Failed to send campaign: {str(e)}')
    
    messages.success(request, 'Campaign started successfully.')

        # Redirect to the new Analysis Dashboard view
    return redirect('campaign:campaign_analysis', pk=campaign.pk)



@login_required
def campaign_monitor(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)
    
    total_recipients = campaign.get_recipient_count()
    queued = max(0, total_recipients - campaign.sent_count - campaign.error_count)
    
    monitor_data = {
        'status': campaign.status,
        'sent_emails': campaign.sent_count,
        'queued_emails': queued,
        'failed_emails': campaign.error_count,
        **campaign.get_rates(),  # Include all rates
        'total_recipients': total_recipients,
        'time_remaining': campaign.calculate_time_remaining(),
        'last_updated': timezone.now().isoformat()
    }

    return JsonResponse(monitor_data)


@login_required
def campaign_progress(request, pk):
    """
    View to return campaign progress data as JSON
    """
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)
    
    try:
        # Get the progress data using the model method
        progress_data = campaign.get_progress_data()
        
        # Add recent activity (you'll need to implement this in your model)
        progress_data['recent_activity'] = [
            {
                'message': 'Batch processed',
                'timestamp': timezone.now().strftime('%H:%M:%S')
            }
        ]
        
        return JsonResponse(progress_data)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)

def check_campaign_status(request, pk):
    # Get the campaign object
    campaign = get_object_or_404(Campaign, pk=pk)

    # If the campaign doesn't have a task_id, return an error
    if not campaign.task_id:
        return JsonResponse({'error': 'No task found for this campaign'}, status=400)

    # Get the Celery AsyncResult using the campaign's task_id
    task = AsyncResult(campaign.task_id)

    # Get the task progress details
    progress = task.info if isinstance(task.info, dict) else {}
    current = progress.get('current', 0)
    total = progress.get('total', 1) or 1  # avoid division by zero
    success = progress.get('success', 0)
    failed = progress.get('failed', 0)

    percent = int((current / total) * 100)  # Progress percentage

    response = {
        'status': task.status,  # Task status (e.g., PENDING, STARTED, SUCCESS, etc.)
        'progress': {
            'current': current,
            'total': total,
            'success': success,
            'failed': failed,
        },
        'percent': percent,
        'ready': task.ready(),  # True if the task has finished
    }

    if task.failed():
        response['error'] = str(task.result) if task.result else 'Unknown error occurred.'

    return JsonResponse(response)

# ======================
# Email Template Views
# ======================

class EmailTemplateGalleryView(ListView):
    model = EmailTemplate
    template_name = 'campaigns/email_template_gallery.html'
    context_object_name = 'templates'
    queryset = EmailTemplate.objects.filter(is_active=True).order_by('-created_at')


class EmailTemplatePreviewView(UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'campaigns/emailtemplate_form.html'
    context_object_name = 'template'
    success_url = reverse_lazy('campaign:emailtemplate_list')



class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'campaigns/emailtemplate_form.html'
    success_url = reverse_lazy('campaign:emailtemplate_list')

class EmailTemplateListView(LoginRequiredMixin, ListView):
    model = EmailTemplate
    template_name = 'campaigns/emailtemplate_list.html'
    context_object_name = 'templates'


class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'campaigns/emailtemplate_form.html'
    success_url = reverse_lazy('campaign:emailtemplate_list')


class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailTemplate
    template_name = 'campaigns/emailtemplate_confirm_delete.html'
    success_url = reverse_lazy('campaign:emailtemplate_list')

# ======================
# Plugin Views
# ======================
class PluginListView(LoginRequiredMixin, ListView):
    model = Plugin
    template_name = 'campaigns/plugin_list.html'
    context_object_name = 'plugins'

class PluginCreateView(LoginRequiredMixin, CreateView):
    model = Plugin
    form_class = PluginForm
    template_name = 'campaigns/plugin_form.html'
    success_url = reverse_lazy('campaign:plugin_list')

    def form_valid(self, form):
        messages.success(self.request, "Plugin created successfully.")
        return super().form_valid(form)

class PluginUpdateView(LoginRequiredMixin, UpdateView):
    model = Plugin
    form_class = PluginForm  # use same form for consistency
    template_name = 'campaigns/plugin_form.html'
    success_url = reverse_lazy('campaign:plugin_list')

    def form_valid(self, form):
        messages.success(self.request, "Plugin updated successfully.")
        return super().form_valid(form)

class PluginDeleteView(LoginRequiredMixin, DeleteView):
    model = Plugin
    template_name = 'campaigns/plugin_confirm_delete.html'
    success_url = reverse_lazy('campaign:plugin_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Plugin deleted successfully.")
        return super().delete(request, *args, **kwargs)