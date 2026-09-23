from rest_framework.routers import DefaultRouter

from .views import RouteViewSet, RouteStopViewSet


router = DefaultRouter()

router.register(
    "routes",
    RouteViewSet,
    basename="route",
)

router.register(
    "route-stops",
    RouteStopViewSet,
    basename="route-stop",
)

urlpatterns = router.urls
