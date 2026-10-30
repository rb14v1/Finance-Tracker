from rest_framework import serializers

from apps.categories.models import Category
from apps.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transaction
        fields = ["id", "category", "category_name", "amount", "type", "date", "note", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_category(self, value):
        request = self.context["request"]
        if value.user_id != request.user.id:
            raise serializers.ValidationError("Category not found.")
        return value

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        txn_type = attrs.get("type", getattr(self.instance, "type", None))
        if category and txn_type and category.type != txn_type:
            raise serializers.ValidationError({
                "type": (
                    f"Transaction type '{txn_type}' does not match category "
                    f"'{category.name}' which is of type '{category.type}'."
                )
            })
        return attrs
