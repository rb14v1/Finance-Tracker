from rest_framework.routers import DefaultRouter

from apps.budgets.views import BudgetViewSet

router = DefaultRouter()
router.register(r"", BudgetViewSet, basename="budget")

urlpatterns = router.urls
