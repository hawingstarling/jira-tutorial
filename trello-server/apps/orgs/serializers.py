from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Organization,
    OrganizationUser,
    OrganizationOwner,
    OrgLimit,
    OrgSubscription
)

User = get_user_model()

"""
Serializer for public user data
  - Expose only necessary fields to avoid leaking sensitive data
"""
class UserPublicDataSerializer(serializers.ModelSerializer):
  identifier = serializers.CharField(source="email", read_only=True)
  first_name = serializers.CharField(read_only=True)
  last_name = serializers.CharField(read_only=True)

  class Meta:
    model = User
    fields = ["id", "first_name", "last_name", "email", "identifier"]
    read_only_fields = fields

"""
Serializer for organization membership (OrganizationUser)
  - Use SerializerMethodField to avoid N+1 when checking roles
"""
class OrganizationMembershipSerializer(serializers.ModelSerializer):
  # Nested serializer for user data - data has been prefetched in the view
  public_user_data = UserPublicDataSerializer(source="user", read_only=True)

  # SerializerMethodField for role - use annotated field from queryset
  role = serializers.SerializerMethodField()

  class Meta:
    model = OrganizationUser
    fields = [
      "id",
      "user",
      "organization",
      "public_user_data",
      "role",
      "created"
    ]
    
  """
  Get user role in organization
    - Use annotated field 'is_admin' from queryset to avoid N+1
    - If no annotation, fallback to query (slower)
  """
  def get_role(self, obj):
    # Check if there is an annotated field (set in the view's queryset)
    if hasattr(obj, "is_admin_flag"):
      return "admin" if obj.is_admin else "member"
    
    # fallback: query database (N+1 problem without annotation)
    is_owner = OrganizationOwner.objects.filter(
        organization=obj.organization,
        organization_user=obj
    ).exists()
    return 'admin' if is_owner else 'member'

"""Serializer for organization limit"""
class OrganizationLimitSerializer(serializers.ModelSerializer):
  class Meta:
    model = OrgLimit
    fields = ["count", "created_at", "updated_at"]

"""Serializer for organization subscription"""
class OrganizationSubscriptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = OrgSubscription
    fields = [
      "stripe_customer_id",
      "stripe_subscription_id", 
      "stripe_price_id",
      "stripe_current_period_end"
    ]

"""
Basic Serializer for Organization
  - Use SerializerMethodField for computed fields
  - member_count is annotated in queryset to avoid extra query
"""
class OrganizationSerializer(serializers.ModelSerializer):
  slug = serializers.SlugField(read_only=True)
  
  # Use annotated field from queryset to avoid N+1
  member_count = serializers.IntegerField(read_only=True)
  
  # Nested serializers for related data - use source to access OneToOne relation
  limit = OrganizationLimitSerializer(read_only=True)
  subscription = OrganizationSubscriptionSerializer(read_only=True)
  
  class Meta:
    model = Organization
    fields = [
      "id",
      "name",
      "slug",
      "is_active",
      "created",
      "modified",
      "member_count",
      "limit",
      "subscription"
    ]
    read_only_fields = ["id", "created", "modified", "slug"]


"""
Detailed serializer for Organization with memberships
  - Only used when needing to fetch full organization data
  - Memberships data has been prefetched in the view
"""
class OrganizationDetailSerializer(OrganizationSerializer):
    memberships = OrganizationMembershipSerializer(
      source="organization_users",
      many=True,
      read_only=True
    )
    
    class Meta(OrganizationSerializer.Meta):
      fields = OrganizationSerializer.Meta.fields + ["memberships"]


"""
Serializer to create new organization
  - Validate and create organization with owner relationship
"""
class CreateOrganizationSerializer(serializers.ModelSerializer):
  class Meta:
    model = Organization
    fields = ["name"]
  
  """
  Create organization and add creator as owner
    - Use transaction in view to ensure atomicity
  """
  def create(self, validated_data):
    user = self.context['request'].user
    
    # Create organization
    org = Organization.objects.create(**validated_data)
    
    # Create organization user
    org_user = OrganizationUser.objects.create(
        organization=org,
        user=user
    )
    
    # Create organization owner
    OrganizationOwner.objects.create(
        organization=org,
        organization_user=org_user
    )
    
    # Create limit record
    OrgLimit.objects.create(organization=org)
    
    return org
  
  