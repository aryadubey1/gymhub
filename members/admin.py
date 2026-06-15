from django.contrib import admin
from .models import Plan, Member, Membership, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_days', 'price', 'is_active')
    list_filter = ('is_active',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'status', 'joined_at')
    search_fields = ('name', 'phone')
    list_filter = ('status',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    readonly_fields = ('end_date',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'method', 'date')
    list_filter = ('method',)
    search_fields = ('member__name',)
