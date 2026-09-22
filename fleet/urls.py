from rest_framework.routers import DefaultRouter

from .views import VehicleViewSet


router = DefaultRouter()

router.register(
    "fleet",
    VehicleViewSet,
    basename="fleet",
)

urlpatterns = router.urls
