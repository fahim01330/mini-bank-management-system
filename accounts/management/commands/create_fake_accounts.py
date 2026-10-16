import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import BankAccount, generate_unique_account_number
from transactions.models import Transaction, generate_transaction_reference

User = get_user_model()


class Command(BaseCommand):
    help = "Generate bulk bank accounts with realistic balances, dates, and transactions."

    def add_arguments(self, parser):
        parser.add_argument(
            'count',
            type=int,
            nargs='?',
            default=100,
            help="Number of bank accounts to generate (default: 100)"
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.NOTICE(f"Generating {count} bank accounts with realistic dates and transactions..."))

        users = list(User.objects.filter(is_staff=False))
        if not users:
            self.stdout.write(self.style.ERROR("No customer users found. Please create users first."))
            return

        now = timezone.now()
        created_accounts = 0

        for i in range(1, count + 1):
            owner = random.choice(users)
            acc_type = random.choice(['SAVINGS', 'CURRENT'])
            opening_balance = Decimal(str(random.randint(1000, 75000))) + Decimal('0.00')

            # Generate random creation date within the last 180 days
            days_ago = random.randint(1, 180)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            account_date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            account = BankAccount.objects.create(
                account_number=generate_unique_account_number(),
                owner=owner,
                account_type=acc_type,
                balance=opening_balance,
                status='ACTIVE',
                daily_withdrawal_limit=Decimal('50000.00')
            )

            # Update created_at to the past date (since auto_now_add overrides on create)
            BankAccount.objects.filter(id=account.id).update(
                created_at=account_date,
                updated_at=account_date
            )

            # Create opening deposit transaction
            ref = generate_transaction_reference()
            txn = Transaction.objects.create(
                transaction_reference=ref,
                transaction_type='DEPOSIT',
                amount=opening_balance,
                account=account,
                balance_after=opening_balance,
                status='SUCCESS',
                description="Initial account opening deposit"
            )

            # Update transaction timestamp to match the account opening date
            Transaction.objects.filter(id=txn.id).update(timestamp=account_date)

            created_accounts += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_accounts} bank accounts across {len(users)} users!\n"
                f"All accounts have opening deposit transactions and dates distributed over the past 180 days."
            )
        )
