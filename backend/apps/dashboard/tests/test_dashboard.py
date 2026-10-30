from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.budgets.models import Budget
from apps.categories.models import Category
from apps.transactions.models import Transaction
from common.test_utils import auth_client, create_user


class DashboardAggregationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="d@example.com")
        self.other_user = create_user(email="other@example.com")

        self.salary = Category.objects.create(user=self.user, name="Salary", type=Category.Type.INCOME)
        self.groceries = Category.objects.create(user=self.user, name="Groceries", type=Category.Type.EXPENSE)
        self.entertainment = Category.objects.create(user=self.user, name="Entertainment", type=Category.Type.EXPENSE)
        self.rent = Category.objects.create(user=self.user, name="Rent", type=Category.Type.EXPENSE)

        # Budgeted categories: groceries (over), entertainment (under).
        Budget.objects.create(user=self.user, category=self.groceries, month="2026-01-01", limit_amount="200.00")
        Budget.objects.create(user=self.user, category=self.entertainment, month="2026-01-01", limit_amount="100.00")
        # Rent has no budget at all, but has spending this month.

        Transaction.objects.create(user=self.user, category=self.salary, amount="3000.00", type="income", date="2026-01-03")
        Transaction.objects.create(user=self.user, category=self.groceries, amount="150.00", type="expense", date="2026-01-05")
        Transaction.objects.create(user=self.user, category=self.groceries, amount="100.00", type="expense", date="2026-01-20")
        Transaction.objects.create(user=self.user, category=self.entertainment, amount="40.00", type="expense", date="2026-01-10")
        Transaction.objects.create(user=self.user, category=self.rent, amount="900.00", type="expense", date="2026-01-01")

        # Different month - must not leak into January totals.
        Transaction.objects.create(user=self.user, category=self.groceries, amount="999.00", type="expense", date="2026-02-01")

        # Other user's data must never appear.
        other_cat = Category.objects.create(user=self.other_user, name="Groceries", type=Category.Type.EXPENSE)
        Transaction.objects.create(user=self.other_user, category=other_cat, amount="500.00", type="expense", date="2026-01-01")

    def test_totals_and_net(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"), {"month": "2026-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["total_income"]), Decimal("3000.00"))
        self.assertEqual(Decimal(response.data["total_expenses"]), Decimal("1190.00"))
        self.assertEqual(Decimal(response.data["net"]), Decimal("1810.00"))

    def test_budgeted_category_breakdown(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"), {"month": "2026-01"})
        rows = {row["category_name"]: row for row in response.data["categories"]}

        groceries_row = rows["Groceries"]
        self.assertEqual(Decimal(groceries_row["spent"]), Decimal("250.00"))
        self.assertEqual(Decimal(groceries_row["budget_limit"]), Decimal("200.00"))
        self.assertEqual(Decimal(groceries_row["remaining"]), Decimal("-50.00"))

        entertainment_row = rows["Entertainment"]
        self.assertEqual(Decimal(entertainment_row["spent"]), Decimal("40.00"))
        self.assertEqual(Decimal(entertainment_row["budget_limit"]), Decimal("100.00"))
        self.assertEqual(Decimal(entertainment_row["remaining"]), Decimal("60.00"))

    def test_unbudgeted_category_shows_spent_only(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"), {"month": "2026-01"})
        rows = {row["category_name"]: row for row in response.data["categories"]}

        rent_row = rows["Rent"]
        self.assertEqual(Decimal(rent_row["spent"]), Decimal("900.00"))
        self.assertIsNone(rent_row["budget_limit"])
        self.assertIsNone(rent_row["remaining"])

    def test_income_category_never_in_expense_breakdown(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"), {"month": "2026-01"})
        names = [row["category_name"] for row in response.data["categories"]]
        self.assertNotIn("Salary", names)

    def test_defaults_to_current_month_on_missing_param(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("month", response.data)
