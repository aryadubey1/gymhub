import json
from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from urllib.parse import quote
from .models import MessageTemplate, MessageLog
from members.models import Member


def _get_recipients(recipient_group):
    today = timezone.localdate()
    qs = Member.objects.filter(is_archived=False).prefetch_related('membership_set__plan')
    if recipient_group == 'active':
        return qs.filter(status='active')
    elif recipient_group == 'expiring_3':
        return qs.filter(
            status='active',
            membership__is_active=True,
            membership__end_date__range=[today, today + timezone.timedelta(days=3)]
        ).distinct()
    elif recipient_group == 'expiring_7':
        return qs.filter(
            status='active',
            membership__is_active=True,
            membership__end_date__range=[today, today + timezone.timedelta(days=7)]
        ).distinct()
    elif recipient_group == 'overdue':
        return qs.filter(status='expired')
    else:
        return qs


def _normalize_phone(phone):
    """Ensure phone is in E.164 format without + for wa.me links (e.g. 919876543210)."""
    if not phone:
        return ''
    phone = phone.strip().replace(' ', '').replace('-', '').lstrip('+')
    if phone.startswith('0'):
        phone = phone[1:]
    if not phone.startswith('91'):
        phone = '91' + phone
    return phone


@login_required
def bulk_message(request):
    templates = MessageTemplate.objects.filter(is_active=True)
    prepared_recipients = []
    recipients_data = []
    selected_template = None
    recipient_count = 0
    recipient_group = ''
    custom_message = ''

    if request.method == 'POST':
        template_id = request.POST.get('template')
        recipient_group = request.POST.get('recipient_group', '')
        custom_message = request.POST.get('custom_message', '')

        if template_id and recipient_group:
            selected_template = get_object_or_404(MessageTemplate, pk=template_id)
            members = _get_recipients(recipient_group)
            recipient_count = members.count()

            for member in members:
                try:
                    rendered = selected_template.render(
                        member,
                        extra_context={'announcement': custom_message}
                    )
                    phone = _normalize_phone(member.phone)
                    wa_link = f"https://wa.me/{phone}?text={quote(rendered)}" if phone else '#'
                    prepared_recipients.append({
                        'member': member,
                        'message': rendered,
                        'wa_link': wa_link,
                    })
                except Exception:
                    continue

                if not prepared_recipients:
                    messages.warning(request, 'No members found for the selected group.')

            # Safe JSON for JS — passed through json_script filter in template
            recipients_data = [{
                'memberId': item['member'].pk,
                'templateId': selected_template.pk,
                'waLink': item['wa_link'],
                'message': item['message'],
            } for item in prepared_recipients]

    context = {
        'templates': templates,
        'selected_template': selected_template,
        'prepared_recipients': prepared_recipients,
        'recipients_data': recipients_data,
        'recipient_count': recipient_count,
        'recipient_group': recipient_group,
        'custom_message': custom_message,
    }
    return render(request, 'messaging/bulk_message.html', context)


@login_required
@require_POST
def log_send(request):
    """AJAX endpoint — called by JS when a WhatsApp link is opened."""
    member = get_object_or_404(Member, pk=request.POST.get('member_id'))
    template = MessageTemplate.objects.filter(pk=request.POST.get('template_id')).first()
    MessageLog.objects.create(
        member=member,
        template=template,
        message=request.POST.get('message', '')
    )
    return JsonResponse({'status': 'ok'})


@login_required
def message_log(request):
    logs = MessageLog.objects.select_related('member', 'template').all()[:100]
    return render(request, 'messaging/message_log.html', {'logs': logs})