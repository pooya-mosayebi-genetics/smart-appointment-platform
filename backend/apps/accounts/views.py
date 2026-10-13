from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.middleware.csrf import get_token

from .serializers import OrganizationSerializer, BranchSerializer
from .models import Organization, Branch

# --- Import SimpleJWT Views and Serializers ---
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for obtaining JWT pair.
    Adds custom user data to the response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims if needed (e.g., role, org_id)
        # token['username'] = user.username
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get the authenticated user
        user = self.user
        
        # Append user info to the default response (which already contains access & refresh)
        data.update({
            "user": {
                "id": str(user.id),
                "mobile": user.mobile,
                "full_name": user.get_full_name(),
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        })
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View for login endpoint.
    Uses CustomTokenObtainPairSerializer to return user info along with tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    # No need to override post() anymore! 
    # The base class handles everything correctly now.


# --- Existing ViewSets ---

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related('organization').all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Branch.objects.select_related('organization').all()
        
        # Note: This assumes you have AccessScope model linked properly
        # For MVP, we might just return all branches or filter by org later
        try:
            org_ids = user.access_scopes.values_list('organization_id', flat=True)
            return Branch.objects.filter(organization_id__in=org_ids).select_related('organization')
        except AttributeError:
            # Fallback if relation doesn't exist yet in DB schema logic
            return Branch.objects.none()