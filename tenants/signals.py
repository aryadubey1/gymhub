from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Gym


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_gym_for_new_user(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        instance.gym
        return  
    except instance.__class__.gym.RelatedObjectDoesNotExist:
        pass  

    base_slug = slugify(instance.username) or 'gym'
    slug = base_slug
    counter = 1
    while Gym.objects.filter(slug=slug).exists():
        counter += 1
        slug = f'{base_slug}-{counter}'

    Gym.objects.create(
        name=f"{instance.username}'s Gym",
        owner=instance,
        slug=slug,
    )