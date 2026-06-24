from django.db import models

from tenants.models import TenantModel


class MessageTemplate(TenantModel):
    CATEGORY_CHOICES = [
        ('fees_due', 'Fees Due'),
        ('fees_paid', 'Fees Paid'),
        ('fees_overdue', 'Fees Overdue'),
        ('announcement', 'Announcement'),
    ]

    name = models.CharField(max_length=100)
    body = models.TextField(
        help_text='Available placeholders: {name}, {days}, {expiry_date}, {amount}, {plan}, {announcement}'
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def render(self, member, extra_context=None):
        context = {
            'name': member.name,
            'days': member.days_until_expiry or 0,
            'expiry_date': (
                member.active_membership.end_date.strftime('%d %b %Y')
                if member.active_membership else 'N/A'
            ),
            'amount': member.active_membership.plan.price if member.active_membership else 0,
            'plan': member.active_membership.plan.name if member.active_membership else 'N/A',
            'announcement': '',
        }
        if extra_context:
            context.update(extra_context)
        try:
            return self.body.format(**context)
        except (KeyError, ValueError):
            return self.body


class MessageLog(TenantModel):
    template = models.ForeignKey(
        MessageTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    member = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE, related_name='message_logs'
    )
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.member.name} — {self.sent_at.strftime('%d %b %Y %H:%M')}"