from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from common.test_utils import auth_client, create_user


class CategoryIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.category_a = Category.objects.create(user=self.user_a, name="Groceries", type=Category.Type.EXPENSE)

    def test_user_cannot_list_other_users_categories(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.category_a.id, ids)

    def test_user_cannot_retrieve_other_users_category_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("category-detail", args=[self.category_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_category_by_id(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("category-detail", args=[self.category_a.id]), {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.category_a.refresh_from_db()
        self.assertEqual(self.category_a.name, "Groceries")

    def test_user_cannot_delete_other_users_category_by_id(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("category-detail", args=[self.category_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(pk=self.category_a.id).exists())

    def test_user_can_crud_own_category(self):
        client = auth_client(self.user_a)
        response = client.post(reverse("category-list"), {"name": "Salary", "type": "income"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)


class CategoryValidationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="c@example.com")

    def test_duplicate_name_rejected(self):
        Category.objects.create(user=self.user, name="Rent", type=Category.Type.EXPENSE)
        client = auth_client(self.user)
        response = client.post(reverse("category-list"), {"name": "Rent", "type": "expense"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
