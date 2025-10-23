from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch, Count, Exists, OuterRef
from django.db import transaction
from django.core.cache import cache
from .models import (
  Organization,
  OrganizationUser,
  OrganizationOwner,
  OrgLimit,
  OrgSubscription,
)

from .serializers import (
  OrganizationSerializer,
  OrganizationDetailSerializer,
  OrganizationMembershipSerializer,
  CreateOrganizationSerializer
)


"""
Custom pagination class according to Clerk standard
  - page_size_query_param: allows client to control page size
  - max_page_size: limit to avoid query being too large
"""
class StandardResultSetPagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = "pageSize"
  max_page_size = 100

"""
ViewSet for Organization CRUD operations
  Endpoints:
  - GET    /api/organizations/                    - List user's orgs
  - POST   /api/organizations/                    - Create org
  - GET    /api/organizations/{id}/               - Get org detail
  - PATCH  /api/organizations/{id}/               - Update org
  - DELETE /api/organizations/{id}/               - Delete org
  - GET    /api/organizations/{id}/memberships/   - Get members
  - POST   /api/organizations/{id}/invite/        - Invite member
  - POST   /api/organizations/{id}/remove-member/ - Remove member
  - POST   /api/organizations/{id}/update-role/   - Update member role
  - GET    /api/organizations/user-memberships/   - Get all user's orgs
Performance optimizations:
  1. select_related: JOIN related tables (1-to-1, ForeignKey)
  2. prefetch_related: Separate queries for many-to-many, reverse ForeignKey
  3. annotate: Compute fields in database instead of Python
  4. Cache: Redis/Memcached for frequently accessed data
  5. Transaction: Ensure data consistency
"""
class OrganizationViewSet(viewsets.ModelViewSet):
  permission_classes = [IsAuthenticated]
  pagination_class = StandardResultSetPagination

  """
  CRITICAL: Queryset optimization to avoid the N+1 problem

  Technical usage:
  1. select_related('limit', 'subscription'): JOIN OneToOne relations
  2. prefetch_related: Prefetch reverse ForeignKey (organization_users)
  3. annotate: Calculate member_count and is_user_admin in DB
  4. distinct(): Avoid duplicate when filtering via ManyToMany
  """

  def get_queryset(self):
    user = self.request.user

    # Query with all optimizations
    queryset = Organization.objects.filter(
      organization_users__user=user # Filter organizations of which the user is a member
    ).select_related(
      # JOIN for OneToOne relations (1 query instead of N+1)
      "limit",        # OrgLimit
      "subscription"  # OrgSubscription
    ).prefetch_related(
      # Prefetch organization_users with user data (2 queries instead of N+1)
      Prefetch(
        "organization_users",
        queryset=OrganizationUser.objects.select_related("user")
      ),
      # Prefetch owners to check admin status (2 queries instead of N+1)
      Prefetch(
        "organization_owners",
        queryset=OrganizationOwner.objects.select_related("organization_user__user")
      )
    ).annotate(
      # Calculate member_count in database (avoid separate COUNT query for each org)
      member_count=Count("organization_users", distinct=True),

      # Check if current user is admin (use EXISTS subquery - efficient)
      is_user_admin=Exists(
        OrganizationOwner.objects.filter(
          organization=OuterRef("pk"),
          organization_user__user=user
        )
      )
    ).distinct().order_by("-created") # Avoid duplicate from JOIN

    return queryset
  
  def get_serializer_class(self):
    """
    Choose the appropriate serializer for the action
      - create: CreateOrganizationSerializer (validate input)
      - retrieve: OrganizationDetailSerializer (full data with memberships)
      - list: OrganizationSerializer (lightweight)
    """
    if self.action == "create":
      return CreateOrganizationSerializer
    elif self.action == "retrieve":
      return OrganizationDetailSerializer
    return OrganizationSerializer
  
  @action(detail=True, methods=["get"], url_path="memberships")
  def memberships(self, request, pk=None):
    """
    GET /api/organizations/{id}/memberships/
    Get list of members with pagination
      Similar: useOrganization({ memberships: { pageSize: 10, role: 'admin' } })
      
      Query params:
      - page: Page number (default: 1)
      - pageSize: Items per page (default: 10)
      - role: Filter by role ('admin' or 'member')
      - query: Search term (search in name, email)
      
      Performance optimizations:
      1. select_related('user'): Avoid N+1 when accessing user data
      2. annotate(is_admin): Check admin status in DB
      3. Index on organization, user, created fields
    """
    organization = self.get_object() # Optimized from get_queryset()

    # Permission check - use annotated field
    if not hasattr(organization, "is_user_admin") or not organization.is_user_admin:
      # Fallback check if not annotation
      if not organization.is_member(request.user):
        return Response(
          {
            "detail": "Not a member of this organization"
          },
          status=status.HTTP_403_FORBIDDEN
        )
      
    # Parse query parameters
    role = request.query_params.get("role")
    query = request.query_params.get("query")

    # Base queryset with optimization
    memberships = OrganizationUser.objects.filter(
      organization=organization
    ).select_related(
      # JOIN user table to avoid N+1 when serializing
      "user"
    ).annotate(
      # Check admin status in DB (EXISTS subquery -efficient)
      is_admin_flag=Exists(
        OrganizationOwner.objects.filter(
          organization=organization,
          organization_user=OuterRef("pk")
        )
      )
    )

    # Filter by role - use annotated field
    if role:
      if role == "admin":
        memberships = memberships.filter(is_admin=True)
      elif role == "member":
        memberships = memberships.filter(is_admin=False)
    
    # Search functionality
    if query:
      # Search in user fields - make sure there is an index on these fields
      memberships = memberships.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query)
      )
    
    # Order by created date (consistent pagination)
    memberships = memberships.order_by("-created")

    # Paginate and serialize
    page = self.paginate_queryset(memberships)
    if page is not None:
      serializer = OrganizationMembershipSerializer(page, many=True)
      return self.get_paginated_response(serializer.data)
    
    serializer = OrganizationMembershipSerializer(memberships, many=True)
    return Response(serializer.data)
  
  @transaction.atomic # Wrap in transaction to make sure data consistency
  @action(detail=True, methods=["post"], url_path="invite")
  def invite_member(self, request, pk=None):
    """
    POST /api/organizations/{id}/invite/
    Body: { "email": "tien.dinh@hdwebsoft.dev" }

    Invite users to the organization

    Performance considerations:
    1. transaction.atomic: Ensure all operations succeed or rollback
    2. exists() instead of count(): Efficient check
    3. select_for_update: Lock row to avoid race condition (if needed)
    """

    organization = self.get_object()

    # Permission check - only admin can invite
    if not hasattr(organization, "is_user_admin") or not organization.is_user_admin:
      return Response(
        {
          "detail": "Admin access required"
        },
        status=status.HTTP_403_FORBIDDEN
      )
    
    email = request.data.get("email")
    if not email:
      return Response(
        {
          "detail": "Email is required"
        },
        status=status.HTTP_400_BAD_REQUEST
      )
    # Check if user is already a member (exists() is more efficient than count())
    is_member = OrganizationUser.objects.filter(
      organization=organization,
      user__email=email
    ).exists()

    if is_member:
      return Response(
        {"detail": "User is already a member"},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    try:
      # Get or create user
      from django.contrib.auth import get_user_model
      User = get_user_model()

      user, created = User.objects.get_or_create(
        email=email,
        defaults={
          "username": email
        }
      )

      # Add user to organization
      org_user = OrganizationUser.objects.create(
        organization=organization,
        user=user
      )

      # Invalidate cache
      cache.delete(f'org_members_{organization.id}')
      cache.delete(f'user_orgs_{user.id}')

      serializer = OrganizationMembershipSerializer(org_user)
      return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
      return Response(
          {"detail": str(e)},
          status=status.HTTP_400_BAD_REQUEST
      )
    
  @transaction.atomic
  @action(detail=True, methods=["post"], url_path="remove-member")
  def remove_member(self, request, pk=None):
    """
    POST /api/organizations/{id}/remove-member/
    Content: { "user_id": "uuid" }

    Remove member from organization

    Business logic:
    - Delete last admin not allowed
    - Delete cascade will delete OrganizationOwner if present
    """
    organization = self.get_object()

    # Permission check
    if not hasattr(organization, "is_user_admin") or not organization.is_user_admin:
      return Response(
        {
          "detail": "Admin access require"
        },
        status=status.HTTP_403_FORBIDDEN
      )
    
    user_id = request.data.get("user_id")
    if not user_id:
      return Response(
        {"detail": "user_id is required"},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    # Check if target user is admin
    is_target_admin = OrganizationOwner.objects.filter(
      organization=organization,
      organization_user__user_id=user_id
    ).exists()

    # Prevent removing last admin
    if is_target_admin:
      admin_count = OrganizationOwner.objects.filter(
        organization=organization
      ).count()
      
      if admin_count <= 1:
        return Response(
          {"detail": "Cannot remove the last admin"},
          status=status.HTTP_400_BAD_REQUEST
        )
      
    try:
      # Get and delete membership
      # select_for_update() to lock row, avoid race condition
      org_user = OrganizationUser.objects.select_for_update().get(
          organization=organization,
          user_id=user_id
      )
      
      user_id_cache = org_user.user_id
      OrganizationUser.objects.filter(pk=org_user.pk).delete() # Cascade delete OrganizationOwner
      
      # Invalidate caches
      cache.delete(f'org_members_{organization.id}')
      cache.delete(f'user_orgs_{user_id_cache}')
      
      return Response(
        {"detail": "Member removed successfully"},
        status=status.HTTP_200_OK
      )
            
    except OrganizationUser.DoesNotExist:
      return Response(
        {"detail": "User is not a member"},
        status=status.HTTP_404_NOT_FOUND
      )
  
  @action(detail=False, methods=["get"], url_path="user-memberships")
  def user_memberships(self, request):
      """
      GET /api/organizations/user-memberships/
      
      Get all organizations that user is a member of
      Similar: useOrganizationList({ userMemberships: { infinite: true } })
      
      Optimization:
      - Reuse get_queryset() optimizations
      - Cache results (5 minutes)
      """
      user = request.user
      
      # Try cache first
      cache_key = f'user_memberships_{user.id}'
      cached_data = cache.get(cache_key)
      if cached_data:
        return Response(cached_data)
      
      # get_queryset() has all optimizations
      organizations = self.get_queryset().order_by('-created')
      
      # Paginate
      page = self.paginate_queryset(organizations)
      if page is not None:
        serializer = OrganizationSerializer(page, many=True)
        response_data = self.get_paginated_response(serializer.data).data
        
        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)
        return Response(response_data)
      
      serializer = OrganizationSerializer(organizations, many=True)
      response_data = serializer.data
      
      # Cache for 5 minutes
      cache.set(cache_key, response_data, 300)
      return Response(response_data)
    
  @transaction.atomic
  def create(self, request, *args, **kwargs):
    """
    POST /api/organizations/
    Body: { "name": "My Organization" }

    Create new organization and add creator as owner

    Transaction ensures:

    - Organization is created
    - OrganizationUser is created
    - OrganizationOwner is created
    - OrgLimit is created
    Or all rollback if there is an error
    """
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Create in transaction (defined in serializer.create())
    organization = serializer.save()
    
    # Invalidate user's cache
    cache.delete(f'user_orgs_{request.user.id}')
    cache.delete(f'user_memberships_{request.user.id}')
    
    # Return created organization
    output_serializer = OrganizationSerializer(organization)
    headers = self.get_success_headers(output_serializer.data)
    
    return Response(
        output_serializer.data,
        status=status.HTTP_201_CREATED,
        headers=headers
    )
    
  @transaction.atomic
  def update(self, request, *args, **kwargs):
    """
    PUT/PATCH /api/organizations/{id}/
    
    Update organization with transaction
    """
    partial = kwargs.pop('partial', False)
    instance = self.get_object()
    serializer = self.get_serializer(
      instance,
      data=request.data,
      partial=partial
    )
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)
    
    # Invalidate cache
    cache.delete(f'org_{instance.id}')
    
    return Response(serializer.data)
  
  @transaction.atomic
  def destroy(self, request, *args, **kwargs):
    """
    DELETE /api/organizations/{id}/
    
    Delete organization
    - Cascade delete all related data (OrganizationUser, OrganizationOwner, etc.)
    """
    instance = self.get_object()
    org_id = instance.id
    
    # Get all members to invalidate cache
    member_ids = list(
        instance.organization_users.values_list('user_id', flat=True)
    )
    
    # Perform deletion
    self.perform_destroy(instance)
    
    # Invalidate caches
    cache.delete(f'org_{org_id}')
    for user_id in member_ids:
        cache.delete(f'user_orgs_{user_id}')
        cache.delete(f'user_memberships_{user_id}')
    
    return Response(status=status.HTTP_204_NO_CONTENT)

  @transaction.atomic
  @action(detail=True, methods=["post"], url_path="update-role")
  def update_role(self, request, pk=None):
    """
    POST /api/organizations/{id}/update-role/
      Body: { "user_id": "uuid", "role": "admin" | "member" }

      Update member role (promote/demote)
      Business logic:
      - Only admin can update roles
      - Cannot remove the last admin
      - Update OrganizationOwner table accordingly
    """
    organization = self.get_object()

    # Permission check
    if not hasattr(organization, "is_user_admin") or not organization.is_user_admin:
      return Response({"detail": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
    
    user_id = request.data.get("user_id")
    role = request.data.get("role")

    if not user_id or role not in ["admin", "member"]:
      return Response(
          {"detail": "user_id and role (admin/member) are required"},
          status=status.HTTP_400_BAD_REQUEST,
      )
    
    try:
        org_user = OrganizationUser.objects.get(organization=organization, user_id=user_id)
    except OrganizationUser.DoesNotExist:
        return Response({"detail": "User is not a member"}, status=status.HTTP_404_NOT_FOUND)

    is_target_admin = OrganizationOwner.objects.filter(
        organization=organization, organization_user=org_user
    ).exists()

    # Promote to admin
    if role == "admin" and not is_target_admin:
        OrganizationOwner.objects.create(organization=organization, organization_user=org_user)

    # Demote to member
    elif role == "member" and is_target_admin:
        admin_count = OrganizationOwner.objects.filter(organization=organization).count()
        if admin_count <= 1:
            return Response(
                {"detail": "Cannot demote the last admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        OrganizationOwner.objects.filter(
            organization=organization, organization_user=org_user
        ).delete()

    # Invalidate cache
    cache.delete(f'org_members_{organization.id}')
    cache.delete(f'user_orgs_{user_id}')

    return Response({"detail": "Role updated successfully"}, status=status.HTTP_200_OK)
  
  @transaction.atomic
  @action(detail=True, methods=["post"], url_path="leave")
  def leave_organization(self, request, pk=None):
    """
    POST /api/organizations/{id}/leave/
    Allow current user to leave the organization.

    Business rules:
    - If user is the last admin → cannot leave
    - Delete cascade removes OrganizationOwner if exists
    """
    organization = self.get_object()
    user = request.user

    try:
        org_user = OrganizationUser.objects.get(organization=organization, user=user)
    except OrganizationUser.DoesNotExist:
        return Response({"detail": "You are not a member of this organization"}, status=404)

    # Check if user is admin
    is_admin = OrganizationOwner.objects.filter(
        organization=organization, organization_user=org_user
    ).exists()

    if is_admin:
        admin_count = OrganizationOwner.objects.filter(organization=organization).count()
        if admin_count <= 1:
            return Response(
                {"detail": "You cannot leave as the last admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Perform leave
    user_id_cache = user.id
    OrganizationOwner.objects.filter(
        organization=organization,
        organization_user=org_user
    ).delete()  # Cascade deletes admin role

    # Invalidate cache
    cache.delete(f'org_members_{organization.id}')
    cache.delete(f'user_orgs_{user_id_cache}')
    cache.delete(f'user_memberships_{user_id_cache}')

    return Response({"detail": "You have left the organization"}, status=200)
  
  @transaction.atomic
  @action(detail=True, methods=["post"], url_path="transfer-owner")
  def transfer_ownership(self, request, pk=None):
    """
    POST /api/organizations/{id}/transfer-owner/
    Body: { "new_owner_id": "uuid" }

    Transfer ownership to another member.
    Business rules:
    - Only current admin can transfer
    - New owner must be a member
    - Promote new owner if not admin
    """
    organization = self.get_object()
    user = request.user

    # Check permission
    if not hasattr(organization, "is_user_admin") or not organization.is_user_admin:
        return Response({"detail": "Admin access required"}, status=403)

    new_owner_id = request.data.get("new_owner_id")
    if not new_owner_id:
        return Response({"detail": "new_owner_id is required"}, status=400)

    try:
        new_owner_user = OrganizationUser.objects.get(
            organization=organization, user_id=new_owner_id
        )
    except OrganizationUser.DoesNotExist:
        return Response({"detail": "Target user is not a member"}, status=404)

    # Make sure new owner is in OrganizationOwner table
    OrganizationOwner.objects.get_or_create(
        organization=organization, organization_user=new_owner_user
    )

    # Optionally: demote current admin
    # (optional rule, depends on your business)
    # OrganizationOwner.objects.filter(
    #     organization=organization,
    #     organization_user__user=user
    # ).delete()

    cache.delete(f'org_members_{organization.id}')
    cache.delete(f'user_orgs_{user.id}')
    cache.delete(f'user_orgs_{new_owner_id}')

    return Response({"detail": "Ownership transferred successfully"}, status=200)