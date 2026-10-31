from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.budgets.models import Budget
from apps.categories.models import Category
from apps.transactions.models import Transaction


def _parse_month(raw: str | None) -> tuple[int, int]:
    """Returns (year, month). Falls back to the current month for a missing
    or malformed ?month=YYYY-MM value."""
    if raw:
        try:
            year_str, month_str = raw.split("-")
            year, month = int(year_str), int(month_str)
            if 1 <= month <= 12:
                return year, month
        except (ValueError, AttributeError):
            pass
    today = date.today()
    return today.year, today.month


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year, month = _parse_month(request.query_params.get("month"))
        user = request.user

        totals = (
            Transaction.objects.filter(user=user, date__year=year, date__month=month)
            .values("type")
            .annotate(total=Sum("amount"))
        )
        totals_by_type = {row["type"]: row["total"] for row in totals}
        total_income = totals_by_type.get(Transaction.Type.INCOME, Decimal("0"))
        total_expenses = totals_by_type.get(Transaction.Type.EXPENSE, Decimal("0"))

        spent_by_category = {
            row["category_id"]: row["total"]
            for row in (
                Transaction.objects.filter(
                    user=user, type=Transaction.Type.EXPENSE, date__year=year, date__month=month
                )
                .values("category_id")
                .annotate(total=Sum("amount"))
            )
        }

        budgets_by_category = {
            budget.category_id: budget
            for budget in Budget.objects.filter(user=user, month__year=year, month__month=month)
        }

        category_ids = set(spent_by_category) | set(budgets_by_category)
        categories = {c.id: c for c in Category.objects.filter(id__in=category_ids)}

        breakdown = []
        for category_id in category_ids:
            category = categories.get(category_id)
            if category is None:
                continue
            spent = spent_by_category.get(category_id, Decimal("0"))
            budget = budgets_by_category.get(category_id)
            row = {
                "category": category.id,
                "category_name": category.name,
                "spent": spent,
                "budget_limit": budget.limit_amount if budget else None,
                "remaining": (budget.limit_amount - spent) if budget else None,
            }
            breakdown.append(row)

        breakdown.sort(key=lambda row: row["category_name"])

        return Response({
            "month": f"{year:04d}-{month:02d}",
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "categories": breakdown,
        })
