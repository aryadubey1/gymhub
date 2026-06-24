from django.contrib import admin
from .models import Plan, Member, Membership, Payment


class TenantModelAdmin(admin.ModelAdmin):
    """
    Base admin class for all TenantModel subclasses.
    - Scopes querysets to the gym of the logged-in user.
    - Auto-assigns gym on save.
    """

    def get_queryset(self, request):
        qs = self.model.objects.unscoped()  # bypass TenantManager filter
        if not request.user.is_superuser:
            gym = getattr(request.user, 'gym', None)
            if gym:
                qs = qs.filter(gym=gym)
        return qs

    def save_model(self, request, obj, form, change):
        if obj.gym_id is None:
            gym = getattr(request.user, 'gym', None)
            if gym:
                obj.gym = gym
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Scope FK dropdowns (e.g. plan, member) to the current user's gym."""
        gym = getattr(request.user, 'gym', None)
        if gym:
            fk_model = db_field.related_model
            if hasattr(fk_model, 'gym'):  # only scope TenantModels
                kwargs['queryset'] = fk_model.objects.unscoped().filter(gym=gym)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Plan)
class PlanAdmin(TenantModelAdmin):
    list_display = ('name', 'duration_days', 'price', 'is_active')
    list_filter = ('is_active',)


@admin.register(Member)
class MemberAdmin(TenantModelAdmin):
    list_display = ('name', 'phone', 'status', 'joined_at')
    search_fields = ('name', 'phone')
    list_filter = ('status',)


@admin.register(Membership)
class MembershipAdmin(TenantModelAdmin):
    list_display = ('member', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    readonly_fields = ('end_date',)


@admin.register(Payment)
class PaymentAdmin(TenantModelAdmin):
    list_display = ('member', 'amount', 'method', 'date')
    list_filter = ('method',)
    search_fields = ('member__name',)