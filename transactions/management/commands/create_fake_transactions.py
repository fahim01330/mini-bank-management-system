import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.management.base import BaseCommand
from accounts.models import BankAccount
from transactions.models import Transaction, generate_transaction_reference

DEPOSIT_DESCRIPTIONS = [
    "Salary direct deposit",
    "Client freelance payout",
    "Cash deposit at branch",
    "Mobile check deposit",
    "Investment dividend payout",
    "Consulting fee",
    "Tax refund deposit",
    "Bonus payout",
]

WITHDRAW_DESCRIPTIONS = [
    "Branch ATM cash withdrawal",
    "Online bill payment",
    "Debit card retail purchase",
    "Grocery supermarket payment",
    "Utility electric bill payment",
    "Gas station payment",
    "Restaurant dining payment",
    "Pharmacy purchase",
]

TRANSFER_DESCRIPTIONS = [
    "Peer-to-peer money transfer",
    "Dinner bill split",
    "Apartment rent share",
    "Gift to family member",
    "Emergency fund transfer",
    "Project expense reimbursement",
    "Loan repayment split",
]


class Command(BaseCommand):
    help = "Generate bulk realistic transactions (Deposits, Withdrawals, Transfers) with distributed dates."

    def add_arguments(self, parser):
        parser.add_argument(
            'count',
            type=int,
            nargs='?',
            default=150,
            help="Number of transactions to generate (default: 150)"
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.NOTICE(f"Generating {count} realistic transactions with historical dates..."))

        accounts = list(BankAccount.objects.filter(status='ACTIVE'))
        if len(accounts) < 2:
            self.stdout.write(self.style.ERROR("Need at least 2 active bank accounts to generate transactions."))
            return

        now = timezone.now()
        created_count = 0

        # We will loop until we generate `count` transactions
        while created_count < count:
            txn_type = random.choice(['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'DEPOSIT'])
            days_ago = random.randint(1, 120)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            txn_time = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            if txn_type == 'DEPOSIT':
                acc = random.choice(accounts)
                amount = Decimal(str(random.randint(100, 5000))) + Decimal('0.00')

                with db_transaction.atomic():
                    locked_acc = BankAccount.objects.select_for_update().get(id=acc.id)
                    locked_acc.balance += amount
                    locked_acc.save(update_fields=['balance'])

                    ref = generate_transaction_reference()
                    txn = Transaction.objects.create(
                        transaction_reference=ref,
                        transaction_type='DEPOSIT',
                        amount=amount,
                        account=locked_acc,
                        balance_after=locked_acc.balance,
                        status='SUCCESS',
                        description=random.choice(DEPOSIT_DESCRIPTIONS)
                    )
                    Transaction.objects.filter(id=txn.id).update(timestamp=txn_time)

                created_count += 1

            elif txn_type == 'WITHDRAWAL':
                acc = random.choice(accounts)
                # Keep withdrawal reasonable so balance doesn't go below 100
                if acc.balance > Decimal('300.00'):
                    max_withdraw = int(min(acc.balance - Decimal('100.00'), Decimal('2000.00')))
                    if max_withdraw >= 50:
                        amount = Decimal(str(random.randint(50, max_withdraw))) + Decimal('0.00')

                        with db_transaction.atomic():
                            locked_acc = BankAccount.objects.select_for_update().get(id=acc.id)
                            if locked_acc.balance >= amount:
                                locked_acc.balance -= amount
                                locked_acc.save(update_fields=['balance'])

                                ref = generate_transaction_reference()
                                txn = Transaction.objects.create(
                            transaction_reference=ref,
                            transaction_type='WITHDRAWAL',
                            amount=amount,
                            account=locked_acc,
                            balance_after=locked_acc.balance,
                            status='SUCCESS',
                            description=random.choice(WITHDRAW_DESCRIPTIONS)
                        )
                                Transaction.objects.filter(id=txn.id).update(timestamp=txn_time)
                                created_count += 1

            elif txn_type == 'TRANSFER':
                acc_from, acc_to = random.sample(accounts, 2)
                if acc_from.balance > Decimal('200.00'):
                    max_transfer = int(min(acc_from.balance - Decimal('50.00'), Decimal('1500.00')))
                    if max_transfer >= 50:
                        amount = Decimal(str(random.randint(50, max_transfer))) + Decimal('0.00')

                        with db_transaction.atomic():
                            # Lock in ID order
                            first_id, second_id = sorted([acc_from.id, acc_to.id])
                            acc_map = {
                                a.id: a
                                for a in BankAccount.objects.select_for_update().filter(id__in=[first_id, second_id])
                            }
                            locked_from = acc_map[acc_from.id]
                            locked_to = acc_map[acc_to.id]

                            if locked_from.balance >= amount:
                                locked_from.balance -= amount
                                locked_from.save(update_fields=['balance'])

                                locked_to.balance += amount
                                locked_to.save(update_fields=['balance'])

                                ref = generate_transaction_reference()
                                desc = random.choice(TRANSFER_DESCRIPTIONS)

                                t1 = Transaction.objects.create(
                                    transaction_reference=ref,
                                    transaction_type='TRANSFER',
                                    amount=amount,
                                    account=locked_from,
                                    related_account=locked_to,
                                    balance_after=locked_from.balance,
                                    status='SUCCESS',
                                    description=f"{desc} (to {locked_to.account_number})"
                                )
                                t2 = Transaction.objects.create(
                                    transaction_reference=ref,
                                    transaction_type='TRANSFER',
                                    amount=amount,
                                    account=locked_to,
                                    related_account=locked_from,
                                    balance_after=locked_to.balance,
                                    status='SUCCESS',
                                    description=f"{desc} (from {locked_from.account_number})"
                                )

                                Transaction.objects.filter(id=t1.id).update(timestamp=txn_time)
                                Transaction.objects.filter(id=t2.id).update(timestamp=txn_time)

                                created_count += 2  # Paired double-entry ledger records

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {created_count} transactions across active bank accounts!\n"
                f"Transactions include Deposits, Withdrawals, and Peer-to-Peer Transfers with dates across the last 120 days."
            )
        )
