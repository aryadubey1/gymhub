from django.db import models
from django.conf import settings

from .middleware import get_current_gym

class Gym(models.Model):
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gym')
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        gym = get_current_gym()
        if gym is not None:
            qs = qs.filter(gym=gym)
        return qs

    def unscoped(self):
        return super().get_queryset()

    def all_gyms(self):
        """Explicit alias — use when you intentionally want all tenant rows."""
        return super().get_queryset()
    

class TenantModel(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name= '%(class)ss', null=True, blank=True)
    objects = TenantManager()

    class Meta:
        abstract = True
