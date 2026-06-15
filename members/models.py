from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from decimal import Decimal


class Plan(models.Model):
    name = models.CharField(max_length=100)
    duration_days = models.IntegerField(help_text='30=monthly, 90=quarterly, 365=annual')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class Member(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'Phone must be exactly 10 digits')]
    )
    address = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='members/%Y/%m/', blank=True)
    joined_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def active_membership(self):
        return self.membership_set.filter(is_active=True).first()

    @property
    def days_until_expiry(self):
        membership = self.active_membership
        if membership:
            today = timezone.localdate()
            if membership.end_date >= today:
                return (membership.end_date - today).days
        return None

    @property
    def is_birthday_today(self):
        if self.dob:
            today = timezone.localdate()
            return self.dob.month == today.month and self.dob.day == today.day
        return False


class Membership(models.Model):
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.name} - {self.plan.name}"

    def save(self, *args, **kwargs):
        from datetime import timedelta
        # Auto-calculate end_date
        if not self.end_date and self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        
        # Deactivate previous memberships for this member when creating a new active one
        if self.is_active:
            Membership.objects.filter(
                member=self.member,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"₹{self.amount} - {self.member.name}"
