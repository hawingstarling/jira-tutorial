from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orgs.views import OrganizationViewSet

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")

urlpatterns = [
  path("", include(router.urls)),
]