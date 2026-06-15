from django.utils import timezone


class AutoExpireMembersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = timezone.localdate()
        from .models import Member
        Member.objects.filter(
            status='active',
            membership__is_active=True,
            membership__end_date__lt=today
        ).update(status='expired')
        return self.get_response(request)