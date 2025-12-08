# products/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from configurations.models import ProductConfiguration

class Family(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Part(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    part_number = models.CharField(max_length=128)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="parts")
    description = models.TextField(null=True, blank=True)
    unit_of_measure = models.CharField(max_length=64, blank=True, null=True)
    image_src = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("part_number", "family")

    def __str__(self):
        return f"{self.part_number}"

class PartAttribute(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="attributes")
    name = models.CharField(max_length=128)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.FloatField(blank=True, null=True)
    value_type = models.CharField(max_length=32, blank=True, null=True)  # 'text','number','bool','date'
    unit = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.part.part_number} - {self.name}"

class Configuration(models.Model):
    APPLICATION_TYPES = [
        ("marine", "Marine"),
        ("industrial", "Industrial"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)

    # Required fields
    duty_cycle = models.CharField(max_length=50, blank=True)
    propulsion = models.CharField(max_length=50, blank=True)
    transmission_config = models.CharField(max_length=50, blank=True)

    # Manufacturer section
    engine_manufacturer = models.CharField(max_length=50, blank=True)
    unit_system = models.CharField(max_length=20, default="imperial")
    power_value = models.FloatField(null=True, blank=True)
    rpm_value = models.IntegerField(null=True, blank=True)

    # Optional fields
    primary_use = models.CharField(max_length=50, blank=True)
    hybrid = models.CharField(max_length=10, blank=True)

    # Tracking
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config #{self.id} for {self.user.username}"

class QuoteRequest(models.Model):
    config = models.ForeignKey(ProductConfiguration, null=True, blank=True, on_delete=models.SET_NULL)
    project_name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Quote #{self.id} — {self.project_name}"
