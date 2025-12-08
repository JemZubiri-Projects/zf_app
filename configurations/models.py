# configurations/models.py
import uuid
from django.db import models
from django.conf import settings

class ProductConfiguration(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Duty Cycle
    vessel_use = models.CharField(max_length=64, blank=True, null=True)  # commercial / recreational
    duty_cycle = models.CharField(max_length=64, blank=True, null=True)  # pleasure/light/medium/continuous

    # Configuration
    propulsion_type = models.CharField(max_length=64, blank=True, null=True)  # shaft/water/surface/thruster
    hybrid_or_brake = models.BooleanField(null=True)
    transmission_config = models.CharField(max_length=64, blank=True, null=True)

    # Manufacturer & Power
    engine_manufacturer = models.CharField(max_length=64, blank=True, null=True)
    power_factor = models.FloatField(null=True, blank=True)
    ratio = models.CharField(max_length=64, null=True, blank=True)
    

    # series & model selection (string for now)
    selected_series = models.CharField(max_length=128, blank=True, null=True)
    selected_model = models.CharField(max_length=128, blank=True, null=True)
    selected_model_name = models.CharField(max_length=255, null=True, blank=True)

    bellhousing = models.CharField(max_length=255, null=True, blank=True)
    actuation = models.CharField(max_length=255, null=True, blank=True)
    trolling = models.CharField(max_length=255, null=True, blank=True)
    mountings = models.CharField(max_length=255, null=True, blank=True)
    pto = models.CharField(max_length=255, null=True, blank=True)
    ptishaftbrake = models.CharField(max_length=255, null=True, blank=True)
    trailingpump = models.CharField(max_length=255, null=True, blank=True)
    propflange = models.CharField(max_length=255, null=True, blank=True)
    inputflange = models.CharField(max_length=255, null=True, blank=True)
    monitoring = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


