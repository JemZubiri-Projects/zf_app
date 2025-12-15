from django.contrib import admin
from .models import Customer, CustomerMembership, Salesperson, CustomerDiscount

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_number", "name", "primary_salesperson")
    list_filter = ("primary_salesperson",)
    search_fields = ("customer_number", "name")


@admin.register(CustomerMembership)
class CustomerMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "customer", "role")
    list_filter = ("customer", "role")
    search_fields = ("user__username", "customer__customer_number", "customer__name")


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id")
    search_fields = ("user__username", "employee_id")

@admin.register(CustomerDiscount)
class CustomerDiscountAdmin(admin.ModelAdmin):
    list_display = ("customer", "name", "discount_percent", "active")
    list_filter = ("active", "customer")
    search_fields = (
        "name",
        "customer__name",
        "customer__customer_number",
    )
    ordering = ("customer__name", "-active")

    # Nice readable formatting if you want to display the percent
    def formatted_discount(self, obj):
        return f"{obj.discount_percent}%"
    formatted_discount.short_description = "Discount"
