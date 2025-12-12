from django.contrib import admin
from .models import Salesperson, Customer, UserProxy


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user")
    search_fields = ("employee_id", "user__username", "user__email")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "salesperson")
    list_filter = ("salesperson",)
    search_fields = ("name",)


@admin.register(UserProxy)
class UserProxyAdmin(admin.ModelAdmin):
    list_display = ("user", "customer")
    list_filter = ("customer",)
    search_fields = ("user__username", "customer__name")
