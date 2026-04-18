"""
python manage.py seed_data

Seeds:
  1 admin        → admin@homeease.in  / admin123
  8 providers    → (email below)      / provider123
  2 customers    → (email below)      / customer123
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


PROVIDERS = [
    dict(name='Rajesh Kumar',  email='rajesh@homeease.in',   phone='9876543210',
         city='Ahmedabad',  area='Navrangpura',  state='Gujarat',
         skill='Plumber',           gender='Male',   experience=10,
         working_hours='Mon-Sat 8AM-6PM',
         description='10 years experience in home plumbing, pipe fitting, '
                     'leak fixes, and bathroom installations.',
         aadhaar='123456789012', rating=4.7, available=True),

    dict(name='Sunita Devi',   email='sunita@homeease.in',   phone='9876543211',
         city='Surat',       area='Adajan',       state='Gujarat',
         skill='Electrician',        gender='Female', experience=7,
         working_hours='Mon-Sat 9AM-5PM',
         description='Specialized in home wiring, switchboard repair, '
                     'inverter installation, and electrical safety.',
         aadhaar='123456789013', rating=4.9, available=True),

    dict(name='Aman Singh',    email='aman@homeease.in',     phone='9876543212',
         city='Vadodara',    area='Alkapuri',     state='Gujarat',
         skill='Carpenter',          gender='Male',   experience=8,
         working_hours='Mon-Sun 9AM-7PM',
         description='Furniture making, door/window repair, custom woodwork '
                     'and modular kitchen installations.',
         aadhaar='123456789014', rating=4.5, available=False),

    dict(name='Pooja Sharma',  email='pooja@homeease.in',    phone='9876543213',
         city='Rajkot',      area='Kalavad Road', state='Gujarat',
         skill='Cleaner',            gender='Female', experience=5,
         working_hours='Mon-Fri 8AM-4PM',
         description='Home and office deep cleaning, post-construction cleaning, '
                     'sofa and mattress cleaning.',
         aadhaar='123456789015', rating=4.4, available=True),

    dict(name='Vikash Patel',  email='vikash@homeease.in',   phone='9876543214',
         city='Bhavnagar',   area='Waghawadi',    state='Gujarat',
         skill='Painter',            gender='Male',   experience=12,
         working_hours='Mon-Sat 7AM-5PM',
         description='Interior and exterior painting, texture painting, '
                     'waterproof coating, and wall design.',
         aadhaar='123456789016', rating=4.2, available=True),

    dict(name='Kavita Mehta',  email='kavita@homeease.in',   phone='9876543215',
         city='Ahmedabad',   area='Satellite',    state='Gujarat',
         skill='AC Technician',      gender='Female', experience=6,
         working_hours='Mon-Sat 10AM-6PM',
         description='AC installation, servicing, gas refilling, '
                     'and repair for all brands.',
         aadhaar='123456789017', rating=4.6, available=True),

    dict(name='Suresh Yadav',  email='suresh@homeease.in',   phone='9876543216',
         city='Gandhinagar', area='Sector 5',     state='Gujarat',
         skill='Pest Control',       gender='Male',   experience=9,
         working_hours='Mon-Sat 9AM-5PM',
         description='General pest control, termite treatment, rodent control, '
                     'and annual maintenance contracts.',
         aadhaar='123456789018', rating=4.3, available=False),

    dict(name='Deepak Nair',   email='deepak@homeease.in',   phone='9876543217',
         city='Surat',       area='Vesu',         state='Gujarat',
         skill='CCTV Installation',  gender='Male',   experience=4,
         working_hours='Mon-Sun 10AM-7PM',
         description='CCTV installation, NVR/DVR setup, access control, '
                     'and video door phone installation.',
         aadhaar='123456789019', rating=4.7, available=True),
]

CUSTOMERS = [
    dict(name='Priya Patel',  email='priya@example.com',  phone='9000000001',
         city='Ahmedabad', area='Bodakdev',  state='Gujarat'),
    dict(name='Rohit Mehta',  email='rohit@example.com',  phone='9000000002',
         city='Surat',     area='Citylight', state='Gujarat'),
]


class Command(BaseCommand):
    help = 'Seed HomeEase with admin, demo providers, and sample customers.'

    def handle(self, *args, **options):
        from apps.accounts.models import User, Notification
        from apps.providers.models import ProviderProfile

        self.stdout.write('\nSeeding HomeEase…\n')

        # ── Admin ──────────────────────────────────────────────────────
        if not User.objects.filter(email='admin@homeease.in').exists():
            User.objects.create_superuser(
                email='admin@homeease.in',
                password='admin123',
                name='Admin',
                role=User.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Admin  →  admin@homeease.in / admin123'))
        else:
            self.stdout.write('  – Admin already exists, skipped.')

        # ── Providers ──────────────────────────────────────────────────
        for p in PROVIDERS:
            if User.objects.filter(email=p['email']).exists():
                self.stdout.write(f"  – Provider {p['email']} exists, skipped.")
                continue
            rating     = p.pop('rating')
            available  = p.pop('available')
            prof_keys  = ['skill', 'gender', 'experience', 'working_hours',
                          'description', 'aadhaar']
            prof_data  = {k: p.pop(k) for k in prof_keys}
            user = User.objects.create_user(role=User.PROVIDER, password='provider123', **p)
            ProviderProfile.objects.create(
                user=user,
                status=ProviderProfile.APPROVED,
                is_available=available,
                rating=rating,
                total_reviews=max(5, int(rating * 8)),
                approved_at=timezone.now(),
                **prof_data,
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Provider: {user.name}'))

        # ── Customers ──────────────────────────────────────────────────
        for c in CUSTOMERS:
            if User.objects.filter(email=c['email']).exists():
                self.stdout.write(f"  – Customer {c['email']} exists, skipped.")
                continue
            user = User.objects.create_user(role=User.CUSTOMER, password='customer123', **c)
            Notification.objects.create(
                user=user,
                title='Welcome to HomeEase! 🎉',
                sub='Your account was created successfully.',
                type='green',
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Customer: {user.name}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete!\n'))
        self.stdout.write('Credentials:')
        self.stdout.write('  Admin:    admin@homeease.in  / admin123')
        self.stdout.write('  Customer: priya@example.com / customer123')
        self.stdout.write('  Provider: rajesh@homeease.in / provider123\n')
