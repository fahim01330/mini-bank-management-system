from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import BankAccount
from transactions.models import Transaction, generate_transaction_reference

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with demo users, bank accounts, and transactions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Setting up demo data for Mini Bank Management System..."))

        # Create Admin
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@minibank.com",
                "first_name": "System",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists.")

        # Create Customer 1: John Doe
        john, created = User.objects.get_or_create(
            username="john_doe",
            defaults={
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+15551234567",
                "address": "456 Elm St, New York, NY",
            }
        )
        if created:
            john.set_password("password123")
            john.save()
            self.stdout.write(self.style.SUCCESS("Created customer: john_doe / password123"))

        # Create Customer 2: Jane Smith
        jane, created = User.objects.get_or_create(
            username="jane_smith",
            defaults={
                "email": "jane.smith@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone_number": "+15559876543",
                "address": "789 Oak Ave, San Francisco, CA",
            }
        )
        if created:
            jane.set_password("password123")
            jane.save()
            self.stdout.write(self.style.SUCCESS("Created customer: jane_smith / password123"))

        # Create Accounts for John
        john_savings, _ = BankAccount.objects.get_or_create(
            owner=john,
            account_type="SAVINGS",
            defaults={"balance": Decimal('5000.00'), "daily_withdrawal_limit": Decimal('10000.00')}
        )
        john_current, _ = BankAccount.objects.get_or_create(
            owner=john,
            account_type="CURRENT",
            defaults={"balance": Decimal('1500.00'), "daily_withdrawal_limit": Decimal('15000.00')}
        )

        # Create Account for Jane
        jane_savings, _ = BankAccount.objects.get_or_create(
            owner=jane,
            account_type="SAVINGS",
            defaults={"balance": Decimal('3200.00'), "daily_withdrawal_limit": Decimal('10000.00')}
        )

        # Record demo transactions if none exist
        if not Transaction.objects.filter(account=john_savings).exists():
            # Initial deposit
            Transaction.objects.create(
                transaction_type="DEPOSIT",
                amount=Decimal('5000.00'),
                account=john_savings,
                balance_after=john_savings.balance,
                status="SUCCESS",
                description="Opening account deposit"
            )

            # Withdrawal from John's current
            Transaction.objects.create(
                transaction_type="DEPOSIT",
                amount=Decimal('2000.00'),
                account=john_current,
                balance_after=Decimal('2000.00'),
                status="SUCCESS",
                description="Salary direct deposit"
            )
            Transaction.objects.create(
                transaction_type="WITHDRAWAL",
                amount=Decimal('500.00'),
                account=john_current,
                balance_after=Decimal('1500.00'),
                status="SUCCESS",
                description="Branch ATM cash withdrawal"
            )

            # Transfer from John to Jane
            ref = generate_transaction_reference()
            Transaction.objects.create(
                transaction_reference=ref,
                transaction_type="TRANSFER",
                amount=Decimal('300.00'),
                account=john_savings,
                related_account=jane_savings,
                balance_after=john_savings.balance,
                status="SUCCESS",
                description=f"Transfer to {jane_savings.account_number}"
            )
            Transaction.objects.create(
                transaction_reference=ref,
                transaction_type="TRANSFER",
                amount=Decimal('300.00'),
                account=jane_savings,
                related_account=john_savings,
                balance_after=jane_savings.balance,
                status="SUCCESS",
                description=f"Transfer received from {john_savings.account_number}"
            )

            self.stdout.write(self.style.SUCCESS("Created demo transactions and account activities."))

        self.stdout.write(self.style.SUCCESS("Demo setup successfully completed!"))
