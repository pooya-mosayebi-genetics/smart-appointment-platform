from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, BranchViewSet, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'orgs', OrganizationViewSet, basename='organization')
router.register(r'branches', BranchViewSet, basename='branch')

urlpatterns = [
    # JWT Endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Resource endpoints via Router
    path('', include(router.urls)),
]