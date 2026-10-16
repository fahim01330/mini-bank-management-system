import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import BankAccount
from transactions.models import Transaction

User = get_user_model()

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts"
]

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "Austin, TX",
    "San Jose, CA", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC"
]


class Command(BaseCommand):
    help = "Generate bulk customer users with active bank accounts and realistic balances."

    def add_arguments(self, parser):
        parser.add_argument(
            'count',
            type=int,
            nargs='?',
            default=50,
            help="Number of users to generate (default: 50)"
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.NOTICE(f"Generating {count} customer users with bank accounts..."))

        created_users = 0
        default_password = "Password123!"

        for i in range(1, count + 1):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            random_num = random.randint(100, 9999)
            username = f"{first.lower()}_{last.lower()}{random_num}"
            email = f"{username}@example.com"

            # Avoid duplicates if generated username exists
            if User.objects.filter(username=username).exists():
                username = f"{username}_{i}"
                email = f"{username}@example.com"

            birth_year = random.randint(1970, 2005)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            dob = date(birth_year, birth_month, birth_day)

            phone = f"+1555{random.randint(1000000, 9999999)}"
            address = f"{random.randint(100, 9999)} Main St, {random.choice(CITIES)}"

            user = User.objects.create_user(
                username=username,
                email=email,
                password=default_password,
                first_name=first,
                last_name=last,
                phone_number=phone,
                address=address,
                date_of_birth=dob
            )

            # Create 1 or 2 bank accounts for each user
            num_accounts = random.choice([1, 1, 2])
            for acc_idx in range(num_accounts):
                acc_type = 'SAVINGS' if acc_idx == 0 else 'CURRENT'
                opening_balance = Decimal(str(random.randint(500, 25000))) + Decimal('0.00')

                account = BankAccount.objects.create(
                    owner=user,
                    account_type=acc_type,
                    balance=opening_balance,
                    daily_withdrawal_limit=Decimal('50000.00')
                )

                # Record opening transaction
                Transaction.objects.create(
                    transaction_type='DEPOSIT',
                    amount=opening_balance,
                    account=account,
                    balance_after=opening_balance,
                    status='SUCCESS',
                    description="Opening account deposit"
                )

            created_users += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_users} customer users!\n"
                f"All created users have password: '{default_password}'"
            )
        )
