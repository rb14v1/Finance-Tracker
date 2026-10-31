from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter

from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    filterset_fields = ["type"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = Category.objects.filter(user=self.request.user)
        type_param = self.request.query_params.get("type")
        if type_param:
            qs = qs.filter(type=type_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
