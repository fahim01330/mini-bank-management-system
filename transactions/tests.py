from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import BankAccount
from transactions.models import Transaction

User = get_user_model()


class TransactionOperationTests(TestCase):
    def setUp(self):
        self.client_alice = APIClient()
        self.client_bob = APIClient()

        self.alice = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='Password123!'
        )
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='Password123!'
        )

        self.client_alice.force_authenticate(user=self.alice)
        self.client_bob.force_authenticate(user=self.bob)

        # Create bank accounts
        self.alice_account = BankAccount.objects.create(
            owner=self.alice,
            account_type='SAVINGS',
            balance=Decimal('1000.00'),
            daily_withdrawal_limit=Decimal('500.00')
        )
        self.bob_account = BankAccount.objects.create(
            owner=self.bob,
            account_type='CURRENT',
            balance=Decimal('200.00')
        )

        self.deposit_url = reverse('transaction-deposit')
        self.withdraw_url = reverse('transaction-withdraw')
        self.transfer_url = reverse('transaction-transfer')
        self.history_url = reverse('transaction-history')

    # ==================== DEPOSIT TESTS ====================
    def test_deposit_valid_positive_amount(self):
        payload = {
            "account": self.alice_account.id,
            "amount": "250.00",
            "description": "Salary bonus"
        }
        response = self.client_alice.post(self.deposit_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.alice_account.refresh_from_db()
        self.assertEqual(self.alice_account.balance, Decimal('1250.00'))
        self.assertTrue(Transaction.objects.filter(account=self.alice_account, transaction_type='DEPOSIT').exists())

    def test_deposit_reject_zero_or_negative_amount(self):
        # Zero amount
        res_zero = self.client_alice.post(
            self.deposit_url,
            {"account": self.alice_account.id, "amount": "0.00"},
            format='json'
        )
        self.assertEqual(res_zero.status_code, status.HTTP_400_BAD_REQUEST)

        # Negative amount
        res_neg = self.client_alice.post(
            self.deposit_url,
            {"account": self.alice_account.id, "amount": "-50.00"},
            format='json'
        )
        self.assertEqual(res_neg.status_code, status.HTTP_400_BAD_REQUEST)

    # ==================== WITHDRAWAL TESTS ====================
    def test_withdrawal_valid_amount(self):
        payload = {
            "account": self.alice_account.id,
            "amount": "100.00",
            "description": "ATM cash"
        }
        response = self.client_alice.post(self.withdraw_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.alice_account.refresh_from_db()
        self.assertEqual(self.alice_account.balance, Decimal('900.00'))

    def test_withdrawal_reject_insufficient_funds(self):
        payload = {
            "account": self.alice_account.id,
            "amount": "2000.00"  # Alice only has 1000.00
        }
        response = self.client_alice.post(self.withdraw_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alice_account.refresh_from_db()
        self.assertEqual(self.alice_account.balance, Decimal('1000.00'))

    def test_withdrawal_reject_zero_or_negative_amount(self):
        res_zero = self.client_alice.post(
            self.withdraw_url,
            {"account": self.alice_account.id, "amount": "0.00"},
            format='json'
        )
        self.assertEqual(res_zero.status_code, status.HTTP_400_BAD_REQUEST)

        res_neg = self.client_alice.post(
            self.withdraw_url,
            {"account": self.alice_account.id, "amount": "-100.00"},
            format='json'
        )
        self.assertEqual(res_neg.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdrawal_daily_limit_exceeded(self):
        # Alice's daily withdrawal limit is set to 500.00 in setUp
        payload = {
            "account": self.alice_account.id,
            "amount": "600.00"  # Exceeds 500.00 limit even though balance is 1000
        }
        response = self.client_alice.post(self.withdraw_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Daily withdrawal limit", str(response.data))

    # ==================== TRANSFER TESTS ====================
    def test_transfer_success_consistent_balances(self):
        payload = {
            "from_account": self.alice_account.id,
            "to_account": self.bob_account.id,
            "amount": "300.00",
            "description": "Lunch split"
        }
        response = self.client_alice.post(self.transfer_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.alice_account.refresh_from_db()
        self.bob_account.refresh_from_db()

        self.assertEqual(self.alice_account.balance, Decimal('700.00'))
        self.assertEqual(self.bob_account.balance, Decimal('500.00'))

        # Check transactions recorded with same reference
        ref = response.data['transaction']['transaction_reference']
        alice_txn = Transaction.objects.get(account=self.alice_account, transaction_reference=ref)
        bob_txn = Transaction.objects.get(account=self.bob_account, transaction_reference=ref)

        self.assertEqual(alice_txn.amount, Decimal('300.00'))
        self.assertEqual(alice_txn.balance_after, Decimal('700.00'))
        self.assertEqual(bob_txn.amount, Decimal('300.00'))
        self.assertEqual(bob_txn.balance_after, Decimal('500.00'))

    def test_transfer_reject_same_account(self):
        payload = {
            "from_account": self.alice_account.id,
            "to_account": self.alice_account.id,
            "amount": "50.00"
        }
        response = self.client_alice.post(self.transfer_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_reject_insufficient_funds(self):
        payload = {
            "from_account": self.alice_account.id,
            "to_account": self.bob_account.id,
            "amount": "1500.00"
        }
        response = self.client_alice.post(self.transfer_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.alice_account.refresh_from_db()
        self.bob_account.refresh_from_db()
        self.assertEqual(self.alice_account.balance, Decimal('1000.00'))
        self.assertEqual(self.bob_account.balance, Decimal('200.00'))

    def test_transfer_unauthorized_from_account(self):
        # Bob attempts to transfer money from Alice's account
        payload = {
            "from_account": self.alice_account.id,
            "to_account": self.bob_account.id,
            "amount": "100.00"
        }
        response = self.client_bob.post(self.transfer_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ==================== HISTORY & FILTER TESTS ====================
    def test_transaction_history_filter_by_type(self):
        # Alice deposits 100
        self.client_alice.post(
            self.deposit_url,
            {"account": self.alice_account.id, "amount": "100.00"},
            format='json'
        )
        # Alice withdraws 50
        self.client_alice.post(
            self.withdraw_url,
            {"account": self.alice_account.id, "amount": "50.00"},
            format='json'
        )

        # Filter by DEPOSIT
        res_dep = self.client_alice.get(f"{self.history_url}?transaction_type=DEPOSIT")
        self.assertEqual(res_dep.status_code, status.HTTP_200_OK)
        results = res_dep.data.get('results', res_dep.data)
        for item in results:
            self.assertEqual(item['transaction_type'], 'DEPOSIT')

        # Filter by WITHDRAWAL
        res_with = self.client_alice.get(f"{self.history_url}?transaction_type=WITHDRAWAL")
        self.assertEqual(res_with.status_code, status.HTTP_200_OK)
        results = res_with.data.get('results', res_with.data)
        for item in results:
            self.assertEqual(item['transaction_type'], 'WITHDRAWAL')
