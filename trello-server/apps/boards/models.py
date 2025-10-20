from django.db import models
import uuid

# Create your models here.
class Board(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  title = models.CharField(max_length=255)
  image_id = models.CharField(max_length=255)
  image_thumb_url = models.TextField()
  image_full_url = models.TextField()
  image_username = models.TextField()
  image_link_html = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class List(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')
  title = models.CharField(max_length=255)
  order = models.IntegerField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class Card(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='cards')
  title = models.CharField(max_length=255)
  order = models.IntegerField()
  description = models.TextField(blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)