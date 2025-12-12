from django.db import models
from django.contrib.auth.models import User


class Salesperson(models.Model):
    """
    Represents a salesperson. Not a Django user — a role entity.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="salesperson_profile"
    )
    employee_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Customer(models.Model):
    """
    A customer company or individual.
    """
    name = models.CharField(max_length=100)
    
    # Each customer MUST have one salesperson
    salesperson = models.ForeignKey(
        Salesperson,
        on_delete=models.PROTECT,  # cannot delete a salesperson with customers
        related_name="customers"
    )

    def __str__(self):
        return self.name


class UserProxy(models.Model):
    """
    A user account tied to a specific customer.
    Both real customers and salespeople acting on their behalf use this table.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="proxies"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="users"
    )

    class Meta:
        unique_together = ("user", "customer")

    def __str__(self):
        return f"{self.user.username} → {self.customer.name}"
