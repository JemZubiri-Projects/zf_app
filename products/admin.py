# products/admin.py
from django.contrib import admin
from .models import Family, Part, PartAttribute

class PartAttributeInline(admin.TabularInline):
    model = PartAttribute
    extra = 0

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("code", "name")

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("part_number", "family", "is_active")
    search_fields = ("part_number",)
    inlines = [PartAttributeInline]
