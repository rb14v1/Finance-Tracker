from rest_framework import permissions, viewsets

from apps.budgets.models import Budget
from apps.budgets.serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Budget.objects.filter(user=self.request.user).select_related("category")
        month = self.request.query_params.get("month")
        if month:
            try:
                year_str, month_str = month.split("-")
                qs = qs.filter(month__year=int(year_str), month__month=int(month_str))
            except (ValueError, AttributeError):
                pass
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
