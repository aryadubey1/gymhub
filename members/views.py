from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.core.paginator import Paginator
from urllib.parse import quote
from .models import Member, Membership, Payment, Plan
from .forms import MemberForm, PaymentForm, MembershipForm, MemberWithMembershipForm, RenewWithPaymentForm
from messaging.models import MessageTemplate


@login_required
def dashboard(request):
    today = timezone.localdate()
    
    # Total active members
    total_active = Member.objects.filter(status='active', is_archived=False).count()
    
    # Members with active membership ending in 1-3 days
    expiring_1_3 = Member.objects.filter(
        status='active',
        is_archived=False,
        membership__is_active=True,
        membership__end_date__range=[today + timezone.timedelta(days=1), today + timezone.timedelta(days=3)]
    ).distinct().count()
    
    # Members with active membership ending in 4-7 days
    expiring_4_7 = Member.objects.filter(
        status='active',
        is_archived=False,
        membership__is_active=True,
        membership__end_date__range=[today + timezone.timedelta(days=4), today + timezone.timedelta(days=7)]
    ).distinct().count()
    
    # Members with active membership ending in 8-15 days
    expiring_8_15 = Member.objects.filter(
        status='active',
        is_archived=False,
        membership__is_active=True,
        membership__end_date__range=[today + timezone.timedelta(days=8), today + timezone.timedelta(days=15)]
    ).distinct().count()
    
    # Overdue members (status='expired' and no active membership)
    overdue = Member.objects.filter(
        status='expired',
        is_archived=False
    ).annotate(
        has_active=Count('membership', filter=Q(membership__is_active=True))
    ).filter(has_active=0).count()
    
    # Birthdays today
    birthdays_today = Member.objects.filter(
        dob__month=today.month,
        dob__day=today.day,
        is_archived=False
    ).count()
    
    context = {
        'total_active': total_active,
        'expiring_1_3': expiring_1_3,
        'expiring_4_7': expiring_4_7,
        'expiring_8_15': expiring_8_15,
        'overdue': overdue,
        'birthdays_today': birthdays_today,
    }
    return render(request, 'dashboard.html', context)


@login_required
def member_list(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    members = Member.objects.filter(is_archived=False).prefetch_related('membership_set__plan').order_by('-created_at')
    
    if status_filter:
        if status_filter == 'expiring':
            today = timezone.localdate()
            days = int(request.GET.get('days', 7))
            members = members.filter(
                membership__is_active=True,
                membership__end_date__range=[today, today + timezone.timedelta(days=days)]
            ).distinct()
        elif status_filter == 'birthday':
            today = timezone.localdate()
            members = members.filter(dob__month=today.month, dob__day=today.day)
        elif status_filter == 'expired':
            members = members.filter(status='expired')
        else:
            members = members.filter(status=status_filter)
    
    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) | Q(phone__icontains=search_query)
        )
    
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'filter_tabs': [
            ('All', ''),
            ('Active', 'active'),
            ('Expiring', 'expiring'),
            ('Expired', 'expired'),
            ('Paused', 'paused'),
            ('Birthdays', 'birthday'),
        ],
    }
    return render(request, 'members/member_list.html', context)


@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member.objects.prefetch_related('membership_set__plan'), pk=pk)
    payments = Payment.objects.filter(member=member).order_by('-date')[:10]
    templates = MessageTemplate.objects.filter(is_active=True)
    
    import json
    # Compute values for JavaScript
    member_data = {
        'name': member.name,
        'days': member.days_until_expiry or 0,
        'expiry_date': member.active_membership.end_date.strftime('%d %b %Y') if member.active_membership else 'N/A',
        'amount': str(member.active_membership.plan.price) if member.active_membership else '0',
        'plan': member.active_membership.plan.name if member.active_membership else 'N/A',
    }
    
    context = {
        'member': member,
        'payments': payments,
        'templates': templates,
        'member_data_json': json.dumps(member_data),
    }
    return render(request, 'members/member_detail.html', context)


@login_required
def member_add(request):
    if request.method == 'POST':
        form = MemberWithMembershipForm(request.POST, request.FILES, gym=request.user.gym)
        if form.is_valid():
            member = form.save(commit=False)
            member.gym = request.user.gym
            member.save()
            plan = form.cleaned_data.get('plan')
            start_date = form.cleaned_data.get('start_date')
            
            if plan and start_date:
                Membership.objects.create(
                    member=member,
                    plan=plan,
                    start_date=start_date,
                    is_active=True,
                    gym=request.user.gym,
                )
            
            messages.success(request, f'Member {member.name} added successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = MemberWithMembershipForm(gym=request.user.gym)
    
    return render(request, 'members/member_form.html', {'form': form, 'title': 'Add Member'})

@login_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member {member.name} updated successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = MemberForm(instance=member)
    
    return render(request, 'members/member_form.html', {'form': form, 'title': 'Edit Member', 'member': member})


@login_required
def member_pay(request, pk):
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.member = member
            payment.gym = request.user.gym   
            payment.save()
            messages.success(request, f'Payment of ₹{payment.amount} recorded successfully!')
            return redirect('member_detail', pk=member.pk)
    else:
        form = PaymentForm()
    
    return render(request, 'members/payment_form.html', {'form': form, 'member': member})


@login_required
def member_renew(request, pk):
    member = get_object_or_404(Member, pk=pk)

    if request.method == 'POST':
        form = RenewWithPaymentForm(request.POST, gym=request.user.gym)
        if form.is_valid():
            # Create membership
            membership = Membership(
                member=member,
                plan=form.cleaned_data['plan'],
                start_date=form.cleaned_data['start_date'],
                is_active=True,
                gym=request.user.gym,   # <-- add this
            )
            membership.save()  # triggers deactivation of old membership

            # Record payment
            Payment.objects.create(
                member=member,
                amount=form.cleaned_data['amount'],
                method=form.cleaned_data['method'],
                notes=form.cleaned_data.get('notes', ''),
                gym=request.user.gym,   # <-- add this
            )


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    member = payment.member

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully.')
            return redirect('member_detail', pk=member.pk)
    else:
        form = PaymentForm(instance=payment)

    return render(request, 'members/payment_edit.html', {'form': form, 'payment': payment, 'member': member})


@login_required
def payment_delete_confirm(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'members/payment_delete_confirm.html', {'payment': payment, 'member': payment.member})


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    member = payment.member
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted.')
        return redirect('member_detail', pk=member.pk)
    return redirect('payment_delete_confirm', pk=pk)

@login_required
def member_archive(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.is_archived = True
        member.save()
        messages.success(request, f'{member.name} has been archived.')
        return redirect('member_list')
    return render(request, 'members/member_archive_confirm.html', {'member': member})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keeps user logged in after change
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'auth/change_password.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})