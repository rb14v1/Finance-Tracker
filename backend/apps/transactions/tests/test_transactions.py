from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.transactions.models import Transaction
from common.test_utils import auth_client, create_user


class TransactionIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.category_a = Category.objects.create(user=self.user_a, name="Groceries", type=Category.Type.EXPENSE)
        self.txn_a = Transaction.objects.create(
            user=self.user_a, category=self.category_a, amount="50.00",
            type=Category.Type.EXPENSE, date="2026-01-15",
        )

    def test_user_cannot_list_other_users_transactions(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("transaction-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.txn_a.id, ids)

    def test_user_cannot_retrieve_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("transaction-detail", args=[self.txn_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("transaction-detail", args=[self.txn_a.id]), {"amount": "999.00"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.txn_a.refresh_from_db()
        self.assertEqual(str(self.txn_a.amount), "50.00")

    def test_user_cannot_delete_other_users_transaction_by_id(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("transaction-detail", args=[self.txn_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Transaction.objects.filter(pk=self.txn_a.id).exists())

    def test_user_cannot_create_transaction_against_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.post(reverse("transaction-list"), {
            "category": self.category_a.id, "amount": "10.00", "type": "expense", "date": "2026-01-16",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionValidationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="v@example.com")
        self.expense_cat = Category.objects.create(user=self.user, name="Rent", type=Category.Type.EXPENSE)
        self.income_cat = Category.objects.create(user=self.user, name="Salary", type=Category.Type.INCOME)

    def test_type_must_match_category_type_expense_category_income_type(self):
        client = auth_client(self.user)
        response = client.post(reverse("transaction-list"), {
            "category": self.expense_cat.id, "amount": "100.00", "type": "income", "date": "2026-01-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)

    def test_type_must_match_category_type_income_category_expense_type(self):
        client = auth_client(self.user)
        response = client.post(reverse("transaction-list"), {
            "category": self.income_cat.id, "amount": "100.00", "type": "expense", "date": "2026-01-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)

    def test_matching_type_and_category_succeeds(self):
        client = auth_client(self.user)
        response = client.post(reverse("transaction-list"), {
            "category": self.expense_cat.id, "amount": "100.00", "type": "expense", "date": "2026-01-01",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_negative_amount_rejected(self):
        client = auth_client(self.user)
        response = client.post(reverse("transaction-list"), {
            "category": self.expense_cat.id, "amount": "-5.00", "type": "expense", "date": "2026-01-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_month(self):
        client = auth_client(self.user)
        Transaction.objects.create(user=self.user, category=self.expense_cat, amount="20.00", type="expense", date="2026-01-05")
        Transaction.objects.create(user=self.user, category=self.expense_cat, amount="30.00", type="expense", date="2026-02-05")
        response = client.get(reverse("transaction-list"), {"month": "2026-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
