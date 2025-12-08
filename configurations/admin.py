# configurations/admin.py
from django.contrib import admin
from .models import ProductConfiguration

@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(admin.ModelAdmin):
    list_display = ("uuid", "vessel_use", "duty_cycle", "engine_manufacturer", "created_at")
    readonly_fields = ("uuid", "created_at", "updated_at")
