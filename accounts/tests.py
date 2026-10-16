from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import BankAccount

User = get_user_model()


class BankAccountManagementTests(TestCase):
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

        self.accounts_url = reverse('account-list-create')

    def test_create_bank_account_with_initial_deposit(self):
        payload = {
            "account_type": "SAVINGS",
            "initial_deposit": "500.00"
        }
        response = self.client_alice.post(self.accounts_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(str(response.data['balance'])), Decimal('500.00'))
        self.assertTrue(len(response.data['account_number']) >= 10)
        self.assertEqual(response.data['owner_username'], 'alice')

    def test_unique_account_numbers_generated(self):
        res1 = self.client_alice.post(self.accounts_url, {"account_type": "SAVINGS"}, format='json')
        res2 = self.client_alice.post(self.accounts_url, {"account_type": "CURRENT"}, format='json')
        self.assertNotEqual(res1.data['account_number'], res2.data['account_number'])

    def test_list_own_accounts_only(self):
        self.client_alice.post(self.accounts_url, {"account_type": "SAVINGS"}, format='json')
        self.client_bob.post(self.accounts_url, {"account_type": "CURRENT"}, format='json')

        response = self.client_alice.get(self.accounts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that only Alice's account is returned
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['owner_username'], 'alice')

    def test_view_account_details_and_balance(self):
        res = self.client_alice.post(self.accounts_url, {"account_type": "SAVINGS", "initial_deposit": "1000.00"}, format='json')
        acc_id = res.data['id']

        detail_url = reverse('account-detail', kwargs={'pk': acc_id})
        balance_url = reverse('account-balance', kwargs={'pk': acc_id})

        detail_res = self.client_alice.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(detail_res.data['balance'])), Decimal('1000.00'))

        balance_res = self.client_alice.get(balance_url)
        self.assertEqual(balance_res.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(balance_res.data['balance'])), Decimal('1000.00'))

    def test_prevent_cross_customer_account_access(self):
        res = self.client_alice.post(self.accounts_url, {"account_type": "SAVINGS"}, format='json')
        alice_acc_id = res.data['id']

        # Bob attempts to view Alice's account details and balance
        detail_url = reverse('account-detail', kwargs={'pk': alice_acc_id})
        balance_url = reverse('account-balance', kwargs={'pk': alice_acc_id})

        detail_res = self.client_bob.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_403_FORBIDDEN)

        balance_res = self.client_bob.get(balance_url)
        self.assertEqual(balance_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_account_statement_csv_and_pdf(self):
        res = self.client_alice.post(self.accounts_url, {"account_type": "SAVINGS", "initial_deposit": "200.00"}, format='json')
        acc_id = res.data['id']

        statement_url = reverse('account-statement', kwargs={'pk': acc_id})

        # Test CSV export
        csv_res = self.client_alice.get(f"{statement_url}?format=csv")
        self.assertEqual(csv_res.status_code, status.HTTP_200_OK)
        self.assertEqual(csv_res['Content-Type'], 'text/csv')

        # Test PDF export
        pdf_res = self.client_alice.get(f"{statement_url}?format=pdf")
        self.assertEqual(pdf_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_res['Content-Type'], 'application/pdf')
