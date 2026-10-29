"""Fill a gym with realistic sample members, plans, memberships and payments for demos and screenshots.

    python manage.py seed_demo --username demo --password demo12345

Creates the user and gym if missing. Refuses to run if that gym already has members, so it never mixes
sample data into a real gym. Use it on a local or demo database only.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from members.models import Member, Membership, Payment, Plan
from tenants.models import Gym

FIRST = ['Aarav', 'Vivaan', 'Aditya', 'Rohan', 'Kabir', 'Arjun', 'Ishaan', 'Reyansh', 'Sai', 'Karan', 'Rahul', 'Nikhil',
         'Siddharth', 'Yash', 'Harsh', 'Ananya', 'Diya', 'Saanvi', 'Aadhya', 'Isha', 'Kavya', 'Priya', 'Neha', 'Riya',
         'Pooja', 'Sneha', 'Meera', 'Tanvi', 'Shreya', 'Nandini']
LAST = ['Sharma', 'Verma', 'Gupta', 'Mehta', 'Patel', 'Singh', 'Joshi', 'Dubey', 'Mishra', 'Tiwari', 'Agarwal', 'Rao',
        'Nair', 'Kapoor', 'Chouhan', 'Saxena', 'Pandey', 'Yadav', 'Jain', 'Thakur']
AREAS = ['Arera Colony', 'MP Nagar', 'Kolar Road', 'Shahpura', 'Indrapuri', 'TT Nagar', 'Bawadia Kalan', 'Ayodhya Nagar']
PLANS = [('Monthly', 30, '1200'), ('Quarterly', 90, '3200'), ('Half-yearly', 180, '5800'), ('Annual', 365, '9999'),
         ('Personal Training (Monthly)', 30, '4500')]


class Command(BaseCommand):
    help = 'Fill a gym with realistic sample data (local/demo databases only).'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='demo')
        parser.add_argument('--password', default='demo12345')
        parser.add_argument('--gym', default='Iron Temple Fitness')
        parser.add_argument('--members', type=int, default=128)
        parser.add_argument('--seed', type=int, default=7)

    def handle(self, *args, **opts):
        rnd = random.Random(opts['seed'])
        today = timezone.localdate()
        User = get_user_model()
        user, made = User.objects.get_or_create(username=opts['username'])
        if made:
            user.set_password(opts['password'])
            user.save()
        gym, _ = Gym.objects.get_or_create(owner=user, defaults={'name': opts['gym'], 'slug': opts['username']})
        if made:  # a signal may have named the new gym already
            Gym.objects.filter(pk=gym.pk).update(name=opts['gym'])
            gym.refresh_from_db()
        if Member.objects.unscoped().filter(gym=gym).exists():
            raise CommandError(f'{gym} already has members; refusing to add sample data.')

        plans = [Plan.objects.create(gym=gym, name=n, duration_days=d, price=Decimal(p)) for n, d, p in PLANS]
        weights = [40, 25, 12, 15, 8]
        phones = set()

        # (how many, days until the membership ends): spread so every dashboard tile has something
        buckets = [(6, (1, 3)), (9, (4, 7)), (11, (8, 15)), (opts['members'] - 26 - 14 - 2, (16, 300))]
        # created first, so the newest-first member list opens on active members
        for _ in range(14):  # overdue: expired, not renewed
            self._member(gym, rnd, plans, weights, phones, today, end_in=-rnd.randint(2, 40), birthday=False)
        for _ in range(2):  # paused
            m = self._member(gym, rnd, plans, weights, phones, today, end_in=rnd.randint(20, 60), birthday=False)
            m.status = 'paused'
            m.save()

        n = 0
        for count, (lo, hi) in buckets:
            for _ in range(count):
                n += 1
                self._member(gym, rnd, plans, weights, phones, today, end_in=rnd.randint(lo, hi), birthday=n <= 3)
        self.stdout.write(self.style.SUCCESS(
            f'{gym}: {Member.objects.unscoped().filter(gym=gym).count()} members, '
            f'{Payment.objects.unscoped().filter(gym=gym).count()} payments. Log in as {user.username}.'))

    def _member(self, gym, rnd, plans, weights, phones, today, end_in, birthday):
        phone = None
        while phone is None or phone in phones:
            phone = str(rnd.choice([6, 7, 8, 9])) + ''.join(str(rnd.randint(0, 9)) for _ in range(9))
        phones.add(phone)
        if birthday:
            year = today.year - rnd.randint(19, 40)
            dob = today.replace(year=year) if not (today.month == 2 and today.day == 29) else date(year, 2, 28)
        else:
            dob = today - timedelta(days=rnd.randint(19 * 365, 45 * 365))
        m = Member.objects.create(
            gym=gym, name=f'{rnd.choice(FIRST)} {rnd.choice(LAST)}', phone=phone, dob=dob,
            address=f'{rnd.randint(1, 300)}, {rnd.choice(AREAS)}, Bhopal',
            status='active' if end_in >= 0 else 'expired')
        plan = rnd.choices(plans, weights)[0]
        end = today + timedelta(days=end_in)
        start = end - timedelta(days=plan.duration_days)
        Membership.objects.create(gym=gym, member=m, plan=plan, start_date=start, end_date=end, is_active=end_in >= 0)
        p = Payment.objects.create(gym=gym, member=m, amount=plan.price, method=rnd.choice(['UPI', 'UPI', 'Cash', 'Card']))
        Payment.objects.unscoped().filter(pk=p.pk).update(date=start)  # date is auto_now_add
        Member.objects.unscoped().filter(pk=m.pk).update(joined_at=start - timedelta(days=rnd.randint(0, 400)))
        return m
