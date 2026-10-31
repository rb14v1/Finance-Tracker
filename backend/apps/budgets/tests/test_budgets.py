from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.budgets.models import Budget
from apps.categories.models import Category
from common.test_utils import auth_client, create_user


class BudgetIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.category_a = Category.objects.create(user=self.user_a, name="Groceries", type=Category.Type.EXPENSE)
        self.budget_a = Budget.objects.create(
            user=self.user_a, category=self.category_a, month="2026-01-01", limit_amount="300.00",
        )

    def test_user_cannot_list_other_users_budgets(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("budget-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.budget_a.id, ids)

    def test_user_cannot_retrieve_other_users_budget_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("budget-detail", args=[self.budget_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_budget_by_id(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("budget-detail", args=[self.budget_a.id]), {"limit_amount": "999.00"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_other_users_budget_by_id(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("budget-detail", args=[self.budget_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Budget.objects.filter(pk=self.budget_a.id).exists())

    def test_user_cannot_create_budget_against_other_users_category(self):
        client = auth_client(self.user_b)
        response = client.post(reverse("budget-list"), {
            "category": self.category_a.id, "month": "2026-02-01", "limit_amount": "100.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BudgetValidationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="v@example.com")
        self.expense_cat = Category.objects.create(user=self.user, name="Rent", type=Category.Type.EXPENSE)
        self.income_cat = Category.objects.create(user=self.user, name="Salary", type=Category.Type.INCOME)

    def test_budget_on_income_category_rejected(self):
        client = auth_client(self.user)
        response = client.post(reverse("budget-list"), {
            "category": self.income_cat.id, "month": "2026-01-01", "limit_amount": "100.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_month_normalised_to_first_of_month(self):
        client = auth_client(self.user)
        response = client.post(reverse("budget-list"), {
            "category": self.expense_cat.id, "month": "2026-01-15", "limit_amount": "100.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["month"], "2026-01-01")

    def test_duplicate_budget_for_same_category_and_month_rejected(self):
        Budget.objects.create(user=self.user, category=self.expense_cat, month="2026-01-01", limit_amount="100.00")
        client = auth_client(self.user)
        response = client.post(reverse("budget-list"), {
            "category": self.expense_cat.id, "month": "2026-01-01", "limit_amount": "200.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
