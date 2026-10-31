from django.conf import settings
from django.db import models

from apps.categories.models import Category


class Budget(models.Model):
    """A spending limit for one expense category in one calendar month.

    `month` is stored as a DateField normalised to the first day of the
    month (e.g. 2026-01-01 represents "January 2026"). This avoids a second
    year/month int-pair column while still giving us a clean unique
    constraint and easy __year/__month filtering, matching how
    Transaction.date is already queried.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    month = models.DateField(help_text="Always normalised to the first day of the month.")
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month"]
        constraints = [
            models.UniqueConstraint(fields=["user", "category", "month"], name="unique_budget_per_category_month"),
        ]

    def __str__(self):
        return f"{self.category.name} budget for {self.month:%Y-%m}"
