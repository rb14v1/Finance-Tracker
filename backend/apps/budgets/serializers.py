from rest_framework import serializers

from apps.budgets.models import Budget
from apps.categories.models import Category


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "category", "category_name", "month", "limit_amount", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_limit_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Limit amount must be greater than zero.")
        return value

    def validate_category(self, value):
        request = self.context["request"]
        if value.user_id != request.user.id:
            raise serializers.ValidationError("Category not found.")
        if value.type != Category.Type.EXPENSE:
            raise serializers.ValidationError("Budgets can only be set on expense categories.")
        return value

    def validate_month(self, value):
        return value.replace(day=1)

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        month = attrs.get("month", getattr(self.instance, "month", None))
        request = self.context["request"]
        if category and month:
            qs = Budget.objects.filter(user=request.user, category=category, month=month)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A budget for this category and month already exists.")
        return attrs
