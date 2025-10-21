from django.db import models
import uuid
from django.contrib.auth import get_user_model
from organizations.abstract import (
  AbstractOrganization,
  AbstractOrganizationUser,
  AbstractOrganizationOwner,
)
import uuid

User = get_user_model()

class Organization(AbstractOrganization):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  class Meta(AbstractOrganization.Meta):
      abstract = False
      db_table = 'organizations_organization'

class OrganizationUser(AbstractOrganizationUser):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_users",
        verbose_name="organization"
    )
  user = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name="organizations_organizationuser",
      verbose_name="user"
  )
  class Meta:
      abstract = False
      db_table = 'organizations_organizationuser'
      verbose_name = "organization user"
      verbose_name_plural = "organization users"

class OrganizationOwner(AbstractOrganizationOwner):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_owners",
        verbose_name="organization"
    )
  organization_user = models.ForeignKey(
      OrganizationUser,
      on_delete=models.CASCADE,
      related_name="organizations_organizationowner",
      verbose_name="organization user"
  )
  class Meta:
      abstract = False
      db_table = 'organizations_organizationowner'
      verbose_name = "organization owner"
      verbose_name_plural = "organization owners"

class OrgLimit(models.Model):
  organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="limit")
  count = models.IntegerField(default=0)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
      db_table = 'organizations_orglimit'
      verbose_name = "Organization Limit"
      verbose_name_plural = "Organization Limits"
    
  def __str__(self):
      return f"{self.organization.name} - Limit: {self.count}"

class OrgSubscription(models.Model):
  organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="subscription")
  stripe_customer_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
  stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
  stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
  stripe_current_period_end = models.DateTimeField(null=True, blank=True)

  class Meta:
      db_table = 'organizations_orgsubscription'
      verbose_name = "Organization Subscription"
      verbose_name_plural = "Organization Subscriptions"
    
  def __str__(self):
      return f"{self.organization.name} - Subscription"