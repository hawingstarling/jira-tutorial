from django.db import models
from organizations.models import Organization
import uuid

# Create your models here.
class AuditLog(models.Model):
  class Action(models.TextChoices):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

  class EntityType(models.TextChoices):
    BOARD = "BOARD"
    LIST = "LIST"
    CARD = "CARD"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="audit_logs")
  action = models.CharField(max_length=10, choices=Action.choices)
  entity_id = models.CharField(max_length=255)
  entity_type = models.CharField(max_length=10, choices=EntityType.choices)
  entity_title = models.CharField(max_length=255)
  user_id = models.CharField(max_length=255)
  user_image = models.TextField()
  user_name = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)