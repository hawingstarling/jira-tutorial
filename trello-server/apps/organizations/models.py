from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class Organization(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=255)
  owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_organizations")
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

# class OrgLimit(models.Model):
#   organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="limit")
#   count = models.IntegerField(default=0)
#   created_at = models.DateTimeField(auto_now_add=True)
#   updated_at = models.DateTimeField(auto_now=True)

# class OrgSubscription(models.Model):
#   organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="subscription")
#   stripe_customer_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
#   stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
#   stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
#   stripe_current_period_end = models.DateTimeField(null=True, blank=True)